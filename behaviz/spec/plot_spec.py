import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Optional, Callable, Literal
from dataclasses import dataclass, field, replace

from .line_spec import LineSpec
from .axis_spec import AxisSpec, ScaleType
from .figure_spec import FigureSpec,LegendPosition

CM = 1/2.54


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

    # -- Axes
    x: AxisSpec = field(default_factory=AxisSpec)
    y: AxisSpec = field(default_factory=AxisSpec)

    # -- Figure (only used when the spec creates its own figure)
    figure: FigureSpec = field(default_factory=FigureSpec)

    # -- Legend
    show_legend: bool = False
    legend_pos: LegendPosition = LegendPosition.BEST

    # -- Annotations
    annotations: list[dict] = field(default_factory=list)
    # each dict: {"x": val, "y": val, "text": str, "kwargs": {...}}

    # -- Post-processing hook
    # Signature: hook(ax: Axes, spec: PlotSpec) -> None
    post_hook: Optional[Callable] = None
    
    
    @classmethod
    def preset(cls, name: Literal["paper", "poster", "notebook", "dark", "custom"], style_dict:dict|None=None) -> "PlotSpec":
        """
        Return a PlotSpec tuned for a specific output target.

        paper    → small figure, thin lines, no grid
        poster   → large figure, thick lines, big fonts
        notebook → medium figure, grid on, slightly transparent markers
        dark     → dark background, bright colours
        """
        if name == "paper":
            return cls(
                figure=FigureSpec(figsize=(5*CM, 5*CM), dpi=300, style="seaborn-v0_8-paper"),
                x=AxisSpec(grid=False),
                y=AxisSpec(grid=False),
            )
        elif name == "poster":
            return cls(
                figure=FigureSpec(figsize=(15*CM, 15*CM), dpi=300, style="seaborn-v0_8-talk"),
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
            assert isinstance(style_dict,dict), f"Custom style requires a custom style dictionary to be provided, got {style_dict}"
            return cls(
                figure=FigureSpec(figsize=style_dict.get("figure.figsize",(12, 12)), 
                                  dpi=style_dict.get("figure.dpi",300), 
                                  style=style_dict)
            )
        else:
            raise ValueError(f"Unknown preset '{name}'. Choose: paper | poster | notebook | dark. Or provide a custom style dictionary")
    
    @classmethod
    def from_labels(cls, xlabel: str, ylabel: str, xunit: str = "", yunit: str = "", **kwargs) -> "PlotSpec":
        """Shortest path when you only care about axis labels."""
        return cls(
            x=AxisSpec(label=xlabel, unit=xunit),
            y=AxisSpec(label=ylabel, unit=yunit),
            **kwargs,
        )
    
    # ------------------------------------------------------------------
    # Mutation-free override helpers
    # ------------------------------------------------------------------
    def with_title(self, title: str) -> "PlotSpec":
        return replace(self, title=title)

    def with_xlim(self, lo, hi) -> "PlotSpec":
        return replace(self, x=replace(self.x, lim=(lo, hi)))

    def with_ylim(self, lo, hi) -> "PlotSpec":
        return replace(self, y=replace(self.y, lim=(lo, hi)))

    def with_scale(self, axis: Literal["x", "y", "both"], scale_type:Literal["linear","log","logit","symlog"]) -> "PlotSpec":
        new = self
        if axis in ("x", "both"):
            new = replace(new, x=replace(new.x, scale=ScaleType(scale_type)))
        if axis in ("y", "both"):
            new = replace(new, y=replace(new.y, scale=ScaleType(scale_type)))
        return new
    
    def with_size(self, figsize:tuple[int,int]) -> "PlotSpec":
        return replace(self, figure=replace(self.figure, figsize=figsize))

    def with_annotation(self, x, y, text: str, **kwargs) -> "PlotSpec":
        new_annotations = self.annotations + [{"x": x, "y": y, "text": text, "kwargs": kwargs}]
        return replace(self, annotations=new_annotations)
    
    def with_hook(self, fn: Callable) -> "PlotSpec":
        return replace(self, post_hook=fn)
            
        
def make_ax(spec: PlotSpec):
    """Create a figure+ax using FigureSpec when the caller didn't supply one."""
    plt.style.use(spec.figure.style)
    fig, ax = plt.subplots(figsize=spec.figure.figsize, dpi=spec.figure.dpi)
    return fig, ax


def apply_axis_spec(ax, spec: PlotSpec) -> None:
    """Apply all AxisSpec and PlotSpec settings to an existing Axes object."""
    # Labels
    ax.set_xlabel(spec.x.full_label)
    ax.set_ylabel(spec.y.full_label)
    if spec.title:
        ax.set_title(spec.title)

    # Scales
    ax.set_xscale(spec.x.scale.value)
    ax.set_yscale(spec.y.scale.value)
    
    # remove spines
    

    # Limits
    if spec.x.lim:
        ax.set_xlim(*spec.x.lim)
    if spec.y.lim:
        ax.set_ylim(*spec.y.lim)

    # Ticks
    if spec.x.ticks is not None:
        ax.set_xticks(spec.x.ticks)
    if spec.y.ticks is not None:
        ax.set_yticks(spec.y.ticks)
    if spec.x.tick_fmt:
        ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(spec.x.tick_fmt))
    if spec.y.tick_fmt:
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(spec.y.tick_fmt))

    # Invert
    if spec.x.invert:
        ax.invert_xaxis()
    if spec.y.invert:
        ax.invert_yaxis()

    # Grid
    ax.grid(spec.x.grid or spec.y.grid, which="major",color="#c1c1c1")
    if spec.x.grid_minor or spec.y.grid_minor:
        ax.minorticks_on()
        ax.grid(True, which="minor", color="#c1c1c1", linestyle=":", linewidth=0.5, alpha=0.5)

    # Legend
    if spec.show_legend:
        if spec.legend_pos == LegendPosition.OUTSIDE:
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
        else:
            ax.legend(loc=spec.legend_pos.value)

    # Annotations
    for ann in spec.annotations:
        ax.annotate(
            ann["text"],
            xy=(ann["x"], ann["y"]),
            xytext=(ann["x"], ann["y"]),
            **ann.get("kwargs", {}),
        )

    # Post-processing hook
    if spec.post_hook:
        spec.post_hook(ax, spec)