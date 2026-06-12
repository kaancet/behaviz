# core_factory.py
#
# Factory for generating standard (x, y) plot functions.
#
# Plot types with a simple (x, y) call signature are generated here rather
# than hand-written in core.py. Adding a new standard plot type only requires:
#   1. Registering it in plot_registry.py (with mpl_dummy_args if needed).
#   2. Implementing it on each backend Renderer.
#   3. Adding it to each overrider's VALID_CALL_KWARGS.
#
# No changes to this file or core.py are needed for simple plot types.
#
# Non-standard signatures (plot_errorbar, plot_violin) stay in core.py.

import numpy as np
from typing import Optional

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from .plot_setup import plot_function
from .channels import Channel
from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR),
    y=AxisSpec(scale=ScaleType.LINEAR),
    show_legend=True,
)

# Shared docstring sections so every generated function documents the input
# contract, the data= keyword and the return shape identically.
_XY_DOC_TEMPLATE = """{summary}

Args:
    x: x values, shape (N,). Array-like (list/tuple/ndarray/Series), or a
        column name when ``data=`` is given.
    y: y values, shape (N,). Same accepted types as ``x``.
    data: optional dataframe-like (pandas/polars/dict of arrays) that string
        channels are resolved against.
    ax: axes to plot on (created if None).
    spec: plot specification.
    **overrides: styling forwarded to the active backend renderer.{extra_args}

Returns:
    (fig, ax): backend figure and axes handles.

Raises:
    BehavizDataError: if shapes or types are inconsistent (the message names
        the offending argument).

Example:
    >>> bv.{example}
"""


def _make_xy_plot(
    plot_name: str,
    renderer_method: str,
    extra_params: Optional[dict] = None,
    summary: str = "",
    example: str = "",
    extra_args_doc: str = "",
) -> callable:
    """
    Build a decorated plot function for a standard (x, y) plot type.

    Parameters
    ----------
    plot_name : str
        Public name, e.g. "plot_line". Used as __name__ on the result.
    renderer_method : str
        The method name to call on the active Renderer, e.g. "line".
    extra_params : dict, optional
        Additional fixed keyword arguments forwarded to the renderer method,
        e.g. {"where": "pre"} for step plots.
    summary, example, extra_args_doc : str
        Filled into the shared docstring template.
    """
    extra = extra_params or {}

    @plot_function(
        default_spec=DEFAULT_SPEC,
        channels=[Channel("x"), Channel("y", same_length_as="x")],
    )
    def _plot(
        x: np.ndarray,
        y: np.ndarray,
        ax: Optional[BehavizAxes] = None,
        spec: Optional[PlotSpec] = None,
        **overrides,
    ) -> tuple[BehavizFigure, BehavizAxes]:

        x = x.ravel()
        y = y.ravel()
        assert x.shape == y.shape, (
            f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."
        )
        getattr(get_renderer(), renderer_method)(ax, x, y, **extra, **overrides)
        return ax

    _plot.__name__ = plot_name
    _plot.__qualname__ = plot_name
    _plot.__doc__ = _XY_DOC_TEMPLATE.format(summary=summary, example=example, extra_args=extra_args_doc)

    return _plot


# ---------------------------------------------------------------------------
# Generated standard plot functions
# ---------------------------------------------------------------------------
plot_line = _make_xy_plot(
    plot_name="plot_line",
    renderer_method="line",
    summary="Plot a line.",
    example='plot_line("time", "value", data=df)',
)

plot_scatter = _make_xy_plot(
    plot_name="plot_scatter",
    renderer_method="scatter",
    summary="Plot a scatter.",
    example="plot_scatter(x, y, s=20, color='#336699')",
)

plot_step = _make_xy_plot(
    plot_name="plot_step",
    renderer_method="step",
    summary="Plot a step function.",
    example="plot_step(x, y, where='mid')",
    extra_args_doc="\n        Pass where='pre'|'post'|'mid' to control step placement.",
)
