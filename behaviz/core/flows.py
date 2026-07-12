"""Sankey & alluvial (flow) plots — first-class behaviz plot types.

The backend-agnostic *layout* (ribbon polygons + node rectangles) is computed
here from a tidy flow table; each backend's renderer just draws the result. So
both are normal ``ALL_PLOTS`` plots: they draw on the passed axes, honour the
spec, and return ``(fig, ax)``.

Tidy flow table (one row per flow):
    sankey   — columns: source, target, value
    alluvial — same, plus a ``stage`` column ordering the transitions

The ribbon geometry is a cubic-bezier band between stacked source/target nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from .plot_setup import plot_function
from .data_source import resolve
from .grouping import _ordered_unique
from .palette import resolve_palette
from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from ..spec import PlotSpec, AxisSpec

# Flow plots fill the whole axes; hide grid/spines (the draw methods also hide
# the ticks/axis themselves).
_FLOW_SPEC = PlotSpec(x=AxisSpec(grid=False, spines=[]), y=AxisSpec(grid=False, spines=[]))


@dataclass
class Ribbon:
    xs: np.ndarray
    ys: np.ndarray
    color: str
    source: Any
    target: Any
    value: float


@dataclass
class Node:
    x0: float
    x1: float
    y0: float
    y1: float
    color: str
    label: str
    value: float
    first: bool  # left-most layer → label on the left
    last: bool  # right-most layer → label on the right


@dataclass
class FlowLayout:
    ribbons: list
    nodes: list


def resolve_flows(data, source, target, value, stage=None) -> list[list[tuple]]:
    """Tidy flow table → per-transition flow lists ``[[(src, tgt, val), ...], ...]``."""
    src = np.asarray(resolve(source, data))
    tgt = np.asarray(resolve(target, data))
    val = np.asarray(resolve(value, data), dtype=float)
    if not (len(src) == len(tgt) == len(val)):
        raise ValueError("plot_sankey/alluvial: source, target and value must be the same length.")
    if stage is None:
        return [list(zip(src.tolist(), tgt.tolist(), val.tolist()))]
    st = np.asarray(resolve(stage, data))
    flows = []
    for s in _ordered_unique(st, None):
        m = st == s
        flows.append(list(zip(src[m].tolist(), tgt[m].tolist(), val[m].tolist())))
    return flows


def _layer_nodes(flows_by_layer: list[list[tuple]]) -> list[list]:
    """Ordered node names per layer: every node that receives from the previous
    transition or emits into the next one (a node may do only one of the two)."""
    n_layers = len(flows_by_layer) + 1
    layers = []
    for i in range(n_layers):
        names: list = []
        if i > 0:
            names += [f[1] for f in flows_by_layer[i - 1]]  # arrives here
        if i < n_layers - 1:
            names += [f[0] for f in flows_by_layer[i]]  # leaves from here
        layers.append(_ordered_unique(np.array(names, dtype=object), None))
    return layers


def _node_heights(flows_by_layer, layer_nodes) -> list[dict]:
    """Flow-unit height of each node: ``max(incoming, outgoing)``.

    Sizing on incoming alone under-sizes any node that emits more than it
    receives, so its outgoing ribbons overflow the node rectangle.
    """
    n_layers = len(layer_nodes)
    heights = []
    for i, nodes in enumerate(layer_nodes):
        h = {}
        for n in nodes:
            incoming = sum(f[2] for f in flows_by_layer[i - 1] if f[1] == n) if i > 0 else 0
            outgoing = sum(f[2] for f in flows_by_layer[i] if f[0] == n) if i < n_layers - 1 else 0
            h[n] = max(incoming, outgoing)
        heights.append(h)
    return heights


def compute_layout(
    flows_by_layer,
    *,
    palette=None,
    height: float = 1.0,
    node_width: float = 0.12,
    gap_frac: float = 0.02,
    n_points: int = 60,
) -> FlowLayout:
    """Turn per-transition flows into drawable ribbons + node rectangles."""
    layer_nodes = _layer_nodes(flows_by_layer)
    n_layers = len(layer_nodes)
    node_h = _node_heights(flows_by_layer, layer_nodes)

    # colour by node identity (shared palette across layers)
    cats: list = []
    seen: set = set()
    for nodes in layer_nodes:
        for c in nodes:
            if c not in seen:
                seen.add(c)
                cats.append(c)
    color_map = resolve_palette(cats, palette)

    totals = [sum(node_h[i].get(c, 0) for c in layer_nodes[i]) for i in range(n_layers)]
    max_total = max(totals) if totals else 0
    max_active = max((sum(1 for c in layer_nodes[i] if node_h[i].get(c, 0) > 0) for i in range(n_layers)), default=1)
    gap = height * gap_frac
    avail = height - gap * (max_active - 1 if max_active > 1 else 0)
    scale = avail / max_total if max_total > 0 else 1.0

    # stack nodes within each layer
    node_pos: list[dict] = []
    for i in range(n_layers):
        pos: dict = {}
        y = 0.0
        for c in layer_nodes[i]:
            hh = node_h[i].get(c, 0) * scale
            pos[c] = (y, y + hh)
            if hh > 0:
                y += hh + gap
        node_pos.append(pos)

    # bezier ribbons between consecutive layers, stacked in each node
    t = np.linspace(0, 1, n_points)
    ribbons: list[Ribbon] = []
    for li, flows in enumerate(flows_by_layer):
        xs0 = li + node_width / 2
        xs1 = (li + 1) - node_width / 2
        s_cur = {c: node_pos[li][c][0] for c in layer_nodes[li]}
        t_cur = {c: node_pos[li + 1][c][0] for c in layer_nodes[li + 1]}
        cx0 = xs0 + (xs1 - xs0) / 3
        cx1 = xs0 + 2 * (xs1 - xs0) / 3
        xb = (1 - t) ** 3 * xs0 + 3 * (1 - t) ** 2 * t * cx0 + 3 * (1 - t) * t**2 * cx1 + t**3 * xs1
        for fr, to, v in flows:
            if v == 0:
                continue
            sv = v * scale
            ysb, yst = s_cur[fr], s_cur[fr] + sv
            s_cur[fr] = yst
            ytb, ytt = t_cur[to], t_cur[to] + sv
            t_cur[to] = ytt
            ytop = (1 - t) ** 3 * yst + 3 * (1 - t) ** 2 * t * yst + 3 * (1 - t) * t**2 * ytt + t**3 * ytt
            ybot = (1 - t) ** 3 * ysb + 3 * (1 - t) ** 2 * t * ysb + 3 * (1 - t) * t**2 * ytb + t**3 * ytb
            ribbons.append(
                Ribbon(np.concatenate([xb, xb[::-1]]), np.concatenate([ytop, ybot[::-1]]), color_map[fr], fr, to, v)
            )

    nodes: list[Node] = []
    for i in range(n_layers):
        for c in layer_nodes[i]:
            y0, y1 = node_pos[i][c]
            if y1 > y0:
                nodes.append(
                    Node(
                        i - node_width / 2,
                        i + node_width / 2,
                        y0,
                        y1,
                        color_map[c],
                        str(c),
                        node_h[i].get(c, 0),
                        first=(i == 0),
                        last=(i == n_layers - 1),
                    )
                )
    return FlowLayout(ribbons, nodes)


@plot_function(default_spec=_FLOW_SPEC)
def plot_sankey(
    data,
    source: str = "source",
    target: str = "target",
    value: str = "value",
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    palette: Any = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Sankey diagram from a tidy flow table (columns ``source``, ``target``, ``value``).

    Args:
        data: Data to be used for the alluvial plot, preferably a DataFrame
        source: upper curve, shape (N,) (or a scalar for a constant level).
        target: lower curve, shape (N,); a scalar (default 0) fills down to a
            constant.
        value:

        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer
            (e.g. ``color``, ``alpha``).

    Returns:
        (fig, ax): backend figure and axes handles.

    Example:
        >>> df = pd.DataFrame({"source": ["A", "A", "B"], "target": ["X", "Y", "Y"], "value": [3, 2, 4]})
        >>> bv.plot_sankey(df)
    """
    layout = compute_layout(resolve_flows(data, source, target, value), palette=palette)
    get_renderer().sankey(ax, layout, **overrides)
    return ax


@plot_function(default_spec=_FLOW_SPEC)
def plot_alluvial(
    data,
    source: str = "source",
    target: str = "target",
    value: str = "value",
    stage: str = "stage",
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    palette: Any = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """Multi-stage sankey (alluvial) from a tidy flow table with a ``stage`` column
    ordering the transitions.

    Args:
        data: Data to be used for the alluvial plot, preferably a DataFrame
        source: upper curve, shape (N,) (or a scalar for a constant level).
        target: lower curve, shape (N,); a scalar (default 0) fills down to a
            constant.

        ax: axes to plot on (created if None).
        spec: plot specification.
        **overrides: styling forwarded to the active backend renderer
            (e.g. ``color``, ``alpha``).

    Returns:
        (fig, ax): backend figure and axes handles.

    Example:
        >>> bv.plot_alluvial(df, stage="stage")   # df has source/target/value/stage
    """
    layout = compute_layout(resolve_flows(data, source, target, value, stage), palette=palette)
    get_renderer().alluvial(ax, layout, **overrides)
    return ax
