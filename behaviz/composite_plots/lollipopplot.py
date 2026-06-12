from typing import Optional
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_bar, plot_scatter, Channel
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

from behaviz.composite_plots.styling import split_styles

LOLLIPOP_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    y=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    title="Lollipop plot",
)


@plot_function(
    default_spec=LOLLIPOP_SPEC,
    channels=[Channel("x"), Channel("y", same_length_as="x")],
)
def plot_lollipop(
    x: ArrayLike,
    y: ArrayLike,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """Lollipop plot: a thin stem with a dot at each value.

    Args:
        x: stem positions, shape (N,). Array-like, or a column name when
            ``data=`` is given.
        y: stem heights, shape (N,). Same accepted types as ``x``.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling routed per component with ``bar_``/``scatter_``
            prefixes (unprefixed kwargs are shared).

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if shapes or types are inconsistent.

    Example:
        >>> bv.plot_lollipop(range(5), counts, scatter_s=60)
    """
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
