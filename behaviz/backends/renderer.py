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
        return self.name

    @abstractmethod
    def make_figure(self, spec: PlotSpec):
        """Create and return a (fig, ax) equivalent for this backend."""
        pass

    @abstractmethod
    def get_figure(self, ax):
        """Get the figure of a given axes"""
        pass

    @abstractmethod
    def get_xlims(self, ax):
        pass

    @abstractmethod
    def get_ylims(self, ax):
        pass

    @abstractmethod
    def apply_axis_spec(self, ax, spec: PlotSpec) -> None:
        """Apply axis labels, limits, grid, title, etc."""
        pass

    @abstractmethod
    def save(self, fig, path, **kwargs) -> str:
        """Write ``fig`` to ``path``, dispatching on the file extension.

        Raises ``BehavizSaveError`` for unsupported backend/format combinations.
        Returns the path written.
        """
        pass

    @abstractmethod
    def show(self, fig) -> None:
        """Display ``fig`` interactively (window, browser tab, or notebook cell)."""
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
    def hbar(self, ax, x, y, width, bottom=None, **kwargs) -> None:
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

    @abstractmethod
    def vertical(self, x, ymin, ymax, **kwargs):
        pass

    @abstractmethod
    def horizontal(self, x, ymin, ymax, **kwargs):
        pass

    @abstractmethod
    def image(self, ax, data, extent=None, origin="upper", cmap="viridis", vmin=None, vmax=None, **kwargs):
        pass

    @abstractmethod
    def colorbar(self, ax, mappable, cbar_spec):
        """Attach a colorbar for a colour-mapped artist (e.g. the result of image())."""
        pass

    @abstractmethod
    def fill_between(self, ax, x, y1, y2=0, **kwargs):
        pass

    @abstractmethod
    def pie(self, ax, sizes, labels=None, colors=None, autopct=None, **kwargs):
        pass

    @abstractmethod
    def hexbin(self, ax, x, y, gridsize=30, cmap="viridis", **kwargs):
        pass
