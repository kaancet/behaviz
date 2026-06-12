import numpy as np
from typing import Optional
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_errorbar, plot_bar, plot_scatter, Channel
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec

from behaviz.manipulations.manipulator import VisualManipulator
from behaviz.composite_plots.styling import split_styles

BOXPLOT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    y=AxisSpec(scale=ScaleType.LINEAR, spines=["bottom", "left"]),
    title="Boxplot plot",
)


@plot_function(
    default_spec=BOXPLOT_SPEC,
    channels=[Channel("x"), Channel("ys", kind="vectors", same_length_as="x")],
)
def plot_boxplot(
    x: ArrayLike,
    ys: list[ArrayLike],
    with_data: bool = False,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """Box-and-whisker plot: median, IQR box and min/max whiskers per group.

    Args:
        x: box positions, shape (N,). Array-like, or a column name when
            ``data=`` is given.
        ys: the distributions — a sequence of N 1-D arrays (ragged lengths
            allowed), or a 2-D array read as one distribution per row.
        with_data: also scatter the raw (jittered) data points.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling routed per component with ``bar_``/``scatter_``/
            ``errorbar_`` prefixes (unprefixed kwargs are shared). ``seed``
            controls the jitter RNG.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if ``len(ys) != len(x)`` or the inputs are not
            numeric sequences.

    Example:
        >>> bv.plot_boxplot([0, 1], [ctrl, treat], with_data=True)
    """
    style = split_styles(
        overrides,
        ("bar", "scatter", "errorbar"),
        defaults={
            "bar": {
                "edgecolor": "#000000",
                "facecolor": "#FFFFFF",
                "linewidth": 1,
                "width": 0.7,
            },
            "scatter": {
                "s": 30,
                "edgecolor": "#FFFFFF",
                "color": "#000000",
            },
            "errorbar": {
                "color": "#000000",
                "capsize": 5,
                "ecolor": "#000000",
                "linewidth": 0,
                "elinewidth": 0.8,
            },
        },
    )

    rng_seed = overrides.pop("seed", 42)
    vm = VisualManipulator(seed=rng_seed)

    if with_data:
        for i in range(len(x)):
            yi = ys[i]
            xi = np.ones_like(yi) * x[i]
            mnp = vm.jitter(xi, yi, kind="uniform", axis="x", strength=0.05)

            _, ax = plot_scatter(mnp.x, mnp.y, ax=ax, spec=spec, **style["scatter"])

    # plot the errorbar with min and max extrema
    mins = np.array([np.nanmin(yi) for yi in ys])
    maxs = np.array([np.nanmax(yi) for yi in ys])
    medians = np.array([np.nanmedian(yi) for yi in ys])

    err = np.vstack(((medians - mins).reshape(1, -1), (maxs - medians).reshape(1, -1)))

    _, ax = plot_errorbar(x, medians, err, ax=ax, spec=spec, **style["errorbar"])

    # plot the bars with IQR-median-IQR
    t_iqr = np.array([np.nanquantile(yi, q=0.75) for yi in ys])
    l_iqr = np.array([np.nanquantile(yi, q=0.25) for yi in ys])

    _, ax = plot_bar(x, l_iqr - medians, bottom=medians, ax=ax, spec=spec, **style["bar"])
    _, ax = plot_bar(x, t_iqr - medians, bottom=medians, ax=ax, spec=spec, **style["bar"])

    return ax
