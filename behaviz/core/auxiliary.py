from typing import Optional, Sequence

from .plot_setup import plot_function
from .errors import data_error
from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR),
    y=AxisSpec(scale=ScaleType.LINEAR),
    show_legend=False,
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
    """Annotate a significance bracket with p-value stars between two x positions.

    Args:
        p_val: the p-value; converted to stars (**** < 0.0001 ... * < 0.05,
            "ns" otherwise).
        pos: the two x positions to bracket, (x1, x2).
        loc: y position of the bracket.
        ax: axes to draw the annotation on. Required — must be passed as a
            keyword (``ax=ax``) because of the decorator's argument handling.
        tail_height: height of the bracket tails as a proportion of ``loc``.
            Defaults to 0.05.
        **kwargs: styling forwarded to the active backend renderer.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if ``pos`` does not hold exactly two positions.

    Example:
        >>> bv.plot_pval(0.003, pos=(0, 1), loc=ymax * 1.05, ax=ax)
    """
    if not hasattr(pos, "__len__") or len(pos) != 2:
        raise data_error(
            "plot_pval",
            "`pos` must hold exactly two x positions, (x1, x2).",
            details={"pos": pos},
        )

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
