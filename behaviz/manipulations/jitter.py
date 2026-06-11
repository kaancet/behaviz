import numpy as np
from typing import Literal
from abc import ABC, abstractmethod


class _JitterStrategy(ABC):
    @abstractmethod
    def apply(
        self,
        x: np.ndarray,
        y: np.ndarray,
        rng: np.random.Generator,
        axis: Literal["x", "y"],
        **params,
    ) -> tuple[np.ndarray, np.ndarray]:
        pass


class UniformJitter(_JitterStrategy):
    def apply(self, x, y, rng, *, axis="x", strength=0.05, **_):
        if axis == "x":
            x = x + rng.uniform(-strength, strength, size=x.shape)
        elif axis == "y":
            y = y + rng.uniform(-strength, strength, size=y.shape)
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y


class NormalJitter(_JitterStrategy):
    def apply(self, x, y, rng, *, axis="x", sigma=0.05, **_):
        if axis == "x":
            x = x + rng.normal(0, sigma, size=x.shape)
        elif axis == "y":
            y = y + rng.normal(0, sigma, size=y.shape)
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y


class BeeswarmJitter(_JitterStrategy):
    """Dot-swarm layout (replaces the free make_dot_swarm function)."""

    def apply(
        self,
        x,
        y,
        rng,
        *,
        axis="x",
        center: float = 0.0,
        bin_width: float = 50.0,
        width: float = 0.5,
        side="center",
        **_,
    ):
        if axis == "x":
            x = x + self._beeswarm_coords(y, center=center, bin_width=bin_width, width=width, side=side)
        elif axis == "y":
            y = y + self._beeswarm_coords(x, center=center, bin_width=bin_width, width=width, side=side)
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y  # y is unchanged; x is the dispersed axis

    @staticmethod
    def _beeswarm_coords(
        data: np.ndarray,
        center: float,
        bin_width: float,
        width: float,
        side: Literal["left", "right", "center"] = "center",
    ) -> np.ndarray:
        """Pure function — direct replacement for make_dot_swarm in rainplot.py."""
        if len(data) <= 1:
            return np.array([center])
        bin_edges = np.arange(np.nanmin(data), np.nanmax(data) + bin_width, bin_width)
        counts, bin_edges = np.histogram(data, bins=bin_edges)
        max_count = np.nanmax(counts) // 2
        dx = width / max_count if max_count else 0
        idx_in_bin = []
        for k, (ymin, ymax) in enumerate(zip(bin_edges[:-1], bin_edges[1:])):
            mask = (data >= ymin) & (data <= ymax if k == len(bin_edges) - 2 else data < ymax)
            idx_in_bin.append(np.nonzero(mask)[0])
        x_coords = np.zeros(len(data))
        for i in idx_in_bin:
            if len(i) > 1:
                n, j = len(i), len(i) % 2
                left_half = i[: n // 2][::-1]
                right_half = i[n // 2 + j :]
                for rank, (ll, rr) in enumerate(zip(left_half, right_half)):
                    offset = (rank + (j == 0) * 0.5) * dx
                    x_coords[ll] = -offset if side != "right" else offset
                    x_coords[rr] = offset if side != "left" else -offset
        return x_coords + center
