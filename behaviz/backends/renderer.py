from abc import ABC, abstractmethod
import numpy as np
from typing import Any

from ..spec.plot_spec import PlotSpec


# Each backend works with its own native objects.
# these are just placeholders for type hinting
BehavizFigure = Any
BehavizAxes = Any


class Renderer(ABC):
    name = ""
    """
    Abstract backend. Every backend implements this interface.
    Public plot functions talk only to this — never to matplotlib directly.
    """

    def __str__(self):
        print(self.name)

    @abstractmethod
    def make_figure(self, spec: PlotSpec):
        """Create and return a (fig, ax) equivalent for this backend."""
        pass

    @abstractmethod
    def get_figure(self, ax):
        """Get the figure of a given axes"""
        pass

    @abstractmethod
    def apply_axis_spec(self, ax, spec: PlotSpec) -> None:
        """Apply axis labels, limits, grid, title, etc."""
        pass

    @abstractmethod
    def line(self, ax, x: np.ndarray, y: np.ndarray, **kwargs) -> None:
        pass

    @abstractmethod
    def scatter(self, ax, x: np.ndarray, y: np.ndarray, **kwargs) -> None:
        pass

    @abstractmethod
    def errorbar(self, ax, x, y, err, **kwargs) -> None:
        pass

    @abstractmethod
    def bar(self, ax, x, y, width, bottom=None, **kwargs) -> None:
        pass

    @abstractmethod
    def step(self, ax, x, y, where="pre", **kwargs) -> None:
        pass

    @abstractmethod
    def violin(self, ax, ys, positions, **kwargs):
        pass

    @abstractmethod
    def text(self, ax, x, y, s, **kwargs):
        pass
