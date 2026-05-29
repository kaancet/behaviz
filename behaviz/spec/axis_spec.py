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
    spines: list[Literal["bottom", "top", "left", "right"]] = field(default_factory=lambda: ["bottom","top","left","right"])
    grid: bool = True
    grid_minor: bool = False

    @property
    def full_label(self) -> str:
        """Return 'Label (unit)' or just 'Label' when no unit is set."""
        return f"{self.label} ({self.unit})" if self.unit else self.label