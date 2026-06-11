import numpy as np
from typing import Optional
from numpy.typing import ArrayLike

from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec
from behaviz.spec.plot_spec import PlotSpec
from behaviz.core.plot_setup import plot_function
from behaviz.core.core import plot_scatter, plot_line, plot_vertical
from behaviz.backends.renderer import BehavizAxes, BehavizFigure

from behaviz.compound_plots.styling import split_styles

PARALLEL_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(12, 8), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    y=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    title="Parallel plot",
)


@plot_function(default_spec=PARALLEL_SPEC, data_args=("x", "y"))
def plot_parallel(
    x: ArrayLike,
    ys: ArrayLike,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """_summary_

    Args:
        x (ArrayLike): One dimensional array with shape N
        ys (ArrayLike): Two dimensional array with shape (M,N) where M are observations for each x-axis value
        ax (Optional[BehavizAxes], optional): _description_. Defaults to None.
        spec (Optional[PlotSpec], optional): _description_. Defaults to None.

    Returns:
        BehavizAxes | BehavizFigure: _description_
    """

    style = split_styles(
        overrides,
        ("bar", "dot"),
        defaults={
            "bar": {"color": "#000000"},
            "scatter": {
                "s": 40,
                "color": "#FFFFFF",
                "edgecolor": "#000000",
            },
        },
    )

    # plot the lines
    for yi in ys:
        _, ax = plot_line(x, yi, ax=ax, spec=spec, **style["line"])

    # plot the the dots

    for i, xi in enumerate(x):
        yi = ys[:, i]
        xi = np.asarray([xi] * len(yi))
        _, ax = plot_scatter(xi, yi, ax=ax, spec=spec, **style["scatter"])
        _, ax = plot_vertical(xi, ax=ax, spec=spec, color="#000000", linewidth=0.3, alpha=0.9)

    return ax
