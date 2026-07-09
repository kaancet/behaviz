import numpy as np
from typing import Literal
from abc import ABC, abstractmethod


class _NormaliserStrategy(ABC):
    @abstractmethod
    def apply(
        self,
        x: np.ndarray,
        y: np.ndarray,
        axis: Literal["x", "y"],
        **params,
    ) -> tuple[np.ndarray, np.ndarray]:
        pass


class ConstantNormaliser(_NormaliserStrategy):
    def apply(self, x, y, *, axis="y", normalise_by=None, **_):
        if normalise_by == 0:
            raise ValueError("Can't normalise by 0!")
        if normalise_by is None:
            raise ValueError("Constant normalisation requires a constant value")
        if axis == "x":
            x = x / normalise_by
        elif axis == "y":
            y = y / normalise_by
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y


class MinMaxNormaliser(_NormaliserStrategy):
    def apply(self, x, y, *, axis="y", **_):
        if axis == "x":
            lo, hi = np.nanmin(x), np.nanmax(x)
            x = (x - lo) / (hi - lo) if hi != lo else np.zeros_like(x)
        elif axis == "y":
            lo, hi = np.nanmin(y), np.nanmax(y)
            y = (y - lo) / (hi - lo) if hi != lo else np.zeros_like(y)
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y


class BaselineNormaliser(_NormaliserStrategy):
    def apply(self, x, y, *, axis="y", baseline_idx=None, **_):
        if baseline_idx is None:
            raise ValueError("baseline normalisation requires baseline_idx=")

        if axis == "x":
            x = x - np.nanmean(x[baseline_idx])
        elif axis == "y":
            y = y - np.nanmean(y[baseline_idx])
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y


class ZScoreNormaliser(_NormaliserStrategy):
    def apply(self, x, y, *, axis="y", **_):
        if axis == "x":
            x = (x - np.nanmean(x)) / np.nanstd(x)
        elif axis == "y":
            y = (y - np.nanmean(y)) / np.nanstd(y)
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y
