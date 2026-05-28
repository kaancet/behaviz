import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from behaviz.core.renderer import Renderer
from behaviz.backends.matplotlib.overrider import call_mpl
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.figure_spec import LegendPosition


class MatplotlibRenderer(Renderer):
    name = "matplotlib"
    def make_figure(self, spec: PlotSpec):
        plt.style.use(spec.figure.style)
        fig, ax = plt.subplots(figsize=spec.figure.figsize, dpi=spec.figure.dpi)
        return fig, ax
    
    def get_figure(self, ax) -> plt.Figure:
        return ax.get_figure()
    
    def apply_axis_spec(self, ax, spec: PlotSpec) -> None:
        """Apply all AxisSpec and PlotSpec settings to an existing Axes object."""
        # Labels
        ax.set_xlabel(spec.x.full_label)
        ax.set_ylabel(spec.y.full_label)
        if spec.title:
            ax.set_title(spec.title)

        # Scales
        ax.set_xscale(spec.x.scale.value)
        ax.set_yscale(spec.y.scale.value)

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
        
    def line(self, ax, x, y, **kwargs):
        call_mpl(ax, "plot", x, y, **kwargs)

    def scatter(self, ax, x, y, **kwargs):
        call_mpl(ax, "scatter", x, y, **kwargs)

    def errorbar(self, ax, x, y, err, **kwargs):
        call_mpl(ax, "errorbar", x, y, err, **kwargs)

    def bar(self, ax, x, y, width, bottom=None, **kwargs):
        call_mpl(ax, "bar", x, y, width=width, bottom=bottom, **kwargs)

    def step(self, ax, x, y, where="pre", **kwargs):
        call_mpl(ax, "step", x, y, where=where, **kwargs)

    def violin(self, ax, ys, positions, **kwargs):
        return call_mpl(ax, "violinplot", ys, positions=positions, **kwargs)