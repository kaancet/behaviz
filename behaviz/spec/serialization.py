from __future__ import annotations

import warnings
from dataclasses import fields
from enum import Enum
from typing import Any

from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import AxisSpec
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


def _plain(v: Any) -> Any:
    """JSON-safe scalar: enums → value, tuples → list, everything else as-is."""
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, tuple):
        return list(v)
    return v


def _dataclass_to_dict(obj) -> dict[str, Any]:
    """Serialize every field of a flat dataclass (no nested dataclasses)."""
    return {f.name: _plain(getattr(obj, f.name)) for f in fields(obj)}


# ---------------------------------------------------------------------------
# AxisSpec / FigureSpec
# ---------------------------------------------------------------------------
def axisspec_to_dict(a: AxisSpec) -> dict[str, Any]:
    return _dataclass_to_dict(a)


def axisspec_from_dict(data: dict | None) -> AxisSpec:
    if not data:
        return AxisSpec()
    d = _filter_known(AxisSpec, dict(data))
    if d.get("lim") is not None:
        d["lim"] = tuple(d["lim"])
    return AxisSpec(**d)  # AxisSpec.__post_init__ validates/normalises `scale`


def figurespec_to_dict(f: FigureSpec) -> dict[str, Any]:
    return _dataclass_to_dict(f)


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
    """Convert a PlotSpec to a JSON-serializable dict (every field, minus post_hook)."""
    if spec.post_hook is not None:
        warnings.warn(
            "PlotSpec.post_hook is a callable and cannot be saved to a preset; "
            "it will be dropped. Re-attach it after loading with spec.with_hook(...).",
            stacklevel=2,
        )
    out: dict[str, Any] = {}
    for f in fields(spec):
        if f.name == "post_hook":
            continue
        if f.name in ("x", "y"):
            out[f.name] = axisspec_to_dict(getattr(spec, f.name))
        elif f.name == "figure":
            out[f.name] = figurespec_to_dict(spec.figure)
        else:
            out[f.name] = _plain(getattr(spec, f.name))
    return out


def spec_from_dict(data: dict) -> PlotSpec:
    """Reconstruct a PlotSpec from a dict produced by :func:`spec_to_dict`."""
    d = _filter_known(PlotSpec, dict(data))
    d.pop("post_hook", None)
    d["x"] = axisspec_from_dict(d.get("x"))
    d["y"] = axisspec_from_dict(d.get("y"))
    d["figure"] = figurespec_from_dict(d.get("figure"))
    if d.get("legend_pos") is not None:
        d["legend_pos"] = LegendPosition(d["legend_pos"])
    return PlotSpec(**d)
