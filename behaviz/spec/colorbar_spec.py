from dataclasses import dataclass
from typing import Optional, Literal

# Default padding (axes-fraction) between the axes and the bar, per side.
_AUTO_PAD = {"right": 0.04, "left": 0.15, "top": 0.10, "bottom": 0.15}


@dataclass
class ColorbarSpec:
    """Styling for a colorbar attached to a colour-mapped plot (e.g. ``plot_image``).

    Pass it to a plot's ``colorbar=`` keyword, or use the shorthands handled by
    :meth:`coerce`: ``colorbar=True`` for a default bar, ``colorbar="label"`` for
    a labelled one.

    Fields
    ------
    label : str
        Text shown beside the bar.
    location : "right" | "left" | "top" | "bottom"
        Side of the axes to place the bar on (sets orientation automatically).
    ticks : list | None
        Explicit tick positions. ``None`` → automatic.
    tick_fmt : str | None
        printf-style tick format, e.g. ``"%.1f"``.
    fraction : float
        matplotlib sizing. The default (0.046) makes the bar match the axes
        height — the usual "magic number" — so users don't have to.
    pad : float | None
        Gap between axes and bar (axes-fraction). ``None`` picks a location-aware
        default that clears the axis labels (small on the right, larger on the
        bottom/left where tick labels live).
    fontsize : float
        Label and tick-label size.
    """

    label: str = ""
    location: Literal["right", "left", "top", "bottom"] = "right"
    ticks: Optional[list] = None
    tick_fmt: Optional[str] = None
    fraction: float = 0.046
    pad: Optional[float] = None
    fontsize: float = 12

    def resolved_pad(self) -> float:
        """The pad to use — explicit if set, else a location-aware default."""
        if self.pad is not None:
            return self.pad
        return _AUTO_PAD.get(self.location, 0.05)

    @classmethod
    def coerce(cls, value) -> "ColorbarSpec":
        """Normalise a colorbar argument (True/str/spec) to a spec."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(label=value)
        return cls()
