from enum import Enum
from typing import Optional
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
    style: str | dict = "default"  # any valid plt.style name or custom style dictionary
    face_color: Optional[str] = None  # figure background; None → backend default
    axes_color: Optional[str] = None  # axes/plot-area background; None → backend default
    font_family: Optional[str] = None  # font family for all text; None → backend default
