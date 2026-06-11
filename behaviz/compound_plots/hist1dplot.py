import numpy as np
from typing import Optional
from numpy.typing import ArrayLike
from scipy.stats import gaussian_kde

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_bar, plot_line
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

from behaviz.compound_plots.styling import split_styles


HIST1D_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(label="X", unit="", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Counts", unit="", scale=ScaleType.LINEAR),
    title="Distribution plot",
)


@plot_function(default_spec=HIST1D_SPEC, data_args=("x", "y"))
def plot_hist1d(
    data: ArrayLike,
    bin_width: float,
    density: bool = False,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
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
    data_min = np.nanmin(data)
    data_max = np.nanmax(data)
    bin_edges = np.arange(data_min, data_max + bin_width, bin_width)
    counts, bin_edges = np.histogram(data, bins=bin_edges)

    _, ax = plot_bar(bin_edges[:-1], counts, width=bin_width, ax=ax, spec=spec, **style["bar"])

    if density:
        dx = overrides.get("density_step", bin_width)
        kernel = gaussian_kde(data)
        x = np.arange(data_min, data_max + dx, dx)
        pdf = kernel(x)

        ax_twin = ax.twinx()
        _, ax = plot_line(x, pdf, ax=ax_twin, width=bin_width, spec=spec, **style["line"])

    return ax
