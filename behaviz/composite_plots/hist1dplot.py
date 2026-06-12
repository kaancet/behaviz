import numpy as np
from typing import Optional
from numpy.typing import ArrayLike
from scipy.stats import gaussian_kde

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_bar, plot_line, Channel
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

from behaviz.composite_plots.styling import split_styles


HIST1D_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(label="X", unit="", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Counts", unit="", scale=ScaleType.LINEAR),
    title="Distribution plot",
)


@plot_function(
    default_spec=HIST1D_SPEC,
    channels=[Channel("values")],
)
def plot_hist1d(
    values: ArrayLike,
    bin_width: float,
    density: bool = False,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """1-D histogram of raw samples, with an optional density (KDE) curve.

    Args:
        values: the raw samples to bin, shape (N,). Array-like, or a column
            name when ``data=`` is given.
        bin_width: histogram bin width in data units.
        density: also draw a Gaussian-KDE curve on a twin axis.
        data: optional dataframe-like the string channel is resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling routed per component with ``bar_``/``line_``
            prefixes (unprefixed kwargs are shared).

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if ``values`` is not a numeric 1-D sequence.

    Example:
        >>> bv.plot_hist1d(reaction_times, bin_width=25, density=True)
    """
    style = split_styles(
        overrides,
        components=("bar", "line"),
        defaults={
            "bar": {
                "color": "#0569E2",
                "linewidth": 0.75,
                "edgecolor": "#FFFFFF",
            },
            "line": {
                "color": "#011630",
                "linewidth": 3,
            },
        },
    )

    # make bins
    data_min = np.nanmin(values)
    data_max = np.nanmax(values)
    bin_edges = np.arange(data_min, data_max + bin_width, bin_width)
    counts, bin_edges = np.histogram(values, bins=bin_edges)

    _, ax = plot_bar(bin_edges[:-1], counts, width=bin_width, ax=ax, spec=spec, **style["bar"])

    if density:
        dx = overrides.get("density_step", bin_width)
        kernel = gaussian_kde(values)
        x = np.arange(data_min, data_max + dx, dx)
        pdf = kernel(x)

        ax_twin = ax.twinx()
        _, ax = plot_line(x, pdf, ax=ax_twin, width=bin_width, spec=spec, **style["line"])

    return ax
