from __future__ import annotations
from typing import Literal

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.axes import Axes

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
            print(f"Couldn't find native Seaborn function {method} falling back to matplotlib")

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
            ax.grid(spec.x.grid, which="major", axis="x", color="#c1c1c1")
        if spec.y.grid:
            ax.grid(spec.y.grid, which="major", axis="y", color="#c1c1c1")
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
        df = pd.DataFrame({"x": np.repeat(positions, [len(y) for y in ys]), "y": np.concatenate(ys)})

        self._call(ax, "violin", df, x="x", y="y", **kwargs)

    def text(self, ax, x, y, s, **kwargs):
        # fallback to matplotlib for now
        return self._call(ax, "text", x, y, s, **kwargs)
