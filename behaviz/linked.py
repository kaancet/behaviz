"""Linked plots — one shared ``ColumnDataSource`` for cross-plot brushing.

This is a thin, **bokeh-only** layer; the core/backends are untouched. The
generic backend pipeline never deals with a ColumnDataSource — only bokeh can
support linked selection, so all of that knowledge lives here.

    src = bv.linked(df)
    bv.set_renderer("bokeh")
    f1 = bv.linked_plot(src, "scatter", "x", "y", color="#36c")
    f2 = bv.linked_plot(src, "line",    "x", "z")
    # box/lasso-select in f1 highlights the same rows in f2 (shared source).

Every linked plot draws from the *same* source, so a selection in one figure
(or a DataTable on ``src.cds``) highlights the same rows everywhere — bokeh's
native linked selection, no callbacks. Off bokeh, ``linked_plot`` falls back to
the normal primitive (plain data, no live linking — static backends can't brush).
"""

from __future__ import annotations

from typing import Any
from dataclasses import replace

import numpy as np

from .core.data_source import _available_columns
from .backends.renderer_manager import get_renderer
from .spec.plot_spec import PlotSpec
from .spec.figure_spec import FigureSpec

_LINKED_SPEC = PlotSpec(figure=FigureSpec(figsize=(6, 5)))


class LinkedSource:
    """A dataframe/dict backed by one shared bokeh ``ColumnDataSource``."""

    def __init__(self, data: Any):
        self._data = data
        self._cds = None  # built lazily so importing behaviz never needs bokeh

    @property
    def cds(self):
        from bokeh.models import ColumnDataSource

        if self._cds is None:
            cols = {c: np.asarray(self._data[c]) for c in _available_columns(self._data)}
            self._cds = ColumnDataSource(cols)
        return self._cds

    # duck-type as a data= source so the normal plot functions accept it
    def __getitem__(self, col):
        return self._data[col]

    @property
    def columns(self):
        return _available_columns(self._data)


def linked(data: Any) -> LinkedSource:
    """Wrap ``data`` so plots drawn from it share one source and brush together."""
    return LinkedSource(data)


def _add_select_tools(fig) -> None:
    """Add box/lasso/tap select tools once, so linked figures are brushable."""
    from bokeh.models import BoxSelectTool, LassoSelectTool, TapTool

    kinds = {type(t) for t in fig.tools}
    for tool in (BoxSelectTool, LassoSelectTool, TapTool):
        if tool not in kinds:
            fig.add_tools(tool())


def linked_plot(src: LinkedSource, plot: str, x: str, y: str, *, spec: PlotSpec = None, **kwargs):
    """Draw an x/y plot from a shared source so it brushes with other linked plots.

    Args:
        src: a :func:`linked` source.
        plot: glyph name — ``"scatter"``, ``"line"`` or ``"step"``.
        x, y: column names in ``src``.
        spec: optional PlotSpec (styling); a sensible default is used otherwise.
        **kwargs: styling overrides, routed exactly as in the normal plots
            (``color``, ``size``, ``alpha``, …).

    Returns:
        (fig, ax). On bokeh both are the linked figure; off bokeh this falls back
        to the normal ``bv.plot_<plot>`` (no linking — static backends can't brush).
    """
    r = get_renderer()
    spec = spec or _LINKED_SPEC

    if r.name != "bokeh":
        import behaviz as bv

        return getattr(bv, f"plot_{plot}")(x, y, data=src, spec=spec, **kwargs)

    # Auto-label axes from the column names when the spec hasn't set them — same
    # convenience the normal data= path gives (the decorator does this for us
    # there; linked_plot bypasses the decorator, so do it here).
    if not spec.x.label or not spec.y.label:
        spec = replace(
            spec,
            x=replace(spec.x, label=spec.x.label or x),
            y=replace(spec.y, label=spec.y.label or y),
        )

    fig, ax = r.make_figure(spec)
    call_kw, post_kw = r._ovr.route(plot, dict(kwargs))  # canonical → bokeh (color, size, …)
    glyph = getattr(fig, plot)(x=x, y=y, source=src.cds, **call_kw)
    r._ovr.apply_post(glyph, post_kw)
    r.apply_axis_spec(ax, spec)
    _add_select_tools(fig)
    return fig, ax
