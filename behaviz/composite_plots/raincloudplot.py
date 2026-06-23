import warnings
import numpy as np
from typing import Optional, Literal
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_violin, plot_scatter, Channel
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec
from behaviz.backends.renderer_manager import get_renderer

from behaviz.manipulations.manipulator import VisualManipulator
from behaviz.composite_plots.styling import split_styles

RAINPLOT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10, 10), dpi=300),
    x=AxisSpec(scale=ScaleType.LINEAR),
    y=AxisSpec(scale=ScaleType.LINEAR),
    title="Raincloud plot",
)


@plot_function(
    default_spec=RAINPLOT_SPEC,
    channels=[Channel("x"), Channel("ys", kind="vectors", same_length_as="x")],
    grouping="dodge",
)
def plot_raincloud(
    x: ArrayLike,
    ys: list[ArrayLike],
    ax: Optional[BehavizAxes] = None,
    bin_width: int = 25,  # ms
    cloud_side: Literal["left", "right"] = "left",
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> BehavizAxes | BehavizFigure:
    """Raincloud plot: a half-violin "cloud" plus beeswarm "rain" per group.

    Args:
        x: group positions, shape (N,). Array-like, or a column name when
            ``data=`` is given.
        ys: the distributions — a sequence of N 1-D arrays (ragged lengths
            allowed), or a 2-D array read as one distribution per row.
        bin_width: beeswarm bin width in data units (controls dot stacking).
        cloud_side: which side the half-violin faces ("left" or "right");
            the rain falls on the other side.
        data: optional dataframe-like the string channels are resolved against.
        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling routed per component with ``violin_``/``scatter_``
            prefixes (unprefixed kwargs are shared). ``seed``, ``width`` and
            ``width_margin`` tune the jitter geometry.

    Returns:
        (fig, ax): backend figure and axes handles.

    Raises:
        BehavizDataError: if ``len(ys) != len(x)`` or the inputs are not
            numeric sequences.

    Example:
        >>> bv.plot_raincloud([0, 1, 2], [rt_a, rt_b, rt_c], cloud_side="right")
    """
    style = split_styles(overrides, components=("violin", "scatter"))

    rain_side = "left" if cloud_side == "right" else "right"
    _xspace = 1  # x[1] - x[0]

    x_wm = overrides.pop("width_margin", _xspace / 5)  # arbitrary
    width = overrides.pop("width", (_xspace - 2 * x_wm) / 2)

    rng_seed = overrides.pop("seed", 42)
    vm = VisualManipulator(seed=rng_seed)

    _, ax, vp = plot_violin(x, ys, ax=ax, spec=spec, **style["violin"])

    fold_violins(vp, side=cloud_side)

    # plot the the dots
    for xi, yi in zip(x, ys):
        mnp = vm.jitter(xi, yi, kind="beeswarm", axis="x", bin_width=bin_width, side=rain_side, width=width)

        _, ax = plot_scatter(mnp.x, mnp.y, ax=ax, spec=spec, **style["scatter"])

    return ax


def fold_violins(vp, side: str = "left") -> None:
    """Clip each violin in ``vp["bodies"]`` to one side of its centre, in place.

    Parameters
    ----------
    vp : dict | None
        The third return value of :func:`plot_violin` — ``{"bodies": [...]}``.
        ``None`` or a body-less value is a no-op (e.g. backends that don't expose
        violin artists).
    side : {"left", "right"}
        Which half to keep.
    """
    if not isinstance(vp, dict):
        return
    bodies = vp.get("bodies") or []
    if not bodies:
        return

    name = get_renderer().name
    folder = _FOLDERS.get(name)
    if folder is None:
        warnings.warn(
            f"fold_violins: half-violins are not supported on the '{name}' backend; drawing full violins instead.",
            stacklevel=2,
        )
        return

    for body in bodies:
        folder(body, side)


def _half(xs: np.ndarray, centre: float, side: str) -> np.ndarray:
    """Keep only the values on ``side`` of ``centre`` by folding the rest in."""
    return np.minimum(xs, centre) if side == "left" else np.maximum(xs, centre)


def _fold_mpl(body, side: str) -> None:
    """matplotlib / seaborn: clip the PolyCollection's path vertices."""
    path = body.get_paths()[0]
    vertices = path.vertices
    centre = float(np.mean(vertices[:, 0]))
    vertices[:, 0] = _half(vertices[:, 0], centre, side)


def _fold_bokeh(body, side: str) -> None:
    """bokeh: clip the patch glyph's x column in its data source."""
    src = body.data_source
    xkey = body.glyph.x if isinstance(body.glyph.x, str) else "x"
    data = dict(src.data)
    xs = np.asarray(data[xkey], dtype=float)
    centre = float(np.mean(xs))
    data[xkey] = _half(xs, centre, side)
    src.data = data  # reassign so bokeh picks up the change


_FOLDERS = {
    "matplotlib": _fold_mpl,
    "seaborn": _fold_mpl,
    "bokeh": _fold_bokeh,
}
