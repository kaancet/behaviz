from typing import Optional, Callable, Literal
from dataclasses import dataclass, field, replace

from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec, LegendPosition
from behaviz.spec._style_presets import RC_PRESETS


CM = 1 / 2.54


@dataclass
class PlotSpec:
    """
    Master spec object.  Compose sub-specs for full control, or rely on
    defaults and override only what you need.

    Quick-start
    -----------
    >>> spec = PlotSpec(title="My Plot", x=AxisSpec(label="Time", unit="s"))
    >>> plot_line(ax, t, v, spec)
    """

    # -- Identity
    title: str = ""
    title_fontsize: Optional[float] = None  # None → x.fontsize + 2
    text_color: Optional[str] = None  # labels, title, tick labels; None → backend default

    # -- Axes
    x: AxisSpec = field(default_factory=AxisSpec)
    y: AxisSpec = field(default_factory=AxisSpec)

    # -- Figure (only used when the spec creates its own figure)
    figure: FigureSpec = field(default_factory=FigureSpec)

    # -- Legend
    show_legend: bool = False
    legend_pos: LegendPosition = LegendPosition.BEST
    legend_fontsize: Optional[float] = None  # None → backend default

    # -- Annotations
    annotations: list[dict] = field(default_factory=list)
    # each dict: {"x": val, "y": val, "text": str, "kwargs": {...}}

    # -- Post-processing hook
    # Signature: hook(ax: Axes, spec: PlotSpec) -> None
    post_hook: Optional[Callable] = None

    @classmethod
    def preset(
        cls,
        name: Literal[
            "paper",
            "poster",
            "notebook",
            "dark",
            "presentation",
            "presentation_dark",
            "print",
            "custom",
        ],
        style_dict: dict | None = None,
    ) -> "PlotSpec":
        """
        Return a PlotSpec tuned for a specific output target.

        paper    → small figure, thin lines, no grid
        poster   → large figure, thick lines, big fonts
        notebook → medium figure, grid on, slightly transparent markers
        dark     → dark background, bright colours
        paper             → small figure, thin lines, no grid
        poster            → large figure, thick lines, big fonts
        notebook          → medium figure, grid on, slightly transparent markers
        dark              → dark background, bright colours
        presentation      → large 12x12in slide figure, thick lines, 24pt fonts
        presentation_dark → presentation on a #1E1E1E dark background, muted colors
        print             → 8x8cm Word/print figure, thin lines, 14pt fonts
        """
        if name in RC_PRESETS:
            return cls._from_rcparams(RC_PRESETS[name])

        if name == "paper":
            return cls(
                figure=FigureSpec(figsize=(5 * CM, 5 * CM), dpi=300, style="seaborn-v0_8-paper"),
                x=AxisSpec(grid=False),
                y=AxisSpec(grid=False),
            )
        elif name == "poster":
            return cls(
                figure=FigureSpec(figsize=(15 * CM, 15 * CM), dpi=300, style="seaborn-v0_8-talk"),
            )
        elif name == "notebook":
            return cls(
                figure=FigureSpec(figsize=(8, 5), dpi=100, style="seaborn-v0_8-whitegrid"),
                x=AxisSpec(grid=True, grid_minor=True),
                y=AxisSpec(grid=True, grid_minor=True),
            )
        elif name == "dark":
            return cls(
                figure=FigureSpec(figsize=(8, 5), dpi=120, style="dark_background"),
            )
        elif name == "custom":
            assert isinstance(style_dict, dict), (
                f"Custom style requires a custom style dictionary to be provided, got {style_dict}"
            )
            return cls(
                figure=FigureSpec(
                    figsize=style_dict.get("figure.figsize", (12, 12)),
                    dpi=style_dict.get("figure.dpi", 300),
                    style=style_dict,
                )
            )
        else:
            raise ValueError(
                f"Unknown preset '{name}'. Choose: paper | poster | notebook | dark. Or provide a custom style dictionary"
            )

    @classmethod
    def _from_rcparams(cls, rc: dict) -> "PlotSpec":
        """Build a PlotSpec from a raw matplotlib rcParams dict.

        The full dict is still stored on ``FigureSpec.style`` (applied via
        ``plt.style.use`` on matplotlib/seaborn), but the visual properties are
        also mirrored onto first-class spec fields so the **bokeh** backend —
        which has no rcParams — renders the same preset. Grid is left off,
        matching these styles (they define grid appearance but never set
        ``axes.grid``).
        """
        labelsize = rc.get("axes.labelsize", 12)
        spines = [
            side
            for side, key in (
                ("bottom", "axes.spines.bottom"),
                ("left", "axes.spines.left"),
                ("top", "axes.spines.top"),
                ("right", "axes.spines.right"),
            )
            if rc.get(key, True)
        ]
        axis = lambda p: AxisSpec(  # noqa: E731  (p = "x"/"y" tick prefix)
            fontsize=labelsize,
            spines=list(spines),
            grid=False,
            spine_width=rc.get("axes.linewidth", 2),
            spine_color=rc.get("axes.edgecolor"),
            tick_color=rc.get(f"{p}tick.color"),
            tick_length=rc.get(f"{p}tick.major.size"),
            tick_width=rc.get(f"{p}tick.major.width"),
            grid_color=rc.get("grid.color", "#c1c1c1"),
            grid_alpha=rc.get("grid.alpha", 0.5),
            grid_width=rc.get("grid.linewidth", 0.8),
            grid_style=rc.get("grid.linestyle", "-"),
        )
        return cls(
            text_color=rc.get("text.color") or rc.get("axes.labelcolor"),
            figure=FigureSpec(
                figsize=rc.get("figure.figsize", (12, 12)),
                dpi=rc.get("figure.dpi", 300),
                style=rc,
                face_color=rc.get("figure.facecolor"),
                axes_color=rc.get("axes.facecolor"),
            ),
            x=axis("x"),
            y=axis("y"),
        )

    @classmethod
    def from_labels(cls, xlabel: str, ylabel: str, xunit: str = "", yunit: str = "", **kwargs) -> "PlotSpec":
        """Shortest path when you only care about axis labels."""
        return cls(
            x=AxisSpec(label=xlabel, unit=xunit),
            y=AxisSpec(label=ylabel, unit=yunit),
            **kwargs,
        )

    # ==============================
    # Mutation-free override helpers
    # ==============================
    def with_title(self, title: str) -> "PlotSpec":
        return replace(self, title=title)

    def with_xlabel(self, label: str) -> "PlotSpec":
        return replace(self, x=replace(self.x, label=label))

    def with_ylabel(self, label: str) -> "PlotSpec":
        return replace(self, y=replace(self.y, label=label))

    def with_xlim(self, lo, hi) -> "PlotSpec":
        return replace(self, x=replace(self.x, lim=(lo, hi)))

    def with_ylim(self, lo, hi) -> "PlotSpec":
        return replace(self, y=replace(self.y, lim=(lo, hi)))

    def with_xticks(self, ticks: list, tick_fmt: str = None) -> "PlotSpec":
        new = replace(self, x=replace(self.x, ticks=ticks))
        new = replace(new, x=replace(new.x, tick_fmt=tick_fmt))
        return new

    def with_yticks(self, ticks: list, tick_fmt: str = None) -> "PlotSpec":
        new = replace(self, y=replace(self.y, ticks=ticks))
        new = replace(new, y=replace(new.y, tick_fmt=tick_fmt))
        return new

    def with_fontsize(self, fontsize: float, axis: Literal["x", "y", "both"] = "both") -> "PlotSpec":
        new = self
        if axis in ("x", "both"):
            new = replace(new, x=replace(new.x, fontsize=fontsize))

        if axis in ("y", "both"):
            new = replace(new, y=replace(new.y, fontsize=fontsize))
        return new

    def with_scale(
        self, axis: Literal["x", "y", "both"], scale_type: Literal["linear", "log", "logit", "symlog"]
    ) -> "PlotSpec":
        new = self
        if axis in ("x", "both"):
            new = replace(new, x=replace(new.x, scale=ScaleType(scale_type)))
        if axis in ("y", "both"):
            new = replace(new, y=replace(new.y, scale=ScaleType(scale_type)))
        return new

    def with_size(self, figsize: tuple[int, int]) -> "PlotSpec":
        return replace(self, figure=replace(self.figure, figsize=figsize))

    def with_annotation(self, x, y, text: str, **kwargs) -> "PlotSpec":
        new_annotations = self.annotations + [{"x": x, "y": y, "text": text, "kwargs": kwargs}]
        return replace(self, annotations=new_annotations)

    def with_hook(self, fn: Callable) -> "PlotSpec":
        return replace(self, post_hook=fn)
