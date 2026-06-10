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
import functools

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from .plot_setup import plot_function
from .utils import validate_and_fix_inputs
from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="X", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Y", scale=ScaleType.LINEAR),
    show_legend=True,
)


def _make_xy_plot(
    plot_name: str,
    renderer_method: str,
    extra_params: Optional[dict] = None,
    docstring: Optional[str] = None,
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
    docstring : str, optional
        Docstring for the generated function.
    """
    extra = extra_params or {}

    @plot_function(default_spec=DEFAULT_SPEC)
    @functools.wraps(lambda x, y, ax=None, spec=None, **overrides: None)
    def _plot(
        x: np.ndarray,
        y: np.ndarray,
        ax: Optional[BehavizAxes] = None,
        spec: Optional[PlotSpec] = None,
        **overrides,
    ) -> tuple[BehavizFigure, BehavizAxes]:
        x, y = validate_and_fix_inputs(x, y)
        x = x.ravel()
        y = y.ravel()
        assert x.shape == y.shape, (
            f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."
        )
        getattr(get_renderer(), renderer_method)(ax, x, y, **extra, **overrides)
        return ax

    _plot.__name__ = plot_name
    _plot.__qualname__ = plot_name
    if docstring:
        _plot.__doc__ = docstring

    return _plot


# ---------------------------------------------------------------------------
# Generated standard plot functions
# ---------------------------------------------------------------------------
plot_line = _make_xy_plot(
    plot_name="plot_line",
    renderer_method="line",
    docstring=(
        "Plot a line.\n\n"
        "Args:\n"
        "    x: x-axis values\n"
        "    y: y-axis values\n"
        "    ax: axes to plot on (created if None)\n"
        "    spec: plot specification\n"
        "    **overrides: forwarded to the active backend renderer\n"
    ),
)

plot_scatter = _make_xy_plot(
    plot_name="plot_scatter",
    renderer_method="scatter",
    docstring=(
        "Plot a scatter.\n\n"
        "Args:\n"
        "    x: x-axis values\n"
        "    y: y-axis values\n"
        "    ax: axes to plot on (created if None)\n"
        "    spec: plot specification\n"
        "    **overrides: forwarded to the active backend renderer\n"
    ),
)

plot_step = _make_xy_plot(
    plot_name="plot_step",
    renderer_method="step",
    docstring=(
        "Plot a step function.\n\n"
        "Args:\n"
        "    x: x-axis values\n"
        "    y: y-axis values\n"
        "    ax: axes to plot on (created if None)\n"
        "    spec: plot specification\n"
        "    **overrides: forwarded to the active backend renderer\n"
        "        Pass where='pre'|'post'|'mid' to control step placement.\n"
    ),
)
