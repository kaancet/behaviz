"""Active-canvas state for the ``bv.canvas`` context manager.

A ``bv.canvas(...)`` block creates one figure and lets plot calls inside it omit
``ax=`` — they auto-target the block's axes. That binding is stored here as a
``ContextVar`` so it is correct under threads/async and always unwinds with the
``with`` block. The decorator ([plot_setup.py](plot_setup.py)) reads it; the
context manager ([../io.py](../io.py)) sets and clears it. Kept in its own
module so neither importer has to depend on the other.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from ..spec.plot_spec import PlotSpec


@dataclass(frozen=True)
class ActiveCanvas:
    """The axes (and its spec) that bare plot calls should draw onto."""

    ax: Any
    spec: PlotSpec


_ACTIVE_CANVAS: ContextVar[ActiveCanvas | None] = ContextVar("behaviz_active_canvas", default=None)

# The spec each axes was last drawn/changed with, so ``bv.set_xaxis(..., ax=ax)``
# can change one setting without resetting the rest. Weak: dies with the axes.
_AXES_SPECS: WeakKeyDictionary[Any, PlotSpec] = WeakKeyDictionary()


def get_axes_spec(ax: Any) -> PlotSpec | None:
    return _AXES_SPECS.get(ax)


def set_axes_spec(ax: Any, spec: PlotSpec) -> None:
    _AXES_SPECS[ax] = spec


def get_active_canvas() -> ActiveCanvas | None:
    """Return the active canvas, or ``None`` when not inside a ``bv.canvas`` block."""
    return _ACTIVE_CANVAS.get()


def set_active_canvas(ax: Any, spec: PlotSpec) -> Token:
    """Bind ``ax``/``spec`` as the active canvas; returns a token for :func:`clear_active_canvas`."""
    return _ACTIVE_CANVAS.set(ActiveCanvas(ax=ax, spec=spec))


def clear_active_canvas(token: Token) -> None:
    """Restore the previous active canvas (always called when the block exits)."""
    _ACTIVE_CANVAS.reset(token)
