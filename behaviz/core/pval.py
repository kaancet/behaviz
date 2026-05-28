import matplotlib.pyplot as plt

def pval_plotter(
    ax: plt.Axes,
    p_val: float,
    pos: list[float, float],
    loc: float,
    tail_height: float = 0.05,
    **kwargs,
) -> plt.Axes:
    """Annotates the p-val between two locations

    Args:
        ax (plt.Axes): axes object to draw the annotation on
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
    if stars != "ns":
        ax.plot(
            [x1, x1, x2, x2],
            [loc, loc + h, loc + h, loc],
            lw=1,
            c=kwargs.get("color", "k"),
        )
        ax.text(
            (x1 + x2) * 0.5,
            loc + h,
            stars,
            ha="center",
            va="center",
            color=kwargs.get("color", "k"),
        )
    return ax