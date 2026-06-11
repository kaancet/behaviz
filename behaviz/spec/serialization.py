from __future__ import annotations

import warnings
from dataclasses import fields
from typing import Any

from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec, LegendPosition

# Bump when the on-disk schema changes in a backward-incompatible way.
PRESET_VERSION = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _filter_known(cls, data: dict) -> dict:
    """Keep only keys that are real fields of ``cls``; warn about the rest.

    Makes hand-edited preset JSON forgiving — a stray/renamed key produces a
    warning instead of a crash.
    """
    known = {f.name for f in fields(cls)}
    unknown = set(data) - known
    if unknown:
        warnings.warn(
            f"Ignoring unknown {cls.__name__} keys in preset: {sorted(unknown)}",
            stacklevel=2,
        )
    return {k: v for k, v in data.items() if k in known}


# ---------------------------------------------------------------------------
# AxisSpec
# ---------------------------------------------------------------------------
def axisspec_to_dict(a: AxisSpec) -> dict[str, Any]:
    return {
        "label": a.label,
        "unit": a.unit,
        "fontsize": a.fontsize,
        "scale": a.scale.value,
        "lim": list(a.lim) if a.lim is not None else None,
        "ticks": list(a.ticks) if a.ticks is not None else None,
        "tick_fmt": a.tick_fmt,
        "invert": a.invert,
        "spines": list(a.spines),
        "grid": a.grid,
        "grid_minor": a.grid_minor,
    }


def axisspec_from_dict(data: dict | None) -> AxisSpec:
    if not data:
        return AxisSpec()
    d = _filter_known(AxisSpec, dict(data))
    if d.get("scale") is not None:
        d["scale"] = ScaleType(d["scale"])
    if d.get("lim") is not None:
        d["lim"] = tuple(d["lim"])
    return AxisSpec(**d)


# ---------------------------------------------------------------------------
# FigureSpec
# ---------------------------------------------------------------------------
def figurespec_to_dict(f: FigureSpec) -> dict[str, Any]:
    return {
        "figsize": list(f.figsize),
        "dpi": f.dpi,
        "tight": f.tight,
        "style": f.style,  # str or dict — both JSON-safe
    }


def figurespec_from_dict(data: dict | None) -> FigureSpec:
    if not data:
        return FigureSpec()
    d = _filter_known(FigureSpec, dict(data))
    if d.get("figsize") is not None:
        d["figsize"] = tuple(d["figsize"])
    return FigureSpec(**d)


# ---------------------------------------------------------------------------
# PlotSpec
# ---------------------------------------------------------------------------
def spec_to_dict(spec: PlotSpec) -> dict[str, Any]:
    """Convert a PlotSpec to a JSON-serializable dict."""
    if spec.post_hook is not None:
        warnings.warn(
            "PlotSpec.post_hook is a callable and cannot be saved to a preset; "
            "it will be dropped. Re-attach it after loading with spec.with_hook(...).",
            stacklevel=2,
        )
    return {
        "title": spec.title,
        "x": axisspec_to_dict(spec.x),
        "y": axisspec_to_dict(spec.y),
        "figure": figurespec_to_dict(spec.figure),
        "show_legend": spec.show_legend,
        "legend_pos": spec.legend_pos.value,
        "annotations": spec.annotations,
    }


def spec_from_dict(data: dict) -> PlotSpec:
    """Reconstruct a PlotSpec from a dict produced by :func:`spec_to_dict`."""
    return PlotSpec(
        title=data.get("title", ""),
        x=axisspec_from_dict(data.get("x")),
        y=axisspec_from_dict(data.get("y")),
        figure=figurespec_from_dict(data.get("figure")),
        show_legend=data.get("show_legend", False),
        legend_pos=LegendPosition(data.get("legend_pos", LegendPosition.BEST.value)),
        annotations=list(data.get("annotations", [])),
    )
