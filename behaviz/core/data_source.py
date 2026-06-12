from __future__ import annotations

from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Dataframe-agnostic column resolution
# ---------------------------------------------------------------------------
# behaviz never imports pandas or polars. A "data" object is anything that
# supports ``data[column_name]`` and yields something ``np.asarray`` can
# materialise — which covers pandas.DataFrame, polars.DataFrame and a plain
# ``dict[str, array]``. That single duck-typed path is all we need to let users
# plot from arrays *or* frames without a hard dependency on either.


def _available_columns(data: Any) -> list:
    """Best-effort list of column names, for friendly error messages."""
    cols = getattr(data, "columns", None)
    if cols is not None:
        return list(cols)
    keys = getattr(data, "keys", None)
    if callable(keys):
        return list(keys())
    return []


def _is_lazy(data: Any) -> bool:
    """Detect a polars LazyFrame (has column names but is not subscriptable)."""
    return type(data).__name__ == "LazyFrame"


def resolve(value: Any, data: Any) -> np.ndarray:
    """Turn a data *channel* into a numpy array or a list of arrays.

    Parameters
    ----------
    value
        Either an array-like (passed straight through) or, when ``data`` is
        supplied, a ``str`` naming a column in ``data``.
    data
        A dataframe-like object (pandas / polars / dict-of-arrays) or ``None``.

    Rules (identical to seaborn): when ``data`` is given, a ``str`` ``value`` is
    a column name; otherwise every ``value`` is treated as raw data.

    A ragged sequence — a list of arrays with *different* lengths, e.g. the
    per-group distributions passed to ``plot_violin`` — cannot become a single
    rectangular array, so it is returned as a ``list`` of 1-D arrays instead.
    """
    if data is not None and isinstance(value, str):
        if _is_lazy(data):
            raise TypeError(
                "Got a lazy frame (e.g. polars LazyFrame). Materialise it first "
                "with .collect() before passing it as `data`."
            )
        if value not in _available_columns(data):
            raise KeyError(f"Column '{value}' not found in data. Available columns: {_available_columns(data)}")
        return _to_array(data[value])

    return _to_array(value)


def _to_array(value: Any) -> np.ndarray | list:
    """Coerce ``value`` to an ndarray, falling back to a list of arrays.

    A homogeneous array-like becomes a single ndarray. A ragged sequence (arrays
    of differing length) raises ``ValueError`` under NumPy >= 2, so we keep it as
    a list of per-element arrays — the form the "vectors" channel kind expects
    for a list of distributions.
    """
    try:
        return np.asarray(value)
    except ValueError:
        return [np.asarray(v) for v in value]
