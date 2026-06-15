from __future__ import annotations

from typing import Any

import numpy as np


class BehavizDataError(ValueError):
    """Raised when input data does not match a plot function's contract.

    Subclasses ``ValueError`` so generic ``except ValueError`` handling
    keeps working.
    """


class BehavizSaveError(ValueError):
    """Raised when a figure cannot be saved in the requested format.

    Covers unsupported backend/extension combinations (e.g. HTML on the
    matplotlib backend, or PNG on bokeh without the optional export deps).
    """


def describe(value: Any) -> str:
    """One-line human description of a data value, for error messages.

    Examples
    --------
    >>> describe(np.zeros((2, 100)))
    'ndarray shape (2, 100)'
    >>> describe([np.zeros(50), np.zeros(48)])
    'list of 2 arrays (lengths 50, 48)'
    >>> describe(4.2)
    'scalar 4.2'
    """
    if value is None:
        return "None"
    if isinstance(value, str):
        return f"str {value!r}"
    if isinstance(value, np.ndarray):
        return f"ndarray shape {value.shape}"
    if np.isscalar(value):
        return f"scalar {value!r}"
    if isinstance(value, (list, tuple)):
        kind = type(value).__name__
        if value and all(isinstance(v, np.ndarray) for v in value):
            lengths = ", ".join(str(v.size) for v in value[:6])
            if len(value) > 6:
                lengths += ", ..."
            return f"{kind} of {len(value)} arrays (lengths {lengths})"
        return f"{kind} of length {len(value)}"
    if hasattr(value, "shape"):
        return f"{type(value).__name__} shape {tuple(value.shape)}"
    return type(value).__name__


def data_error(
    func: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    hint: str | None = None,
) -> BehavizDataError:
    """Build a :class:`BehavizDataError` with the standard layout::

        <func>: <message>
          <name>: <description of the value>
        Hint: <hint>

    ``details`` values run through :func:`describe` unless already strings,
    so callers can pass the raw offending objects directly.
    """
    lines = [f"{func}: {message}"]
    if details:
        width = max(len(k) for k in details)
        for k, v in details.items():
            desc = v if isinstance(v, str) else describe(v)
            lines.append(f"  {k:<{width}}: {desc}")
    if hint:
        lines.append(f"Hint: {hint}")
    return BehavizDataError("\n".join(lines))
