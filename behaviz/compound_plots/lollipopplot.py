from typing import Optional
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_bar, plot_scatter
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

from behaviz.compound_plots.styling import split_styles

LOLLIPOP_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    y=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    title="Lollipop plot",
)


@plot_function(default_spec=LOLLIPOP_SPEC, data_args=("x", "y"))
def plot_lollipop(
    x: ArrayLike,
    y: ArrayLike,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    style = split_styles(
        overrides,
        ("bar", "scatter"),
        defaults={
            "bar": {"color": "#000000"},
            "scatter": {
                "s": 40,
                "color": "#FFFFFF",
                "edgecolor": "#000000",
            },
        },
    )

    _, ax = plot_bar(x, y, ax=ax, spec=spec, width=0.05, **style["bar"])
    _, ax = plot_scatter(x, y, ax=ax, spec=spec, **style["scatter"])

    return ax
