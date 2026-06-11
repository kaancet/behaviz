import numpy as np
from typing import Optional

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from .plot_setup import plot_function

from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec
from .utils import validate_and_fix_inputs

# Re-export generated functions so the public API surface is unchanged
from .core_factory import plot_line, plot_scatter, plot_step  # noqa: F401

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR),
    y=AxisSpec(scale=ScaleType.LINEAR),
    show_legend=True,
)


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y"))
def plot_bar(
    x: np.ndarray,
    y: np.ndarray,
    width: Optional[float | np.ndarray] = 0.2,
    bottom: Optional[np.ndarray] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Plot a bar chart.

    Args:
        x: x-axis positions
        y: bar heights
        width: bar width or array of widths. Defaults to 0.2.
        bottom: bar base offsets (for stacked bars). Defaults to None.
        ax: axes to plot on (created if None)
        spec: plot specification
        **overrides: forwarded to the active backend renderer
    """
    x, y, y_bottom = validate_and_fix_inputs(x, y, bottom)
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    if y_bottom is not None:
        y_bottom = y_bottom.ravel()
        assert y.shape == y_bottom.shape, f"Shape of y({y.shape}) does not match the shape of bottom({y_bottom.shape})."

    r = get_renderer()
    r.bar(ax, x, y, width=width, bottom=bottom, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y"))
def plot_errorbar(
    x: np.ndarray,
    y: np.ndarray,
    err: np.ndarray,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Plot data with error bars.

    Args:
        x: x-axis values
        y: y-axis values
        err: error bar sizes.
            shape (N,): symmetric +/- values.
            shape (2, N): separate lower and upper values (both positive magnitudes).
        ax: axes to plot on (created if None)
        spec: plot specification
        **overrides: forwarded to the active backend renderer
    """
    x, y, err = validate_and_fix_inputs(x, y, err)
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    if err.shape[0] != 2:
        assert y.shape == err.shape, (
            f"Shape of {spec.y.label}({y.shape}) does not match the shape of errors ({err.shape})."
        )
    else:
        assert y.shape[0] == err.shape[1], (
            f"Shape of {spec.y.label}({y.shape[0]}) does not match the shape of errors ({err.shape[1]})."
        )

    r = get_renderer()
    r.errorbar(ax, x, y, err, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y"))
def plot_violin(
    x: np.ndarray,
    ys: list[np.ndarray],
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Plot violin plots.

    Args:
        x: positions for each violin
        ys: list of data arrays, one per violin
        ax: axes to plot on (created if None)
        spec: plot specification
        **overrides: forwarded to the active backend renderer
    """
    x, ys = validate_and_fix_inputs(x, ys)
    x = x.ravel()

    # Normalise ys to a list of 1-D arrays — one distribution per x position.
    # Without this, a 2-D array (n_positions, n_samples) is read column-wise by
    # matplotlib's violinplot (one violin per *column*), which both produces the
    # wrong number of violins and disagrees with the bokeh/seaborn backends. A
    # plain list of arrays is already in this form and is unaffected.
    ys = [np.asarray(yi).ravel() for yi in ys]

    assert len(x) == len(ys), f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({len(ys)})."

    r = get_renderer()
    vp = r.violin(ax, ys, x, **overrides)
    return ax, vp


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y"))
def plot_vertical(
    x: np.ndarray,
    ymin: Optional[np.ndarray] = None,
    ymax: Optional[np.ndarray] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:

    if ymin is None:
        ymin = np.zeros(len(x))

    if ymax is None:
        ymax = np.ones(len(x))

    assert len(x) == len(ymin) == len(ymax), f"Unequal shapes for x{len(x)}, ymin{len(ymin)} and ymax{len(ymax)}."

    r = get_renderer()
    for xi, ymini, ymaxi in zip(x, ymin, ymax):
        r.vertical(ax, xi, ymini, ymaxi, **overrides)

    return ax


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y"))
def plot_horizontal(
    y: np.ndarray,
    xmin: Optional[np.ndarray] = None,
    xmax: Optional[np.ndarray] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:

    if xmin is None:
        xmin = np.zeros(len(y))

    if xmax is None:
        xmax = np.ones(len(y))

    assert len(y) == len(xmin) == len(xmax), f"Unequal shapes for x{len(y)}, ymin{len(xmin)} and ymax{len(xmax)}."

    r = get_renderer()
    for yi, xmini, xmaxi in zip(y, xmin, xmax):
        r.horizontal(ax, yi, xmini, xmaxi, **overrides)

    return ax
