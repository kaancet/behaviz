import numpy as np
from typing import Literal, Callable
from numpy.typing import ArrayLike
from abc import ABC, abstractmethod


class _BinnerStrategy(ABC):
    @abstractmethod
    def apply(
        self,
        x: np.ndarray,
        y: np.ndarray,
        bins: int | ArrayLike,
        axis: Literal["x", "y"],
        **params,
    ) -> tuple[np.ndarray, np.ndarray]:
        pass


class MeanBinner(_BinnerStrategy):
    def apply(self, x, y, bins=10, *, axis="x", **params):
        if axis == "x":
            edges = np.histogram_bin_edges(x, bins=bins)
            x, y = _bin(x, y, edges, np.nanmean)
        elif axis == "y":
            edges = np.histogram_bin_edges(y, bins=bins)
            x, y = _bin(y, x, edges, np.nanmean)
        return x, y


class MedianBinner(_BinnerStrategy):
    def apply(self, x, y, bins=10, *, axis="x", **params):
        if axis == "x":
            edges = np.histogram_bin_edges(x, bins=bins)
            x, y = _bin(x, y, edges, np.nanmedian)
        elif axis == "y":
            edges = np.histogram_bin_edges(y, bins=bins)
            x, y = _bin(y, x, edges, np.nanmedian)
        return x, y


class SumBinner(_BinnerStrategy):
    def apply(self, x, y, bins=10, *, axis="x", **params):
        if axis == "x":
            edges = np.histogram_bin_edges(x, bins=bins)
            x, y = _bin(x, y, edges, np.nansum)
        elif axis == "y":
            edges = np.histogram_bin_edges(y, bins=bins)
            x, y = _bin(y, x, edges, np.nansum)
        return x, y


class CountBinner(_BinnerStrategy):
    def apply(self, x, y, bins=10, *, axis="x", **params):
        if axis == "x":
            edges = np.histogram_bin_edges(x, bins=bins)
            x, y = _bin(x, y, edges, len)
        elif axis == "y":
            edges = np.histogram_bin_edges(y, bins=bins)
            x, y = _bin(y, x, edges, len)
        return x, y


def _bin(bin_coord: np.ndarray, val_coord: np.ndarray, bin_edges: np.ndarray, agg_fn: Callable):
    centers, agg_val = [], []
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (bin_coord >= lo) & (bin_coord < hi)
        if mask.any():
            centers.append((lo + hi) / 2)
            agg_val.append(agg_fn(val_coord[mask]))
    bin_out = np.array(centers)
    val_out = np.array(agg_val)
    return bin_out, val_out
