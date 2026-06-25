import numpy as np
from typing import Optional

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from .plot_setup import plot_function
from .channels import Channel
from .errors import data_error

from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec
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


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("x"),
        Channel("y", same_length_as="x"),
        Channel("width", kind="scalar_or_vector", required=False, same_length_as="x"),
        Channel("bottom", kind="scalar_or_vector", required=False, same_length_as="x"),
    ],
    grouping="dodge",
)
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
        x: bar positions, shape (N,). Array-like (list/tuple/ndarray/Series),
            or a column name when ``data=`` is given.
        y: bar heights, shape (N,). Same accepted types as ``x``.
        width: bar width — a single scalar or one width per bar, shape (N,).
            Defaults to 0.2.
        bottom: bar base offsets for stacked bars — scalar or shape (N,).
            Defaults to 0.
        data: optional dataframe-like (pandas/polars/dict of arrays) that
            string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if shapes or types are inconsistent (the message
            names the offending argument).

    Example:
        >>> bv.plot_bar([0, 1, 2], [3, 5, 2], width=0.5)
    """
    r = get_renderer()
    r.bar(ax, x, y, width=width, bottom=bottom, **overrides)
    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("y"),
        Channel("x", same_length_as="y"),
        Channel("height", kind="scalar_or_vector", required=False, same_length_as="y"),
        Channel("left", kind="scalar_or_vector", required=False, same_length_as="y"),
    ],
    grouping="dodge",
)
def plot_hbar(
    y: np.ndarray,
    x: np.ndarray,
    height: Optional[float | np.ndarray] = 0.2,
    left: Optional[np.ndarray] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Plot a horizontal bar chart.

    Args:
        y: bar positions, shape (N,). Array-like (list/tuple/ndarray/Series),
            or a column name when ``data=`` is given.
        x: bar widths, shape (N,). Same accepted types as ``x``.
        height: bar height, a single scalar or one width per bar, shape (N,).
            Defaults to 0.2.
        left: bar base offsets for horizontal stacked bars, scalar or shape (N,).
            Defaults to 0.
        data: optional dataframe-like (pandas/polars/dict of arrays) that
            string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if shapes or types are inconsistent (the message
            names the offending argument).

    Example:
        >>> bv.plot_hbar([0, 1, 2], [3, 5, 2], height=0.5)
    """
    r = get_renderer()
    r.hbar(ax, y, x, height=height, left=left, **overrides)
    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("x"),
        Channel("y", same_length_as="x"),
        Channel("err", kind="raw"),
    ],
    grouping="dodge",
)
def plot_errorbar(
    x: np.ndarray,
    y: np.ndarray,
    err: np.ndarray,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Plot data points with error bars.

    Args:
        x: x values, shape (N,). Array-like, or a column name when ``data=``
            is given.
        y: y values, shape (N,). Same accepted types as ``x``.
        err: error bar sizes.
            shape (N,): symmetric +/- values.
            shape (2, N): separate lower and upper magnitudes (both positive).
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer
            (e.g. ``capsize``, ``elinewidth``).

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if shapes or types are inconsistent.

    Example:
        >>> bv.plot_errorbar(x, means, sems, capsize=4)
    """
    err = np.asarray(err)
    n = x.shape[0]
    if not (err.shape == (n,) or err.shape == (2, n)):
        raise data_error(
            "plot_errorbar",
            "`err` must be shape (N,) for symmetric or (2, N) for asymmetric errors.",
            details={"x": x, "err": err},
            hint=f"N = {n} here.",
        )

    r = get_renderer()
    r.errorbar(ax, x, y, err, **overrides)
    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("x"),
        Channel("ys", kind="vectors", same_length_as="x"),
    ],
)
def plot_violin(
    x: np.ndarray,
    ys: list[np.ndarray],
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Plot one violin (distribution) per x position.

    Args:
        x: violin positions, shape (N,). Array-like, or a column name when
            ``data=`` is given.
        ys: the distributions — a sequence of N 1-D arrays (ragged lengths
            allowed), or a 2-D array read as one distribution per *row*.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax, vp): figure, axes, and the violin artist dict
            (``vp["bodies"]`` holds one artist per violin on every backend).

    Raises:
        BehavizDataError: if ``len(ys) != len(x)`` or the inputs are not
            numeric sequences.

    Example:
        >>> bv.plot_violin([0, 1, 2], [groupA, groupB, groupC])
    """
    r = get_renderer()
    vp = r.violin(ax, ys, x, **overrides)
    return ax, vp


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("x"),
        Channel("ymin", kind="scalar_or_vector", required=False, same_length_as="x"),
        Channel("ymax", kind="scalar_or_vector", required=False, same_length_as="x"),
    ],
)
def plot_vertical(
    x: np.ndarray,
    ymin: Optional[np.ndarray] = None,
    ymax: Optional[np.ndarray] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Draw one or more vertical lines.

    Args:
        x: x position(s) of the line(s) — a scalar or shape (N,) array-like,
            or a column name when ``data=`` is given.
        ymin: lower end(s) in axis fraction (0 = bottom, 1 = top) — scalar or
            shape (N,). Defaults to 0.
        ymax: upper end(s) in axis fraction — scalar or shape (N,).
            Defaults to 1.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if lengths are inconsistent.

    Example:
        >>> bv.plot_vertical(stimulus_onset, color="#888888", linestyle="--")
    """
    ymin = np.zeros(x.shape) if ymin is None else np.broadcast_to(ymin, x.shape)
    ymax = np.ones(x.shape) if ymax is None else np.broadcast_to(ymax, x.shape)

    r = get_renderer()
    for xi, ymini, ymaxi in zip(x, ymin, ymax):
        r.vertical(ax, xi, ymini, ymaxi, **overrides)

    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("y"),
        Channel("xmin", kind="scalar_or_vector", required=False, same_length_as="y"),
        Channel("xmax", kind="scalar_or_vector", required=False, same_length_as="y"),
    ],
)
def plot_horizontal(
    y: np.ndarray,
    xmin: Optional[np.ndarray] = None,
    xmax: Optional[np.ndarray] = None,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Draw one or more horizontal lines.

    Args:
        y: y position(s) of the line(s) — a scalar or shape (N,) array-like,
            or a column name when ``data=`` is given.
        xmin: left end(s) in axis fraction (0 = left, 1 = right) — scalar or
            shape (N,). Defaults to 0.
        xmax: right end(s) in axis fraction — scalar or shape (N,).
            Defaults to 1.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if lengths are inconsistent.

    Example:
        >>> bv.plot_horizontal(0.5, color="#888888", linestyle=":")
    """
    xmin = np.zeros(y.shape) if xmin is None else np.broadcast_to(xmin, y.shape)
    xmax = np.ones(y.shape) if xmax is None else np.broadcast_to(xmax, y.shape)
    r = get_renderer()
    for yi, xmini, xmaxi in zip(y, xmin, xmax):
        r.horizontal(ax, yi, xmini, xmaxi, **overrides)

    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[Channel("values", kind="grid")],
)
def plot_image(
    values: np.ndarray,
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
        values: 2-D array of scalar values, mapped to colour via ``cmap``.
        extent: (xmin, xmax, ymin, ymax) placement in data coordinates.
            Defaults to (0, ncols, 0, nrows).
        origin: "upper" (row 0 at top, matplotlib default) or "lower".
        cmap: matplotlib colormap name; converted to a palette on bokeh so the
            same name looks the same on every backend.
        vmin, vmax: colour-scale limits. Default to the data min/max.
        colorbar: add a colorbar. ``True`` for a default bar, a ``str`` for a
            labelled bar, or a ``ColorbarSpec`` for full control. The mappable
            is threaded internally — no need to capture it yourself.
        ax: axes/figure to draw on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if ``values`` is not a numeric 2-D array.

    Example:
        >>> bv.plot_image(correlation_matrix, cmap="magma", colorbar="r")
    """
    r = get_renderer()
    mappable = r.image(ax, values, extent=extent, origin=origin, cmap=cmap, vmin=vmin, vmax=vmax, **overrides)

    if colorbar:
        r.colorbar(ax, mappable, ColorbarSpec.coerce(colorbar))
    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("x"),
        Channel("y1", kind="scalar_or_vector", same_length_as="x"),
        Channel("y2", kind="scalar_or_vector", required=False, same_length_as="x"),
    ],
    grouping="overlay",
)
def plot_fill_between(
    x: np.ndarray,
    y1: np.ndarray,
    y2: float | np.ndarray = 0,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Fill the band between two curves — e.g. an SEM/CI ribbon, or an area fill.

    Args:
        x: x values, shape (N,). Array-like, or a column name when ``data=``
            is given.
        y1: upper curve, shape (N,) (or a scalar for a constant level).
        y2: lower curve, shape (N,); a scalar (default 0) fills down to a
            constant.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer
            (e.g. ``color``, ``alpha``).

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if shapes or types are inconsistent.

    Example:
        >>> bv.plot_fill_between(t, mean - sem, mean + sem, alpha=0.3)
    """
    # Broadcast so scalar levels become arrays — bokeh's varea needs arrays.
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


@plot_function(
    default_spec=PIE_SPEC,
    channels=[Channel("sizes")],
)
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
        sizes: slice sizes, shape (N,) — they need not sum to 1, they are
            normalised. Array-like, or a column name when ``data=`` is given.
        labels: per-slice labels (length N).
        colors: per-slice colours (defaults to a categorical palette).
        autopct: percentage format string, e.g. ``"%.1f%%"``
            (matplotlib/seaborn only).
        data: optional dataframe-like the string channel is resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if ``sizes`` is not a numeric 1-D sequence.

    Example:
        >>> bv.plot_pie([40, 35, 25], labels=["go", "no-go", "miss"])
    """
    sizes = sizes.astype(float)
    r = get_renderer()
    r.pie(ax, sizes, labels=labels, colors=colors, autopct=autopct, **overrides)
    return ax


@plot_function(
    default_spec=DEFAULT_SPEC,
    channels=[
        Channel("x"),
        Channel("y", same_length_as="x"),
    ],
)
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
        x: point x coordinates, shape (N,). Array-like, or a column name when
            ``data=`` is given.
        y: point y coordinates, shape (N,). Same accepted types as ``x``.
        gridsize: number of hexagons across the x-range.
        cmap: matplotlib colormap name (converted to a palette on bokeh).
        colorbar: add a count colorbar — ``True`` / ``str`` / ``ColorbarSpec``.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if shapes or types are inconsistent.

    Example:
        >>> bv.plot_hexbin("rt", "accuracy", data=df, colorbar="trials")
    """
    x = x.astype(float)
    y = y.astype(float)

    r = get_renderer()
    mappable = r.hexbin(ax, x, y, gridsize=gridsize, cmap=cmap, **overrides)

    if colorbar:
        r.colorbar(ax, mappable, ColorbarSpec.coerce(colorbar))

    return ax
