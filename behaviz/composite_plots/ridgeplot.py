import numpy as np
from typing import Optional, Literal
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_line, plot_fill_between, Channel
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec
from behaviz.manipulations import VisualManipulator

from behaviz.composite_plots.styling import split_styles


RIDGE_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(label="X", unit="", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Counts", unit="", scale=ScaleType.LINEAR),
    title="",
)


def _find_max(ys: dict[ArrayLike] | list[ArrayLike]) -> float:

    if isinstance(ys, dict):
        max_value = max(max(lst) for lst in ys.values())
    elif isinstance(ys, list):
        max_value = max(max(lst) for lst in ys)
    elif isinstance(ys, np.ndarray):
        max_value = np.max(ys)

    return max_value


@plot_function(
    default_spec=RIDGE_SPEC,
    channels=[
        Channel("x", required=True, kind="vector"),
        Channel("ys", required=True, kind="vectors", element_length_as="x", labels_to="y"),
    ],
    grouping="overlay",
)
def plot_ridge(
    x: ArrayLike,
    ys: dict[ArrayLike] | list[ArrayLike],
    normalize: Literal["none", "each", "all"] = "none",
    normalize_method: Literal["constant", "minmax", "baseline", "zscore"] = "constant",
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """Plot a ridge plot from a collection of one-dimensional signals.

    Args:
        x (ArrayLike):
            Shared x-axis coordinates for all signals.

        ys (dict[ArrayLike] | list[ArrayLike]):
            Collection of y-values to plot. Each element represents one ridge.
            If a dictionary is provided, only its values are used for plotting,
            and the insertion order determines the stacking order.

        normalize (Literal["none", "each", "all"], optional):
            Controls amplitude normalization.

            - ``"none"``: Plot the original values.
            - ``"each"``: Normalize each signal independently.
            - ``"all"``: Normalize all signals using the global maximum value.

            Defaults to ``"none"``.

        normalize_method (Literal["constant", "minmax", "baseline", "zscore"], optional):
            Method used when normalizing the data. When
            ``normalize="all"``, only ``"constant"`` is supported.
            Defaults to ``"constant"``.

        ax (Optional[BehavizAxes], optional):
            Existing axes to draw on. If ``None``, a new figure and axes are
            created. Defaults to ``None``.

        spec (Optional[PlotSpec], optional):
            Plot specification used to configure figure and axes properties.
            Defaults to ``None``.

        **overrides:
            Additional keyword arguments used to customize plotting styles.
            Style arguments are split into two groups:

            - ``line_*``: Passed to the line plot.
            - ``fill_*``: Passed to the filled region.

            By default:

            - ``linewidth=1`` for lines.
            - ``alpha=0.5`` for fills.

    Returns:
        BehavizAxes | BehavizFigure:
            The axes containing the ridge plot. If a new figure is created,
            the associated figure is created internally by the plotting
            utilities.

    Raises:
        ValueError:
            If an invalid normalization mode is specified.

        ValueError:
            If ``normalize="all"`` is used with a normalization method other
            than ``"constant"``.
    """
    style = split_styles(
        overrides,
        ("line", "fill"),
        defaults={
            "line": {
                "linewidth": 1,
            },
            "fill": {
                "alpha": 0.5,
            },
        },
    )
    vm = VisualManipulator()
    y_pos = np.array([i for i in range(len(ys))])

    for i, yi in enumerate(ys[::-1]):
        pos = y_pos[::-1][i]
        base_yi = np.ones_like(yi) * pos

        if normalize == "each":
            mnp = vm.normalise(x, yi, kind=normalize_method, normalise_by=np.max(yi), baseline_idx=0)
            x_plot = mnp.x
            y_plot = mnp.y + pos
        elif normalize == "all":
            if normalize_method != "constant":
                raise ValueError("Only constant value normalization can be used with normalize=all")
            mnp = vm.normalise(x, yi, kind=normalize_method, normalise_by=_find_max(ys))
            x_plot = mnp.x
            y_plot = mnp.y + pos
        elif normalize == "none":
            x_plot = x
            y_plot = yi + pos
        else:
            raise ValueError(f"{normalize} is an invalid value for normalization, try 'all', 'each' or 'none'")

        _, ax = plot_line(x_plot, y_plot, spec=spec, ax=ax, **style["line"])
        _, ax = plot_fill_between(x_plot, y_plot, base_yi, spec=spec, ax=ax, **style["fill"])

    return ax
