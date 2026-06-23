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
def plot_text(
    x: float,
    y: float,
    s: str,
    ax: BehavizAxes = None,
    size: float = 12,
    rotation: float = 0,
    ha: str = "center",
    va: str = "center",
    color: str = "#000000",
    coords: str = "data",
    spec: Optional[PlotSpec] = None,
    **kwargs,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Place text at ``(x, y)`` on any backend.

    Args:
        x, y: position. In data units by default; in 0..1 axes fractions when
            ``coords="axes"`` (e.g. (0.5, 0.95) = top-centre).
        s: the text.
        ax: axes to annotate (created if None).
        size: font size.
        rotation: orientation in degrees, counter-clockwise.
        ha, va: horizontal / vertical anchor ("center"/"left"/"right",
            "center"/"top"/"bottom").
        color: text color.
        **kwargs: extra styling forwarded to the backend.
        coords: "data" (default) or "axes" (0..1 fraction). ``coords="axes"`` is
            matplotlib/seaborn only.

    Returns:
        (fig, ax): backend figure and axes handles.

    Example:
        >>> bv.plot_text(0.5, 0.95, "title", ax=ax, coords="axes")
    """
    r = get_renderer()
    extra = {}
    if coords == "axes":
        if r.name == "bokeh":
            raise data_error(
                "plot_text",
                "coords='axes' (axes-fraction) is not supported on the bokeh backend.",
                hint="use coords='data', or switch to matplotlib/seaborn.",
            )
        extra["transform"] = ax.transAxes  # matplotlib/seaborn axes-fraction transform
    elif coords != "data":
        raise data_error("plot_text", f"coords must be 'data' or 'axes', got {coords!r}.")
    r.text(ax=ax, x=x, y=y, s=s, fontsize=size, rotation=rotation, ha=ha, va=va, color=color, **extra, **kwargs)
    return ax


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
