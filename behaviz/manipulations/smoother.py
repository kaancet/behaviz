import numpy as np
from typing import Literal
from abc import ABC, abstractmethod


class _SmootherStrategy(ABC):
    @abstractmethod
    def apply(
        self,
        x: np.ndarray,
        y: np.ndarray,
        window: int,
        axis: Literal["x", "y"],
        **params,
    ) -> tuple[np.ndarray, np.ndarray]:
        pass


class BoxcarSmooth(_SmootherStrategy):
    def apply(self, x, y, *, axis="y", window=5, **_):
        kernel = np.ones(window) / window
        if axis == "x":
            x = np.convolve(x, kernel, mode="same")
        elif axis == "y":
            y = np.convolve(y, kernel, mode="same")
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y


class GaussianSmooth(_SmootherStrategy):
    def apply(self, x, y, *, axis="y", window=5, sigma=1.0, **_):
        t = np.arange(window) - window // 2
        kernel = np.exp(-0.5 * (t / sigma) ** 2)
        kernel /= kernel.sum()

        if axis == "x":
            x = np.convolve(x, kernel, mode="same")
        elif axis == "y":
            y = np.convolve(y, kernel, mode="same")
        else:
            raise ValueError(f"Unknown coordinate axis {axis}")
        return x, y
