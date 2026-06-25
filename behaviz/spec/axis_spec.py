from enum import Enum
from typing import Optional, Literal
from dataclasses import dataclass, field


class ScaleType(str, Enum):
    LINEAR = "linear"
    LOG = "log"
    SYMLOG = "symlog"
    LOGIT = "logit"


@dataclass
class AxisSpec:
    """Everything that describes a single axis."""

    label: str = ""
    unit: str = ""  # appended automatically: "Voltage (mV)"
    fontsize: float = 12
    scale: ScaleType = ScaleType.LINEAR
    lim: Optional[tuple] = None  # (min, max) or None → auto
    ticks: Optional[list] = None  # explicit tick positions
    tick_fmt: Optional[str] = None  # e.g. "%.2f", "{x:.1e}"
    invert: bool = False  # flip axis direction
    spines: list[Literal["bottom", "top", "left", "right"]] = field(
        default_factory=lambda: ["bottom", "top", "left", "right"]
    )
    spine_width: float = 2
    spine_color: Optional[str] = None  # None → backend default
    spine_offset: float = 0  # push spines outward from the axes (matplotlib only)
    spine_trim: bool = False  # clip spines to the data range (matplotlib only)
    tick_dir: Literal["out", "in", "inout"] = "out"
    tick_length: Optional[float] = None  # None → 3 × spine_width
    tick_width: Optional[float] = None  # None → spine_width
    tick_color: Optional[str] = None  # None → backend default
    tick_sides: Optional[list] = None  # which sides show tick marks; None → backend default
    grid: bool = True
    grid_minor: bool = False
    grid_alpha: float = 0.5
    grid_color: str = "#c1c1c1"
    grid_style: str = "-"  # major grid linestyle ("-", "--", ":", "-.")
    grid_width: float = 0.8  # major grid linewidth

    @property
    def full_label(self) -> str:
        """Return 'Label (unit)' or just 'Label' when no unit is set."""
        return f"{self.label} ({self.unit})" if self.unit else self.label
