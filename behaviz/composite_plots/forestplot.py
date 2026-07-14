import numpy as np
from typing import Optional
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_errorbar, plot_hbar, plot_scatter, Channel
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

from behaviz.manipulations.manipulator import VisualManipulator
from behaviz.composite_plots.styling import split_styles

FORESTPLOT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    y=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    title="Forest plot",
)


@plot_function(
    default_spec=FORESTPLOT_SPEC,
    channels=[Channel("y"), Channel("xs", kind="vectors", same_length_as="x")],
)
def plot_forestplot(
    y: ArrayLike,
    ys: list[ArrayLike],
    with_data: bool = False,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    pass
