from __future__ import annotations

import numbers
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from .errors import data_error, describe


@dataclass(frozen=True)
class Channel:
    """Declarative contract for one data-carrying parameter of a plot function.

    Declared on the :func:`~behaviz.core.plot_setup.plot_function` decorator in
    the same order as the function's leading positional parameters. The
    decorator binds each channel to its argument, resolves column names against
    ``data=``, coerces the value to the declared ``kind`` and runs cross-channel
    length checks — so function bodies always receive clean, normalised arrays.

    Attributes
    ----------
    name
        The parameter name the channel binds to.
    kind
        ``"vector"``            one 1-D numeric sequence; scalars become
                                length-1 arrays, ``(N, 1)`` / ``(1, N)`` are
                                squeezed, true 2-D raises.
        ``"vectors"``           a sequence of 1-D sequences, one per group
                                (ragged allowed); a 2-D array becomes a list of
                                its rows.
        ``"grid"``              exactly one 2-D array.
        ``"scalar_or_vector"``  a scalar passes through untouched (the function
                                broadcasts it); anything else is coerced like
                                ``"vector"``.
        ``"raw"``               bound and dataframe-resolved only — no coercion.
                                The escape hatch for odd contracts checked in
                                the function body.
    required
        When False, ``None`` is allowed and passed through untouched.
    same_length_as
        Name of another channel whose length this one must match.
    """

    name: str
    kind: str = "vector"
    required: bool = True
    same_length_as: str | None = None


# dtype kinds a data channel may hold: bool, (un)signed int, float, complex,
# datetime64, timedelta64. Strings/objects are rejected with a targeted error.
_OK_DTYPE_KINDS = frozenset("biufcMm")


def _is_scalar(value: Any) -> bool:
    return isinstance(value, numbers.Number) or (np.isscalar(value) and not isinstance(value, str))


def _materialise(value: Any) -> Any:
    """Turn a plain iterable (e.g. a generator) into a list; pass others through."""
    if hasattr(value, "__iter__") and not hasattr(value, "__len__") and not isinstance(value, np.ndarray):
        return list(value)
    return value


def _has_length(value: Any) -> bool:
    return hasattr(value, "__len__") and not isinstance(value, str)


def _to_numeric_array(func: str, name: str, value: Any) -> np.ndarray:
    """``np.asarray`` with friendly failure modes (ragged, non-numeric)."""
    try:
        arr = np.asarray(value)
    except (ValueError, TypeError):
        if _has_length(value) and any(_has_length(v) for v in value):
            raise data_error(
                func,
                f"`{name}` must be a flat sequence, but it contains nested sequences of different lengths.",
                details={name: value},
                hint="pass one flat series of values per call.",
            ) from None
        raise data_error(
            func,
            f"`{name}` could not be converted to a numeric array.",
            details={name: value},
            hint="pass a flat numeric sequence (list, tuple, ndarray or Series).",
        ) from None
    if arr.dtype.kind not in _OK_DTYPE_KINDS:
        raise data_error(
            func,
            f"`{name}` must be numeric.",
            details={name: f"{describe(value)} (dtype {arr.dtype})"},
            hint="convert text/objects to numbers first; categorical labels belong in spec ticks, not data.",
        )
    return arr


def _coerce_vector(func: str, name: str, value: Any) -> np.ndarray:
    if _is_scalar(value):
        return np.asarray([value])

    arr = _to_numeric_array(func, name, _materialise(value))

    if arr.ndim == 0:
        return arr.reshape(1)
    if arr.ndim == 2 and 1 in arr.shape:
        return arr.ravel()
    if arr.ndim > 1:
        raise data_error(
            func,
            f"`{name}` must be 1-D.",
            details={name: arr},
            hint="for multiple series, plot them one call at a time (or use a function "
            "that takes a list of series, e.g. plot_violin's ys).",
        )
    return arr


