import numpy as np
from typing import Optional

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from .plot_setup import plot_function

from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec
from .utils import validate_and_fix_inputs
from ..spec.colorbar_spec import ColorbarSpec

# Re-export generated functions so the public API surface is unchanged
from .core_factory import plot_line, plot_scatter, plot_step  # noqa: F401

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR),
    y=AxisSpec(scale=ScaleType.LINEAR),
    show_legend=True,
)

PIE_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(6, 6)),
    x=AxisSpec(spines=[], grid=False, ticks=[]),
    y=AxisSpec(spines=[], grid=False, ticks=[]),
    show_legend=False,
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


@plot_function(default_spec=DEFAULT_SPEC)
def plot_image(
    data: np.ndarray,
    extent: Optional[tuple] = None,
    origin: str = "upper",
    cmap: str = "viridis",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    colorbar: bool | str | ColorbarSpec = False,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Display a 2-D array as an image (heatmap), backend-agnostically.

    Args:
        data: 2-D array of scalar values, mapped to colour via ``cmap``.
        extent: (xmin, xmax, ymin, ymax) placement in data coordinates.
            Defaults to (0, ncols, 0, nrows).
        origin: "upper" (row 0 at top, matplotlib default) or "lower".
        cmap: matplotlib colormap name; converted to a palette on bokeh so the
            same name looks the same on every backend.
        vmin, vmax: colour-scale limits. Default to the data min/max.
        colorbar: add a colorbar. ``True`` for a default bar, a ``str`` for a
            labelled bar, or a ``ColorbarSpec`` for full control. The mappable is
            threaded internally — no need to capture it yourself.
        ax: axes/figure to draw on (created if None).
        spec: plot specification.
        **overrides: forwarded to the active backend renderer.
    """
    data = np.asarray(data)
    assert data.ndim == 2, f"plot_image currently supports 2-D arrays only, got shape {data.shape}."

    r = get_renderer()
    mappable = r.image(ax, data, extent=extent, origin=origin, cmap=cmap, vmin=vmin, vmax=vmax, **overrides)

    if colorbar:
        r.colorbar(ax, mappable, ColorbarSpec.coerce(colorbar))
    return ax


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y1", "y2"))
def plot_fill_between(
    x: np.ndarray,
    y1: np.ndarray,
    y2: float | np.ndarray = 0,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Fill the band between two curves — e.g. an SEM/CI ribbon, or a stacked area.

    Args:
        x: x-axis values.
        y1: upper curve (or the single curve when filling down to ``y2``).
        y2: lower curve; a scalar (default 0) fills down to a constant.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: forwarded to the active backend renderer (e.g. ``color``, ``alpha``).
    """
    x = np.asarray(x, dtype=float).ravel()
    # Broadcast so a scalar y2 (or y1) becomes an array — bokeh's varea needs arrays.
    y1 = np.broadcast_to(y1, x.shape).astype(float)
    y2 = np.broadcast_to(y2, x.shape).astype(float)

    r = get_renderer()
    r.fill_between(ax, x, y1, y2, **overrides)
    return ax


PIE_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(6, 6)),
    x=AxisSpec(spines=[], grid=False, ticks=[]),
    y=AxisSpec(spines=[], grid=False, ticks=[]),
    show_legend=False,
)


@plot_function(default_spec=PIE_SPEC)
def plot_pie(
    sizes: np.ndarray,
    labels: Optional[list] = None,
    colors: Optional[list] = None,
    autopct: Optional[str] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Pie chart for showing ratios / proportions.

    Args:
        sizes: slice sizes (need not sum to 1 — they are normalised).
        labels: per-slice labels.
        colors: per-slice colours (defaults to a categorical palette).
        autopct: percentage format string, e.g. ``"%.1f%%"`` (matplotlib/seaborn only).
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: forwarded to the active backend renderer.
    """
    sizes = np.asarray(sizes, dtype=float)
    r = get_renderer()
    r.pie(ax, sizes, labels=labels, colors=colors, autopct=autopct, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC, data_args=("x", "y"))
def plot_hexbin(
    x: np.ndarray,
    y: np.ndarray,
    gridsize: int = 30,
    cmap: str = "viridis",
    colorbar: bool | str | ColorbarSpec = False,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """2-D histogram of point data, binned into hexagons and coloured by count.

    Unlike ``plot_image`` (which displays a pre-computed grid), ``plot_hexbin``
    bins raw ``(x, y)`` points — use it for density / 2-D-histogram views of
    scatter-like data.

    Args:
        x, y: point coordinates.
        gridsize: number of hexagons across the x-range.
        cmap: matplotlib colormap name (converted to a palette on bokeh).
        colorbar: add a count colorbar — ``True`` / ``str`` / ``ColorbarSpec``.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: forwarded to the active backend renderer.
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()

    r = get_renderer()
    mappable = r.hexbin(ax, x, y, gridsize=gridsize, cmap=cmap, **overrides)

    if colorbar:
        r.colorbar(ax, mappable, ColorbarSpec.coerce(colorbar))

    return ax
