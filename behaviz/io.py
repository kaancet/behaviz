"""Unified, backend-agnostic figure output: ``bv.save`` and ``bv.canvas``.

``save`` dispatches to the active renderer, which validates the
backend/extension combination and raises ``BehavizSaveError`` otherwise.

``canvas`` is a context manager that creates one figure, lets plot calls inside
the block omit ``ax=`` (they auto-target the block's axes), and saves and/or
shows the figure once on exit.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Optional

from .backends.renderer_manager import get_renderer
from .core.context import set_active_canvas, clear_active_canvas
from .spec.plot_spec import PlotSpec
from .spec.axis_spec import AxisSpec, ScaleType
from .spec.figure_spec import FigureSpec

# Mirrors core.DEFAULT_SPEC; defined locally to avoid importing the plot
# functions (and their heavy transitive deps) just for a default figure.
_DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR),
    y=AxisSpec(scale=ScaleType.LINEAR),
    show_legend=True,
)


def save(fig: Any, path, **kwargs) -> str:
    """Save ``fig`` to ``path`` using the active backend.

    The format is taken from the file extension and validated against the
    backend (e.g. ``.png``/``.pdf``/``.svg`` on matplotlib/seaborn, ``.html``
    on bokeh). Unsupported combinations raise
    :class:`~behaviz.core.errors.BehavizSaveError`.

    Args:
        fig: the figure handle returned by any plot function (the first element
            of its ``(fig, ax)`` return).
        path: destination path; its extension selects the format.
        **kwargs: forwarded to the backend writer (e.g. ``dpi=`` on matplotlib).

    Returns:
        The path written, as a string.
    """
    return get_renderer().save(fig, path, **kwargs)


@contextmanager
def canvas(spec: Optional[PlotSpec] = None, *, save: Optional[str] = None, show: bool = False, **save_kwargs):
    """Draw several plots onto one figure, then save/show it on exit.

    Inside the block, plot calls that omit ``ax=`` automatically target the
    block's axes (and inherit ``spec`` unless they pass their own). When the
    block exits cleanly the figure is saved (if ``save`` is given) and shown
    (if ``show`` is True). If the block raises, nothing is saved.

    Args:
        spec: the figure/axis specification for the shared axes.
        save: optional path to write on exit (extension selects the format).
        show: display the figure on exit.
        **save_kwargs: forwarded to :func:`save`.

    Yields:
        The shared axes object (also usable explicitly, e.g. for ``plot_pval``).

    Example:
        >>> with bv.canvas(save="fig.png") as ax:
        ...     bv.plot_line(x, y)
        ...     bv.plot_scatter(x, y2)
    """
    r = get_renderer()
    spec = spec or _DEFAULT_SPEC
    fig, ax = r.make_figure(spec)
    token = set_active_canvas(ax, spec)
    try:
        yield ax
    finally:
        clear_active_canvas(token)

    # Reached only when the block did not raise (the finally above always runs;
    # this line is skipped when an exception propagates).
    if save is not None:
        r.save(fig, save, **save_kwargs)
    if show:
        r.show(fig)
