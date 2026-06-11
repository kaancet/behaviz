from typing import Optional

from .plot_setup import plot_function
from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300),
    x=AxisSpec(label="X", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Y", scale=ScaleType.LINEAR),
    show_legend=True,
)


@plot_function(default_spec=DEFAULT_SPEC)
def plot_pval(
    p_val: float,
    pos: list[float, float],
    loc: Optional[float],
    ax: BehavizAxes,  # auxiliary plot needs an axis
    tail_height: Optional[float] = 0.05,
    **kwargs,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Annotates the p-val between two locations

    Args:
        ax (BehavizAxes): axes object to draw the annotation on
        p_val (float): the text to be written
        pos (list[float,float]): the position of the stars in the independent axis
        loc (float): location of the stars in the dependent axis
        tail_height (float, optional): height of annotation line tails as a proprtion of loc. Defaults to 0.05.

    Returns:
        plt.Axes: Axes object the stars were plotted to
    """

    x1, x2 = pos
    h = loc * tail_height

    stars = "ns"
    if p_val < 0.0001:
        stars = "****"
    elif 0.0001 <= p_val < 0.001:
        stars = "***"
    elif 0.001 <= p_val < 0.01:
        stars = "**"
    elif 0.01 <= p_val < 0.05:
        stars = "*"

    r = get_renderer()

    # plot the line between two
    r.line(ax=ax, x=[x1, x1, x2, x2], y=[loc, loc + h, loc + h, loc], color="#000000", **kwargs)
    # p-val string
    r.text(ax=ax, x=(x1 + x2) * 0.5, y=loc + h, s=stars, ha="center", color="#000000", **kwargs)

    return ax
