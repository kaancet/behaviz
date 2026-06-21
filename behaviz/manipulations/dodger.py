"""Dodging: arrange side-by-side categories that share an x position.

A deterministic positioning transform (no RNG/state) used to place grouped bars
or error bars relative to each other instead of on top of one another. Like the
other manipulations it is a small strategy family — but with its own contract
(``n_levels → placement`` rather than ``(x, y) → (x, y)``), so it is not wired
into ``VisualManipulator``; the grouping engine selects a strategy by name.

Strategies
----------
``centered``  side-by-side: tile n equal slots centered on each x.
``stacked``   each level sits on the cumulative height of the levels below it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


def dodge_offsets(n_levels: int, total_width: float = 0.8) -> tuple[list[float], float]:
    """Tile ``n_levels`` slots, centered on each x position.

    Returns ``(offsets, width)`` — the x offset per level (symmetric about 0)
    and the per-level width (``total_width / n_levels``).

    >>> dodge_offsets(1)
    ([0.0], 0.8)
    >>> dodge_offsets(2, total_width=0.8)
    ([-0.2, 0.2], 0.4)
    """
    if n_levels < 1:
        raise ValueError(f"n_levels must be >= 1, got {n_levels}.")
    width = total_width / n_levels
    offsets = [(i - (n_levels - 1) / 2) * width for i in range(n_levels)]
    return offsets, width


@dataclass(frozen=True)
class DodgePlacement:
    """How one level should be drawn. ``None`` fields leave the default in place."""

    x: np.ndarray
    width: float | None = None
    bottom: np.ndarray | None = None


class _DodgeStrategy(ABC):
    """Place one level of a grouped plot.

    ``place`` is called once per level, in draw order. ``state`` is a mutable
    dict the caller threads across the levels of a single plot, so strategies
    that need running totals (e.g. stacking) can accumulate without holding
    state on the (shared, singleton) strategy instance.
    """

    #: True when the strategy positions via ``bottom`` and so needs bar heights
    #: (a ``bottom`` channel); used to reject it on plots that lack one.
    needs_bottom: bool = False

    @abstractmethod
    def place(
        self,
        level: int,
        n_levels: int,
        x: np.ndarray,
        y: np.ndarray,
        *,
        total_width: float,
        state: dict,
    ) -> DodgePlacement: ...


class CenteredDodge(_DodgeStrategy):
    """Side-by-side bars/markers: equal slots tiled and centered on each x."""

    def place(self, level, n_levels, x, y, *, total_width, state):
        offsets, width = dodge_offsets(n_levels, total_width)
        return DodgePlacement(x=np.asarray(x, dtype=float) + offsets[level], width=width)


class StackedDodge(_DodgeStrategy):
    """Stacked bars: levels share x, each sitting on the cumulative height below."""

    needs_bottom = True

    def place(
        self,
        level,
        n_levels,
        x,
        y,
        *,
        total_width,
        state,
    ):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        running: dict = state.setdefault("running", {})
        keys = [round(float(xi), 9) for xi in x]  # tolerate float x positions
        bottom = np.array([running.get(k, 0.0) for k in keys], dtype=float)
        for k, yi in zip(keys, y):
            running[k] = running.get(k, 0.0) + float(yi)
        return DodgePlacement(x=x, width=total_width, bottom=bottom)


class NoDodge(_DodgeStrategy):
    def place(self, level, n_levels, x, y, *, total_width, state):
        return DodgePlacement(x=np.asarray(x, dtype=float), width=total_width)


_DODGE_STRATEGIES: dict[str, _DodgeStrategy] = {
    "centered": CenteredDodge(),
    "stacked": StackedDodge(),
    "none": NoDodge(),
}


def get_dodge(name: str) -> _DodgeStrategy:
    """Look up a dodge strategy by name."""
    try:
        return _DODGE_STRATEGIES[name]
    except KeyError:
        raise ValueError(f"Unknown dodge {name!r}. Choose: {', '.join(sorted(_DODGE_STRATEGIES))}.") from None
