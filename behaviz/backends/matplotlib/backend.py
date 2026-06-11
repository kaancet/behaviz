import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from behaviz.backends.renderer import Renderer
from behaviz.backends.matplotlib.overrider import MatplotlibOverrider
from behaviz.backends.matplotlib.hover_engine import MatplotlibHoverEngine
from behaviz.backends.hover import pop_hover_kwargs, extract_xy, HOVERABLE
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.figure_spec import LegendPosition
from behaviz.core.plot_registry import get_plot


class MatplotlibRenderer(Renderer):
    name = "matplotlib"

    def __init__(self):
        self._ovr = MatplotlibOverrider()
        self._hover = MatplotlibHoverEngine()

    def _call(self, ax, method: str, *args, **kwargs):
        """Route kwargs, call ax.<method>, apply post-hoc artist styling."""
        # Opt-in hover keys are stripped before routing so they never reach mpl.
        hover_opts = pop_hover_kwargs(kwargs)

        native_method = get_plot(method, "matplotlib")
        call_kw, post_kw = self._ovr.route(method, kwargs)
        result = getattr(ax, native_method)(*args, **call_kw)
        self._ovr.apply_post(result, post_kw)

        if hover_opts is not None and method in HOVERABLE:
            x, y = extract_xy(args, kwargs)
            if x is not None and y is not None:
                self._hover.attach(ax, result, x, y, hover_opts)
        return result

    def make_figure(self, spec: PlotSpec):
        plt.style.use(spec.figure.style)
        fig, ax = plt.subplots(figsize=spec.figure.figsize, dpi=spec.figure.dpi)
        return fig, ax

    def get_figure(self, ax) -> plt.Figure:
        return ax.get_figure()

    def get_xlims(self, ax):
        return list(ax.get_xlim())

    def get_ylims(self, ax):
        return list(ax.get_ylim())

    def apply_axis_spec(self, ax, spec: PlotSpec) -> None:
        """Apply all AxisSpec and PlotSpec settings to an existing Axes object."""
        # Labels
        ax.set_xlabel(spec.x.full_label, fontsize=spec.x.fontsize)
        ax.set_ylabel(spec.y.full_label, fontsize=spec.x.fontsize)
        if spec.title:
            ax.set_title(spec.title, fontsize=spec.x.fontsize + 2)

        ax.tick_params(axis="x", labelsize=spec.x.fontsize)
        ax.tick_params(axis="y", labelsize=spec.x.fontsize)

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
            tick_pos = spec.x.ticks
            if all(isinstance(xi, str) for xi in spec.x.ticks):
                # all strings, make a dummy position ticks
                tick_pos = [i for i in range(len(spec.x.ticks))]
            ax.set_xticks(tick_pos)
            ax.set_xticklabels(spec.x.ticks)

        if spec.y.ticks is not None:
            tick_pos = spec.y.ticks
            if all(isinstance(yi, str) for yi in spec.y.ticks):
                # all strings, make a dummy position ticks
                tick_pos = [i for i in range(len(spec.y.ticks))]
            ax.set_yticks(tick_pos)
            ax.set_yticklabels(spec.y.ticks)
        if spec.x.tick_fmt:
            ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(spec.x.tick_fmt))
        if spec.y.tick_fmt:
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(spec.y.tick_fmt))

        # spines
        for s in ax.spines:
            if s not in spec.x.spines:
                ax.spines[s].set_visible(False)

            if s not in spec.y.spines:
                ax.spines[s].set_visible(False)

        # Invert
        if spec.x.invert:
            ax.invert_xaxis()
        if spec.y.invert:
            ax.invert_yaxis()

        # Grid
        if spec.x.grid:
            ax.grid(spec.x.grid, which="major", axis="x", color=spec.x.grid_color, alpha=spec.x.grid_alpha)
        if spec.y.grid:
            ax.grid(spec.y.grid, which="major", axis="y", color=spec.y.grid_color, alpha=spec.y.grid_alpha)

        if spec.x.grid_minor or spec.y.grid_minor:
            ax.minorticks_on()
            ax.grid(
                True,
                axis="x",
                which="minor",
                color=spec.x.grid_color,
                alpha=spec.x.grid_alpha,
                linestyle=":",
                linewidth=0.5,
            )
            ax.grid(
                True,
                axis="y",
                which="minor",
                color=spec.y.grid_color,
                alpha=spec.y.grid_alpha,
                linestyle=":",
                linewidth=0.5,
            )

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
        self._call(ax, "line", x, y, **kwargs)

    def scatter(self, ax, x, y, **kwargs):
        self._call(ax, "scatter", x, y, **kwargs)

    def errorbar(self, ax, x, y, err, **kwargs):
        self._call(ax, "errorbar", x, y, err, **kwargs)

    def bar(self, ax, x, y, width, bottom=None, **kwargs):
        self._call(ax, "bar", x, y, width=width, bottom=bottom, **kwargs)

    def step(self, ax, x, y, where="pre", **kwargs):
        self._call(ax, "step", x, y, where=where, **kwargs)

    def violin(self, ax, ys, positions, **kwargs):
        return self._call(ax, "violin", ys, positions=positions, **kwargs)

    def text(self, ax, x, y, s, **kwargs):
        return self._call(ax, "text", x, y, s, **kwargs)

    def vertical(self, ax, x, ymin, ymax, **kwargs):
        return self._call(ax, "vertical", x, ymin, ymax, **kwargs)

    def horizontal(self, ax, y, xmin, xmax, **kwargs):
        return self._call(ax, "horizontal", y, xmin, xmax, **kwargs)
