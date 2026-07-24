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

import numpy as np

from .backends.renderer_manager import get_renderer
from .core import layout as _layout
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
def canvas(
    spec: Optional[PlotSpec] = None,
    *,
    ax: Any = None,
    save: Optional[str] = None,
    show: bool = False,
    **save_kwargs,
):
    """Draw several plots onto one figure, then save/show it on exit.

    Inside the block, plot calls that omit ``ax=`` automatically target the
    block's axes (and inherit ``spec`` unless they pass their own). When the
    block exits cleanly the figure is saved (if ``save`` is given) and shown
    (if ``show`` is True). If the block raises, nothing is saved.

    Args:
        spec: the figure/axis specification for the shared axes.
        ax: draw onto this existing axes instead of creating a figure — e.g. one
            cell of a ``plt.subplots`` grid. When given, ``save``/``show`` act on
            its parent figure.
        save: optional path to write on exit (extension selects the format).
        show: display the figure on exit.
        **save_kwargs: forwarded to :func:`save`.

    Yields:
        The shared axes object (also usable explicitly, e.g. for ``plot_pval``).

    Example:
        >>> with bv.canvas(save="fig.png") as ax:
        ...     bv.plot_line(x, y)
        ...     bv.plot_scatter(x, y2)
        >>> f, axs = plt.subplots(1, 2)
        >>> with bv.canvas(ax=axs[0]) as a:
        ...     bv.plot_line(x, y)
    """
    r = get_renderer()
    spec = spec or _DEFAULT_SPEC
    if ax is None:
        fig, ax = r.make_figure(spec)
    else:
        fig = r.get_figure(ax)
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


@contextmanager
def grid(
    nrows: Optional[int] = None,
    ncols: Optional[int] = None,
    *,
    mosaic=None,
    spec: Optional[PlotSpec] = None,
    width_ratios=None,
    height_ratios=None,
    sharex: bool = False,
    sharey: bool = False,
    wspace=None,
    hspace=None,
    suptitle=None,
    layout: Optional[str] = None,
    save: Optional[str] = None,
    show: bool = False,
    **save_kwargs,
):
    """Create a multi-panel figure, then save/show it on exit.

    Unlike :func:`canvas` (one shared axes) a grid has several panels, so there
    is no unambiguous default target — plot calls inside the block must pass
    ``ax=``. Each call may pass its own ``spec=``; the grid-level ``spec``
    supplies the figure size/dpi/style.

    Args:
        nrows, ncols: shape of a regular grid. Mutually exclusive with ``mosaic``.
        mosaic: an ASCII layout — one line per row, one character per cell, where
            repeating a character makes that panel span those cells and ``"."``
            leaves a cell empty. Yields a ``{name: ax}`` dict instead of an array.
        spec: figure/axis specification for the figure as a whole.
        width_ratios, height_ratios: relative column widths / row heights.
        sharex, sharey: link panel axes.
        wspace, hspace: spacing between panels.
        suptitle: figure-level title.
        layout: ``"tight"`` or ``"constrained"`` (matplotlib/seaborn only).
        save: optional path to write on exit. show: display on exit.

    Yields:
        A 2-D numpy object array indexed ``axs[row, col]``, or — when ``mosaic``
        is given — a ``{name: ax}`` dict.

    Example:
        >>> with bv.grid(2, 2, save="fig.png") as axs:
        ...     bv.plot_line(x, y, ax=axs[0, 0])
        >>> with bv.grid(mosaic="AAB\\nCCB") as axs:
        ...     bv.plot_line(x, y, ax=axs["A"])
    """
    r = get_renderer()
    spec = spec or _DEFAULT_SPEC
    placements, n_rows, n_cols = _layout.resolve(nrows, ncols, mosaic)
    _layout.check_ratios(width_ratios, height_ratios, n_rows, n_cols)

    fig, axes = r.make_grid(
        spec,
        placements,
        n_rows,
        n_cols,
        width_ratios=width_ratios,
        height_ratios=height_ratios,
        sharex=sharex,
        sharey=sharey,
        wspace=wspace,
        hspace=hspace,
        suptitle=suptitle,
    )
    if layout is not None:
        r.set_layout_engine(fig, layout)  # raises NotImplementedError on bokeh

    if mosaic is None:  # positional access for a regular grid
        out = np.empty((n_rows, n_cols), dtype=object)
        for p in placements:
            out[p.row, p.col] = axes[p.name]
    else:
        out = axes

    yield out

    if save is not None:
        r.save(fig, save, **save_kwargs)
    if show:
        r.show(fig)


def inset(parent_ax: Any, bounds, spec: Optional[PlotSpec] = None) -> Any:
    """Create an inset axes inside ``parent_ax`` (matplotlib/seaborn only).

    ``bounds`` is ``(x, y, width, height)`` in parent-axes fractions.
    Raises ``NotImplementedError`` on backends without an inset concept.
    """
    return get_renderer().make_inset(parent_ax, bounds, spec)


def shared_colorbar(fig: Any, axes, mappable=None, **kwargs) -> Any:
    """Draw one colorbar shared by several panels (matplotlib/seaborn only).

    ``axes`` is the panels the bar borrows space from; ``mappable`` is the
    artist defining the colour scale (e.g. the return of ``plot_image``).
    Raises ``NotImplementedError`` on backends without a shared-colorbar concept.
    """
    axes = list(axes.values()) if isinstance(axes, dict) else list(np.ravel(axes))
    return get_renderer().shared_colorbar(fig, axes, mappable, **kwargs)
