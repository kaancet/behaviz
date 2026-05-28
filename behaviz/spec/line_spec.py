from dataclasses import dataclass


@dataclass
class LineSpec:
    """Visual style for a single line / scatter series."""

    color: str = "#027F68"
    alpha: float = 0.9
    linewidth: float = 1.5
    elinewidth: float = 1
    linestyle: str = "-"  # "-", "--", "-.", ":"
    marker: str = "none"  # "o", "s", "^", "none", …
    markersize: float = 5.0
    markeredgecolor:str = "w"
    markeredgewidth:float = 0.5
    label: str = ""  # legend entry for this series
    capsize:float = 0
