"""``group`` / ``hue`` engine — split one plot call into per-category series.

Grammar-of-graphics semantics:
  * ``hue``  → one distinctly *colored* series per category, with a legend.
  * ``group`` → one separate primitive per category, same style, no legend.
  * both     → one primitive per (group × hue) combo, colored/labelled by hue.

The engine runs *after* the decorator has resolved and coerced channels, so it
operates on clean arrays. It slices the row-aligned channels per series, injects
``color``/``label`` (which the overrider then routes per backend), and — in
``dodge`` mode — shifts x and narrows width so bars/error bars sit side by side.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from .channels import Channel
from .data_source import resolve
from .errors import data_error
from .palette import categorical_palette, resolve_palette
from ..manipulations.dodger import get_dodge
from .palette import categorical_palette, resolve_palette

_DODGE_TOTAL_WIDTH = 0.8
# Group-only series (no hue) share one colour so they read as one family.
_GROUP_COLOR = categorical_palette(1)[0]


@dataclass
class GroupSpec:
    group: Any = None
    hue: Any = None
    group_order: Sequence | None = None
    hue_order: Sequence | None = None
    palette: Any = None
    dodge: str | None = None  # "centered" (default) | "stacked"; dodge plots only


@dataclass
class Series:
    args: tuple
    kwargs: dict


def pop_grouping(kwargs: dict) -> GroupSpec | None:
    """Strip the reserved grouping keys from ``kwargs`` (mutating it).

    Returns ``None`` when neither ``group`` nor ``hue`` was given (and drops any
    stray ``*_order``/``palette`` so they never reach a backend).
    """
    has_group = "group" in kwargs
    has_hue = "hue" in kwargs
    if not (has_group or has_hue):
        for k in ("group_order", "hue_order", "palette", "dodge"):
            kwargs.pop(k, None)
        return None
    return GroupSpec(
        group=kwargs.pop("group", None),
        hue=kwargs.pop("hue", None),
        group_order=kwargs.pop("group_order", None),
        hue_order=kwargs.pop("hue_order", None),
        palette=kwargs.pop("palette", None),
        dodge=kwargs.pop("dodge", None),
    )


def needs_grouping(gspec: GroupSpec | None) -> bool:
    return gspec is not None and (gspec.group is not None or gspec.hue is not None)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _resolve_key(func: str, name: str, value: Any, data: Any) -> np.ndarray:
    if isinstance(value, str) and data is None:
        raise data_error(
            func,
            f"`{name}` is a column name but no `data=` was given.",
            details={name: value},
            hint=f"pass data=<dataframe/dict> to use {name}=, or give the {name} values as an array.",
        )
    arr = np.asarray(resolve(value, data))
    if arr.ndim != 1:
        raise data_error(
            func,
            f"`{name}` must be a 1-D column of category labels.",
            details={name: arr},
        )
    return arr


def _ordered_unique(values: np.ndarray, order: Sequence | None) -> list:
    """Unique category values in first-appearance order, or the given order."""
    if order is not None:
        return list(order)
    seen: dict = {}
    for v in values.tolist():
        seen.setdefault(v, None)
    return list(seen)


def _locations(channels: Sequence[Channel], args: list, kwargs: dict) -> dict[str, tuple]:
    """Map each supplied channel name to where its value lives (args idx / kwargs key)."""
    loc: dict[str, tuple] = {}
    for i, ch in enumerate(channels):
        if i < len(args):
            loc[ch.name] = ("args", i)
        elif ch.name in kwargs:
            loc[ch.name] = ("kwargs", ch.name)
    return loc


def _get(loc, args, kwargs, name):
    where = loc.get(name)
    if where is None:
        return None
    return args[where[1]] if where[0] == "args" else kwargs[where[1]]


def _set(loc, args, kwargs, name, value):
    where = loc[name]
    if where[0] == "args":
        args[where[1]] = value
    else:
        kwargs[where[1]] = value


def _has_channel(channels, name) -> bool:
    return any(ch.name == name for ch in channels)


def _set_named(loc, args, kwargs, name, value):
    """Set a channel's value whether it was bound positionally, by keyword, or
    not supplied at all (in which case it goes into kwargs by name)."""
    if name in loc:
        _set(loc, args, kwargs, name, value)
    else:
        kwargs[name] = value


def _slice_value(v: Any, mask: np.ndarray, n: int) -> Any:
    """Slice a bound channel value to ``mask`` along whichever axis has length ``n``."""
    if not isinstance(v, np.ndarray):
        return v  # scalar (scalar_or_vector) or non-array — same for every series
    if v.ndim == 1 and v.shape[0] == n:
        return v[mask]
    if v.ndim == 2 and v.shape[1] == n:  # e.g. errorbar err of shape (2, N)
        return v[:, mask]
    if v.ndim >= 1 and v.shape[0] == n:
        return v[mask]
    return v


def build_series(
    func: str,
    channels: Sequence[Channel],
    args: tuple,
    kwargs: dict,
    data: Any,
    gspec: GroupSpec,
    mode: str,
) -> list[Series]:
    """Expand one resolved plot call into one :class:`Series` per category combo."""
    base_args = list(args)
    loc = _locations(channels, base_args, kwargs)

    group_vals = _resolve_key(func, "group", gspec.group, data) if gspec.group is not None else None
    hue_vals = _resolve_key(func, "hue", gspec.hue, data) if gspec.hue is not None else None
    n = len(hue_vals if hue_vals is not None else group_vals)

    # row-aligned channels must match the category length
    for ch in channels:
        v = _get(loc, base_args, kwargs, ch.name)
        if isinstance(v, np.ndarray) and v.ndim == 1 and v.shape[0] not in (n,) and ch.kind in ("vector",):
            raise data_error(
                func,
                f"`{ch.name}` has length {v.shape[0]} but group/hue has length {n}.",
                details={ch.name: v, "group/hue": (hue_vals if hue_vals is not None else group_vals)},
            )

    if mode == "dodge" and group_vals is not None and hue_vals is not None:
        raise data_error(
            func,
            "supports either `group=` or `hue=`, not both together yet.",
            hint="use one categorical for dodged bars/error bars.",
        )

    hue_cats = _ordered_unique(hue_vals, gspec.hue_order) if hue_vals is not None else None
    group_cats = _ordered_unique(group_vals, gspec.group_order) if group_vals is not None else None
    color_map = resolve_palette(hue_cats, gspec.palette) if hue_cats is not None else None

    if gspec.dodge is not None and mode != "dodge":
        raise data_error(
            func,
            "`dodge=` only applies to dodged plots (bar / errorbar).",
            hint="drop dodge= here; overlay plots layer series directly.",
        )

    # dodge dimension = hue if present, else group (exactly one in dodge mode)
    if mode == "dodge":
        strategy = get_dodge(gspec.dodge or "centered")
        if strategy.needs_bottom and not _has_channel(channels, "bottom"):
            raise data_error(
                func,
                f"dodge={gspec.dodge!r} needs bar heights to stack on, which this plot has no `bottom` for.",
                hint="stacked dodge is for bars; use the default (centered) dodge here.",
            )
        dodge_cats = hue_cats if hue_cats is not None else group_cats
        n_levels = len(dodge_cats)
        level_of = {c: i for i, c in enumerate(dodge_cats)}
        dodge_state: dict = {}

    g_iter = group_cats if group_cats is not None else [None]
    h_iter = hue_cats if hue_cats is not None else [None]

    seen_labels: set = set()
    series: list[Series] = []
    for gcat in g_iter:
        for hcat in h_iter:
            mask = np.ones(n, dtype=bool)
            if group_vals is not None:
                mask &= group_vals == gcat
            if hue_vals is not None:
                mask &= hue_vals == hcat
            if not mask.any():
                continue

            s_args = list(base_args)
            s_kwargs = dict(kwargs)
            for ch in channels:
                where = loc.get(ch.name)
                if where is None:
                    continue
                sliced = _slice_value(_get(loc, s_args, s_kwargs, ch.name), mask, n)
                _set(loc, s_args, s_kwargs, ch.name, sliced)

            if hcat is not None:
                s_kwargs["color"] = color_map[hcat]
                if hcat not in seen_labels:  # one legend entry per hue value
                    s_kwargs["label"] = str(hcat)
                    seen_labels.add(hcat)
            elif "color" not in kwargs:
                # group-only (no hue): keep every series the same colour
                s_kwargs["color"] = _GROUP_COLOR

            if mode == "dodge":
                level = level_of[hcat if hue_vals is not None else gcat]
                x = _get(loc, s_args, s_kwargs, "x")
                y = _get(loc, s_args, s_kwargs, "y")
                placement = strategy.place(level, n_levels, x, y, total_width=_DODGE_TOTAL_WIDTH, state=dodge_state)
                _set(loc, s_args, s_kwargs, "x", placement.x)
                if placement.width is not None and _has_channel(channels, "width"):
                    _set_named(loc, s_args, s_kwargs, "width", placement.width)
                if placement.bottom is not None and _has_channel(channels, "bottom"):
                    _set_named(loc, s_args, s_kwargs, "bottom", placement.bottom)

            series.append(Series(args=tuple(s_args), kwargs=s_kwargs))

    return series
