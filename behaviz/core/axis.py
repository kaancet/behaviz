from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from ..backends.renderer_manager import get_renderer
from ..spec.plot_spec import PlotSpec
from .context import get_active_canvas, get_axes_spec, set_active_canvas, set_axes_spec


def _set_axis(dim: str, first, second, ax, fields: dict) -> None:
    """Change the axis; scale, limit, labels etc.
    Helper function that works out which axes and scale the caller meant, changes only that axis,
    and remembers the result so later plot calls on the same axes keep it.

    Args:
        dim: The axis dimension, either "x" or "y"
        first (str | Axes | None): The scale name, or the axes if it is not a string
        second (str | None): The scale, when `first` was the axes. Must be None otherwise
        ax (Axes | None): The axes as a keyword. None falls back to the active `bv.canvas` axes
        fields (dict): Other AxisSpec fields to set (lim, label, ticks...).
            `scale` is added to it when given, so it is mutated in place

    Raises:
        TypeError: The axes was given both positionally and as `ax=`
        TypeError: Two scales were given (`set_xaxis("log", "linear")`)
        ValueError: No axes given and no active canvas
    """
    if first is None or isinstance(first, str):  # set_xaxis("log")
        if second is not None:
            raise TypeError("set_xaxis/set_yaxis: pass the axes first, then the scale: set_xaxis(ax, 'log').")
        scale = first
    else:  # set_xaxis(ax, "log")
        if ax is not None:
            raise TypeError("set_xaxis/set_yaxis: got the axes both positionally and as ax=.")
        ax, scale = first, second

    active = get_active_canvas()
    if ax is None:
        if active is None:
            raise ValueError("set_xaxis/set_yaxis: pass an axes, or call inside a `bv.canvas(...)` block.")
        ax = active.ax
    on_canvas = active is not None and active.ax is ax
    # An axes we never drew on has no spec of ours: start from a neutral one.
    spec = active.spec if on_canvas else get_axes_spec(ax) or PlotSpec()
    if scale is not None:
        fields["scale"] = scale
    # replace() re-runs AxisSpec validation: a bad scale or field name raises here.
    spec = replace(spec, **{dim: replace(getattr(spec, dim), **fields)})
    get_renderer().apply_axis_spec(ax, spec)
    set_axes_spec(ax, spec)
    if on_canvas:  # later plot calls in the block inherit it
        set_active_canvas(ax, spec)


def set_xaxis(first: Any = None, second: Optional[str] = None, *, ax: Any = None, **fields) -> None:
    """Change the x-axis

    Call it as ``set_xaxis("log")`` inside a ``bv.canvas`` block, or name the axes:
    ``set_xaxis(ax, "log")`` / ``set_xaxis("log", ax=ax)``.

    Args:
        first: the scale (``"linear"``, ``"log"``, ``"symlog"``, ``"logit"``), or the axes.
        second: the scale, when the axes came first. ``None`` keeps the current scale.
        ax: the axes, as a keyword. Defaults to the active ``bv.canvas`` axes.
        **fields: any other :class:`AxisSpec` field, e.g. ``lim``, ``label``, ``ticks``.

    An axes behaviz has not drawn on is restyled from a default spec, so its existing
    labels are reset.

    Example:
        >>> fig, ax = bv.plot_line(x, y)
        >>> bv.set_xaxis(ax, "log", lim=(1, 100), label="Time", unit="s")
    """
    _set_axis("x", first, second, ax, fields)


def set_yaxis(first: Any = None, second: Optional[str] = None, *, ax: Any = None, **fields) -> None:
    """Change the y-axis

    Call it as ``set_yaxis("log")`` inside a ``bv.canvas`` block, or name the axes:
        ``set_yaxis(ax, "log")`` / ``set_yaxis("log", ax=ax)``.

        Args:
            first: the scale (``"linear"``, ``"log"``, ``"symlog"``, ``"logit"``), or the axes.
            second: the scale, when the axes came first. ``None`` keeps the current scale.
            ax: the axes, as a keyword. Defaults to the active ``bv.canvas`` axes.
            **fields: any other :class:`AxisSpec` field, e.g. ``lim``, ``label``, ``ticks``.

        An axes behaviz has not drawn on is restyled from a default spec, so its existing
        labels are reset.

        Example:
            >>> fig, ax = bv.plot_line(x, y)
            >>> bv.set_yaxis(ax, "log", lim=(1, 100), label="Time", unit="s")
    """
    _set_axis("y", first, second, ax, fields)
