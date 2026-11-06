"""bokeh ``"bilog"`` axis.

Bokeh has no custom scales, so the axis stays linear: the glyph coordinates are
replaced by ``bilog(value)`` and the ticks are placed at the transformed positions
with the original numbers as labels. The untouched values live in a ``<col>__raw``
column, so every pass recomputes from it (idempotent: ``apply_axis_spec`` runs
after each plot call and on ``bv.set_xaxis``) and a switch back to another scale
restores the data exactly.

Two phases, called from ``BokehRenderer.apply_axis_spec``:
``sync_bilog_data`` (before limits/ticks) and ``apply_bilog_axes`` (after them).
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from bokeh.models import (
    BasicTickFormatter,
    BasicTicker,
    ColumnDataSource,
    DataRange1d,
    FixedTicker,
    HoverTool,
    LogTickFormatter,
    LogTicker,
    Range1d,
)

from behaviz.core.scales import BILOG_C, bilog, bilog_label, bilog_ticks, hidden_labels

_TAG = "behaviz-bilog"  # set on an axis we have decorated, so a switch back can undo it
_RAW = "__raw"
_COORDS = {
    "x": ("x", "x0", "x1", "x2", "left", "right"),
    "y": ("y", "y0", "y1", "y2", "top", "bottom"),
}


def _c(asp) -> float:
    return asp.bilog_c if asp.bilog_c is not None else BILOG_C


def _field(prop):
    """Column name a glyph property is bound to, else None."""
    if isinstance(prop, str):
        return prop
    return prop.get("field") if isinstance(prop, dict) else None


def _scan(fig, dim: str):
    """``([(data_source, column)], skipped)`` for the ``dim`` coordinates of every glyph.

    ``skipped`` names glyphs whose position is a plain non-zero number (image,
    wedge, a scalar vspan...), which can't be transformed in the data.
    """
    cols, skipped, seen = [], set(), set()
    for r in fig.renderers:
        ds, glyph = getattr(r, "data_source", None), getattr(r, "glyph", None)
        if not isinstance(ds, ColumnDataSource) or glyph is None:
            continue
        for name in _COORDS[dim]:
            prop = getattr(glyph, name, None)
            f = _field(prop)
            if f is None:
                if isinstance(prop, (int, float)) and not isinstance(prop, bool) and prop != 0:
                    skipped.add(type(glyph).__name__)  # 0 maps to 0, so it is already right
            elif f in ds.data and (id(ds), f) not in seen:
                seen.add((id(ds), f))
                cols.append((ds, f))
    return cols, skipped


def _retarget_hover(fig, fields, to_raw: bool) -> None:
    """Point ``@{col}`` tooltips at the raw column (or back), so hover shows real values."""
    for tool in fig.tools:
        if not isinstance(tool, HoverTool) or not tool.tooltips:
            continue
        for f in fields:
            old, new = "@{%s}" % f, "@{%s%s}" % (f, _RAW)
            if not to_raw:
                old, new = new, old
            tt = tool.tooltips
            tool.tooltips = tt.replace(old, new) if isinstance(tt, str) else [(k, v.replace(old, new)) for k, v in tt]


def sync_bilog_data(fig, spec) -> None:
    """Phase 1: glyph data = ``bilog(raw)`` on bilog axes, raw everywhere else."""
    for asp, dim, axis in ((spec.x, "x", fig.xaxis[0]), (spec.y, "y", fig.yaxis[0])):
        c = _c(asp) if asp.scale == "bilog" else None
        cols, skipped = _scan(fig, dim)
        touched = []
        for ds, f in cols:
            raw = ds.data.get(f + _RAW)
            if raw is None:
                if c is None:
                    continue
                cur = np.asarray(ds.data[f])
                if cur.dtype.kind not in "fiu":  # dates, strings...: leave alone
                    continue
                raw = cur.astype(float)
                ds.data[f + _RAW] = raw
            ds.data[f] = raw if c is None else bilog(raw, c)
            touched.append(f)
            if c is None:
                del ds.data[f + _RAW]
        _retarget_hover(fig, touched, to_raw=c is not None)

        if c is None and _TAG in axis.tags:  # we decorated it earlier: undo
            axis.tags = [t for t in axis.tags if t != _TAG]
            axis.major_label_overrides = {}
            log = asp.scale == "log"
            axis.ticker = LogTicker() if log else BasicTicker()
            axis.formatter = LogTickFormatter() if log else BasicTickFormatter()
            if not asp.lim:
                setattr(fig, f"{dim}_range", DataRange1d())
        if c is not None and skipped:
            warnings.warn(
                f"bilog {dim}-axis: {', '.join(sorted(skipped))} positions are plain numbers and are "
                "drawn untransformed on bokeh.",
                stacklevel=2,
            )


def _raw_range(fig, dim: str):
    vals = []
    for ds, f in _scan(fig, dim)[0]:
        arr = np.asarray(ds.data.get(f + _RAW, ds.data[f]))
        if arr.dtype.kind in "fiu":
            arr = arr[np.isfinite(arr)]
            if arr.size:
                vals.append(arr)
    if not vals:
        return None
    pooled = np.concatenate(vals)
    return float(pooled.min()), float(pooled.max())


def _even_ticks(lo: float, hi: float, n: int = 6) -> list:
    """1-2-5 ticks in data units, for limits that hold no decade (linear zone)."""
    if not hi > lo:
        return [lo]
    step = (hi - lo) / n
    mag = 10.0 ** math.floor(math.log10(step))
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= step)
    start = math.ceil(lo / step) * step
    return [round(start + i * step, 12) for i in range(int((hi - start) // step) + 1)]


def apply_bilog_axes(fig, spec) -> None:
    """Phase 2: limits, tick positions and tick labels for each bilog axis."""
    for asp, dim, axis in ((spec.x, "x", fig.xaxis[0]), (spec.y, "y", fig.yaxis[0])):
        if asp.scale != "bilog":
            continue
        c = _c(asp)
        if _TAG not in axis.tags:
            axis.tags = [*axis.tags, _TAG]
        if asp.lim:
            setattr(fig, f"{dim}_range", Range1d(*(float(bilog(v, c)) for v in asp.lim)))
        lim = asp.lim or _raw_range(fig, dim)
        if lim is None:
            continue
        lo, hi = sorted(lim)

        explicit = asp.ticks is not None
        if explicit:
            if all(isinstance(t, str) for t in asp.ticks):  # categorical labels: not ours
                continue
            majors, minors = [float(t) for t in asp.ticks], []
        else:
            majors, minors = bilog_ticks(lo, hi, c) or (_even_ticks(lo, hi), [])
        pos = [float(p) for p in bilog(majors, c)]

        # Labels that would overprint (near 0) are blanked; explicit ticks are the user's call.
        hidden = set()
        if not explicit:
            length = (fig.width if dim == "x" else fig.height) or 600
            slot_px = asp.fontsize * 4 / 3 * (3 if dim == "x" else 2)
            span = abs(float(bilog(hi, c)) - float(bilog(lo, c)))
            hidden = hidden_labels(majors, pos, span, 0.85 * length / slot_px)

        def label(v):
            if v in hidden:
                return ""
            try:
                return asp.tick_fmt % v if asp.tick_fmt else bilog_label(v)
            except (TypeError, ValueError):  # not a printf format
                return bilog_label(v)

        axis.ticker = FixedTicker(ticks=pos, minor_ticks=[float(p) for p in bilog(minors, c)])
        axis.major_label_overrides = {p: label(v) for p, v in zip(pos, majors)}
