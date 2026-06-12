import numpy as np
from typing import Optional
from numpy.typing import ArrayLike

from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec
from behaviz.spec.plot_spec import PlotSpec
from behaviz.core.plot_setup import plot_function
from behaviz.core.channels import Channel
from behaviz.core.errors import data_error
from behaviz.core.core import plot_scatter, plot_line, plot_vertical
from behaviz.backends.renderer import BehavizAxes, BehavizFigure

from behaviz.composite_plots.styling import split_styles

PARALLEL_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(12, 8), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    y=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    title="Parallel plot",
)


@plot_function(
    default_spec=PARALLEL_SPEC,
    channels=[Channel("x"), Channel("ys", kind="vectors")],
)
def plot_parallel(
    x: ArrayLike,
    ys: ArrayLike,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """Parallel-coordinates plot: one line per observation across x positions.

    Args:
        x: the parallel axes' positions, shape (N,). Array-like, or a column
            name when ``data=`` is given.
        ys: the observations — a 2-D array of shape (M, N) or a sequence of
            M rows, each holding one value per ``x`` position.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling routed per component with ``line_``/``scatter_``
            prefixes (unprefixed kwargs are shared).

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if the rows of ``ys`` do not all have one value per
            ``x`` position.

    Example:
        >>> bv.plot_parallel([0, 1, 2], subject_scores)  # scores: (n_subjects, 3)
    """
    row_lengths = {len(yi) for yi in ys}
    if row_lengths != {len(x)}:
        raise data_error(
            "plot_parallel",
            "every row of `ys` must have one value per `x` position.",
            details={"x": x, "ys": ys},
            hint=f"expected rows of length {len(x)}, got lengths {sorted(row_lengths)}.",
        )
    ys = np.vstack(ys)

    style = split_styles(
        overrides,
        ("line", "scatter"),
        defaults={
            "line": {"color": "#000000"},
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
