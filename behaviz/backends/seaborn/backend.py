from __future__ import annotations
from typing import Literal

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.collections import PolyCollection

from behaviz.backends.renderer import Renderer
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.figure_spec import LegendPosition
from behaviz.backends.seaborn.overrider import SeabornOverrider
from behaviz.backends.seaborn.hover_engine import SeabornHoverEngine
from behaviz.backends.hover import pop_hover_kwargs, extract_xy, HOVERABLE
from behaviz.core.plot_registry import get_plot


class SeabornRenderer(Renderer):
    name = "seaborn"

    def __init__(
        self,
        context: Literal["paper", "notebook", "talk", "poster"] = "notebook",
        style: Literal["darkgrid", "whitegrid", "dark", "white", "ticks"] = "whitegrid",
        palette: str | list | None = None,
        font_scale: float = 1.0,
    ) -> None:
        self.context = context
        self.style = style
        self.palette = palette
        self.font_scale = font_scale
        self._ovr = SeabornOverrider()
        self._hover = SeabornHoverEngine()

        self._apply_theme()

    def _call(self, ax, method: str, *args, **kwargs):
        """
        ``method`` is always the canonical plot name (e.g. "line", "scatter").
        The native seaborn/mpl function name is looked up separately so that
        ``route()`` always receives the canonical key that matches the
        VALID_CALL_KWARGS table built from ALL_PLOTS.
        """
        # Opt-in hover keys are stripped before routing so they never reach seaborn.
        hover_opts = pop_hover_kwargs(kwargs)

        plot_f = None
        native_method = None
        try:
            native_method = get_plot(method, "seaborn")
            plot_f = getattr(sns, native_method)

        except AttributeError:
            native_method = get_plot(method, "matplotlib")

        # Route using the canonical name so VALID_CALL_KWARGS lookup works.
        call_kw, post_kw = self._ovr.route(method, kwargs)

        if plot_f is not None:
            x = post_kw.pop("x")
            y = post_kw.pop("y")
            result = plot_f(x=x, y=y, *args, ax=ax, **call_kw)
        else:
            result = getattr(ax, native_method)(*args, **call_kw)

        self._ovr.apply_post(result, post_kw)

        if hover_opts is not None and method in HOVERABLE:
            hx, hy = extract_xy(args, kwargs)
            if hx is not None and hy is not None:
                self._hover.attach(ax, result, hx, hy, hover_opts)
        return result

    def _apply_theme(self) -> None:
        sns.set_theme(
            context=self.context,
            style=self.style,
            palette=self.palette,
            font_scale=self.font_scale,
        )

    def make_figure(self, spec: PlotSpec) -> tuple[Figure, Axes]:
        self._apply_theme()  # re-apply in case another renderer changed it
        fig, ax = plt.subplots(
            figsize=spec.figure.figsize,
            dpi=spec.figure.dpi,
        )
        return fig, ax

    def get_figure(self, ax: Axes) -> Figure:
        return ax.get_figure()

    def get_xlims(self, ax):
        return list(ax.get_xlim())

    def get_ylims(self, ax):
        return list(ax.get_ylim())

    def apply_axis_spec(self, ax, spec: PlotSpec) -> None:
        """Apply all AxisSpec and PlotSpec settings to an existing Axes object. Exactly same as matplotlib"""
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
        self._call(ax, "line", x=x, y=y, **kwargs)

    def scatter(self, ax, x, y, **kwargs):
        self._call(ax, "scatter", x=x, y=y, **kwargs)

    def errorbar(self, ax, x, y, err, **kwargs):
        self._call(ax, "errorbar", x, y, err, **kwargs)

    def bar(self, ax, x, y, **kwargs):
        # By default, this function treats one of the variables as categorical and
        # draws data at ordinal positions (0, 1, … n) on the relevant axis.
        # As of version 0.13.0, this can be disabled by setting native_scale=True.
        self._call(ax, "bar", x=x, y=y, native_scale=True, **kwargs)

    def step(self, ax, x, y, where="pre", **kwargs):  # no Seaborn equivalent
        self._call(ax, "step", x, y, where=where, **kwargs)

    def violin(self, ax, ys, positions, **kwargs):
        """Draw one violin per position and return ``{"bodies": [...]}``.

        seaborn's ``violinplot`` returns the Axes, not the violin artists, so we
        snapshot the Axes' collections, draw, and collect the newly-added
        ``PolyCollection`` bodies — matching the return shape of the matplotlib
        and bokeh backends so composite plots (e.g. rainplot) can post-process them.

        ``native_scale=True`` places violins at the real numeric positions (not
        ordinal 0,1,2…) so they align with other layers; ``inner=None`` drops the
        median/quartile box for a clean body (overridable via kwargs).
        """
        df = pd.DataFrame({"x": np.repeat(positions, [len(y) for y in ys]), "y": np.concatenate(ys)})

        kwargs.setdefault("inner", None)
        before = set(ax.collections)
        self._call(ax, "violin", df, x="x", y="y", native_scale=True, **kwargs)
        bodies = [c for c in ax.collections if c not in before and isinstance(c, PolyCollection)]
        return {"bodies": bodies}

    def text(self, ax, x, y, s, **kwargs):
        # fallback to matplotlib for now
        return self._call(ax, "text", x, y, s, **kwargs)

    def vertical(self, ax, x, ymin, ymax, **kwargs):
        return self._call(ax, "vertical", x, ymin, ymax, **kwargs)

    def horizontal(self, ax, y, xmin, xmax, **kwargs):
        return self._call(ax, "horizontal", y, xmin, xmax, **kwargs)

    def image(
        self, ax, data, extent=None, origin="upper", cmap="viridis", vmin=None, vmax=None, aspect="auto", **kwargs
    ):
        return self._call(
            ax, "image", data, extent=extent, origin=origin, cmap=cmap, vmin=vmin, vmax=vmax, aspect=aspect, **kwargs
        )

    def colorbar(self, ax, mappable, cbar_spec):
        fig = ax.get_figure()
        # fraction/pad default to the values that make the bar match the axes height.
        cbar = fig.colorbar(
            mappable, ax=ax, location=cbar_spec.location, fraction=cbar_spec.fraction, pad=cbar_spec.resolved_pad()
        )
        if cbar_spec.label:
            cbar.set_label(cbar_spec.label, fontsize=cbar_spec.fontsize)
        if cbar_spec.ticks is not None:
            cbar.set_ticks(list(cbar_spec.ticks))
        if cbar_spec.tick_fmt:
            cbar.formatter = ticker.FormatStrFormatter(cbar_spec.tick_fmt)
            cbar.update_ticks()
        cbar.ax.tick_params(labelsize=cbar_spec.fontsize)
        return cbar

    def fill_between(self, ax, x, y1, y2=0, **kwargs):
        return self._call(ax, "fill_between", x, y1, y2, **kwargs)

    def pie(self, ax, sizes, labels=None, colors=None, autopct=None, **kwargs):
        return self._call(ax, "pie", sizes, labels=labels, colors=colors, autopct=autopct, **kwargs)

    def hexbin(self, ax, x, y, gridsize=30, cmap="viridis", **kwargs):
        return self._call(ax, "hexbin", x, y, gridsize=gridsize, cmap=cmap, **kwargs)