def _coerce_vectors(func: str, name: str, value: Any) -> list[np.ndarray]:
    if isinstance(value, str) or _is_scalar(value):
        raise data_error(
            func,
            f"`{name}` must be a sequence of sequences (one 1-D series per group).",
            details={name: value},
        )

    value = _materialise(value)

    if isinstance(value, np.ndarray):
        if value.ndim == 2:
            # one group per row — the single place this convention is defined
            return [np.asarray(row) for row in value]
        if value.ndim == 1 and value.dtype == object:
            # ragged array of arrays
            return [_coerce_vector(func, f"{name}[{i}]", v) for i, v in enumerate(value)]
        raise data_error(
            func,
            f"`{name}` must be a sequence of sequences (one 1-D series per group).",
            details={name: value},
            hint=f"for a single group, wrap it: {name}=[your_array].",
        )

    if _has_length(value):
        if len(value) == 0:
            raise data_error(func, f"`{name}` is empty.", hint="pass at least one group of values.")
        if all(_has_length(v) for v in value):
            return [_coerce_vector(func, f"{name}[{i}]", v) for i, v in enumerate(value)]
        if all(_is_scalar(v) for v in value):
            raise data_error(
                func,
                f"`{name}` must be a sequence of sequences, got a flat sequence of scalars.",
                details={name: value},
                hint=f"for a single group, wrap it: {name}=[your_array].",
            )
        raise data_error(
            func,
            f"`{name}` mixes scalars and sequences.",
            details={name: value},
            hint="pass one 1-D series per group, all wrapped in a list.",
        )

    raise data_error(func, f"`{name}` must be a sequence of sequences (one 1-D series per group).", details={name: value})


def _coerce_grid(func: str, name: str, value: Any) -> np.ndarray:
    arr = _to_numeric_array(func, name, _materialise(value))
    if arr.ndim != 2:
        hint = "reshape your values to (n_rows, n_cols)."
        if arr.ndim == 3:
            hint = "RGB(A) images are not supported yet — pass a 2-D array of scalar values."
        raise data_error(func, f"`{name}` must be a 2-D array.", details={name: arr}, hint=hint)
    return arr


def _coerce_scalar_or_vector(func: str, name: str, value: Any) -> Any:
    if _is_scalar(value):
        return value
    return _coerce_vector(func, name, value)


_COERCERS = {
    "vector": _coerce_vector,
    "vectors": _coerce_vectors,
    "grid": _coerce_grid,
    "scalar_or_vector": _coerce_scalar_or_vector,
    "raw": lambda func, name, value: value,
}


def coerce_channel(func: str, channel: Channel, value: Any) -> Any:
    """Coerce one bound value to its channel's kind (``None`` handled here)."""
    if value is None:
        if channel.required:
            raise data_error(func, f"`{channel.name}` is required but got None.")
        return None
    return _COERCERS[channel.kind](func, channel.name, value)


def _channel_length(channel: Channel, value: Any) -> int | None:
    """Group count of a coerced value, or None when length doesn't apply."""
    if value is None:
        return None
    if channel.kind in ("vector", "vectors"):
        return len(value)
    if channel.kind == "scalar_or_vector" and isinstance(value, np.ndarray):
        return len(value)
    return None


def check_lengths(func: str, channels: Sequence[Channel], values: dict[str, Any]) -> None:
    """Enforce every ``same_length_as`` constraint among the bound channels."""
    by_name = {ch.name: ch for ch in channels}
    for ch in channels:
        if not ch.same_length_as or ch.name not in values or ch.same_length_as not in values:
            continue
        other = by_name[ch.same_length_as]
        n = _channel_length(ch, values[ch.name])
        m = _channel_length(other, values[other.name])
        if n is None or m is None or n == m:
            continue
        raise data_error(
            func,
            f"`{ch.name}` must have the same length as `{other.name}`.",
            details={other.name: values[other.name], ch.name: values[ch.name]},
            hint=f"got {m} vs {n} — pass one `{ch.name}` entry per `{other.name}` entry.",
        )
