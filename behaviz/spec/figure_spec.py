from enum import Enum
from dataclasses import dataclass

class LegendPosition(str, Enum):
    BEST = "best"
    UPPER_RIGHT = "upper right"
    UPPER_LEFT = "upper left"
    LOWER_RIGHT = "lower right"
    LOWER_LEFT = "lower left"
    OUTSIDE = "outside"  # handled specially — placed outside axes


@dataclass
class FigureSpec:
    """Figure-level properties."""

    figsize: tuple = (12, 8)
    dpi: int = 120
    tight: bool = True  # call tight_layout automatically
    style: str|dict = "default"  # any valid plt.style name or custom style dictionary