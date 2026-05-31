from __future__ import annotations

import numpy as np
from typing import Any

from bokeh.plotting import figure
from bokeh.models import (
    LogAxis,
    LinearAxis,
    LogScale,
    LinearScale,
    Range1d,
    FixedTicker,
    NumeralTickFormatter,
    PrintfTickFormatter,
    Label,
    Legend,
    LegendItem,
)

from behaviz.core.renderer import Renderer
from behaviz.backends.bokeh.overrider import BokehOverrider
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import ScaleType
from behaviz.spec.figure_spec import LegendPosition


def _scale_type(scale: ScaleType) -> str:
    """Return the Bokeh scale string for a ScaleType value."""
    return "log" if scale == ScaleType.LOG else "linear"


class BokehRenderer(Renderer):
    name = "bokeh"

    def __init__(self):
        self._ovr = BokehOverrider()

    def _call(self, fig, method: str, *args, **kwargs):
        """Route kwargs, call fig.<method>, apply post-hoc glyph property update."""
        plot_type = {
            "line": "line",
            "scatter": "scatter",
            "vbar": "bar",
            "step": "step",
            "segment": "errorbar",
            "patch": "violin",
        }.get(method, method)
        call_kw, post_kw = self._ovr.route(plot_type, kwargs)
        result = getattr(fig, method)(*args, **call_kw)
        self._ovr.apply_post(result, post_kw)
        return result

    def make_figure(self, spec: PlotSpec) -> tuple[Any, Any]:
        w_px, h_px = self._figsize_to_px(spec.figure.figsize)

        x_axis_type = _scale_type(spec.x.scale)
        y_axis_type = _scale_type(spec.y.scale)

        fig = figure(
            width=w_px,
            height=h_px,
            x_axis_type=x_axis_type,
            y_axis_type=y_axis_type,
            title=spec.title or "",
        )

        fig.grid.grid_line_color = "#c1c1c1"
        fig.grid.grid_line_alpha = 0.6

        return fig, fig

    def get_figure(self, ax: Any) -> Any:
        # ax IS the figure in bokeh
        return ax

    def apply_axis_spec(self, ax: Any, spec: PlotSpec) -> None:

        fig = ax  # ax is the Bokeh figure

        # Title
        if spec.title:
            fig.title.text = spec.title
            fig.title.text_font_size = f"{spec.x.fontsize + 2}pt"

        # Axis labels
        fig.xaxis.axis_label = spec.x.full_label
        fig.yaxis.axis_label = spec.y.full_label
        fig.xaxis.axis_label_text_font_size = f"{spec.x.fontsize}pt"
        fig.yaxis.axis_label_text_font_size = f"{spec.y.fontsize}pt"
        fig.xaxis.major_label_text_font_size = f"{spec.x.fontsize}pt"
        fig.yaxis.major_label_text_font_size = f"{spec.y.fontsize}pt"

        # Limits
        if spec.x.lim:
            fig.x_range = Range1d(*spec.x.lim)
        if spec.y.lim:
            fig.y_range = Range1d(*spec.y.lim)

        # Ticks
        if spec.x.ticks is not None:
            numeric_ticks = (
                list(range(len(spec.x.ticks))) if all(isinstance(t, str) for t in spec.x.ticks) else list(spec.x.ticks)
            )
            fig.xaxis.ticker = FixedTicker(ticks=numeric_ticks)
            if all(isinstance(t, str) for t in spec.x.ticks):
                fig.xaxis.major_label_overrides = dict(zip(numeric_ticks, spec.x.ticks))

        if spec.y.ticks is not None:
            numeric_ticks = (
                list(range(len(spec.y.ticks))) if all(isinstance(t, str) for t in spec.y.ticks) else list(spec.y.ticks)
            )
            fig.yaxis.ticker = FixedTicker(ticks=numeric_ticks)
            if all(isinstance(t, str) for t in spec.y.ticks):
                fig.yaxis.major_label_overrides = dict(zip(numeric_ticks, spec.y.ticks))

        # Tick formatters (printf-style, e.g. "%.2f")
        if spec.x.tick_fmt:
            fig.xaxis.formatter = PrintfTickFormatter(format=spec.x.tick_fmt)
        if spec.y.tick_fmt:
            fig.yaxis.formatter = PrintfTickFormatter(format=spec.y.tick_fmt)

        # Grid
        show_grid = spec.x.grid or spec.y.grid
        fig.xgrid.visible = show_grid
        fig.ygrid.visible = show_grid
        if spec.x.grid_minor or spec.y.grid_minor:
            fig.xgrid.minor_grid_line_color = "#c1c1c1"
            fig.xgrid.minor_grid_line_alpha = 0.4
            # fig.xgrid.minor_grid_line_dash = [4, 4]
            fig.ygrid.minor_grid_line_color = "#c1c1c1"
            fig.ygrid.minor_grid_line_alpha = 0.4
            # fig.ygrid.minor_grid_line_dash = [4, 4]

        # Axis inversion
        if spec.x.invert and not spec.x.lim:
            # Bokeh inversion: set a reversed Range1d after first render isn't
            # easy; best done via x_range with flipped bounds.
            # We rely on the user to set lim themselves for inversion, but
            # provide a helpful hint.
            pass  # TODO: requires data range; advise using spec.with_xlim()

        # Spines (Bokeh calls them "axis line" / border)
        _visible = set(spec.x.spines) | set(spec.y.spines)
        fig.outline_line_color = "#cccccc" if _visible else None

        # Legend
        if spec.show_legend and fig.legend:
            legend = fig.legend[0] if fig.legend else None
            if legend:
                if spec.legend_pos == LegendPosition.OUTSIDE:
                    fig.add_layout(legend, "right")
                elif spec.legend_pos == LegendPosition.UPPER_RIGHT:
                    legend.location = "top_right"
                elif spec.legend_pos == LegendPosition.UPPER_LEFT:
                    legend.location = "top_left"
                elif spec.legend_pos == LegendPosition.LOWER_RIGHT:
                    legend.location = "bottom_right"
                elif spec.legend_pos == LegendPosition.LOWER_LEFT:
                    legend.location = "bottom_left"
                else:
                    legend.location = "top_right"
        elif not spec.show_legend and fig.legend:
            for leg in fig.legend:
                leg.visible = False

        # Annotations
        for ann in spec.annotations:
            label = Label(
                x=ann["x"],
                y=ann["y"],
                text=ann["text"],
                text_font_size=f"{spec.x.fontsize}pt",
                **{
                    k: v
                    for k, v in ann.get("kwargs", {}).items()
                    if k in {"text_color", "text_align", "x_offset", "y_offset"}
                },
            )
            fig.add_layout(label)

        # Post-processing hook – same signature as matplotlib backend
        if spec.post_hook:
            spec.post_hook(ax, spec)

    def line(self, ax, x, y, **kwargs):
        self._call(ax, "line", x, y, **kwargs)

    def scatter(self, ax, x, y, **kwargs):
        self._call(ax, "scatter", x, y, **kwargs)

    def errorbar(self, ax, x, y, err, **kwargs) -> None:
        """
        Bokeh has no native errorbar glyph; we draw it from segments + whiskers.
        err may be:
            shape (N,)    → symmetric ±err
            shape (2, N)  → [lower_err, upper_err] (both positive magnitudes)
        """

        err = np.asarray(err)
        if err.ndim == 1:
            y_lower = y - err
            y_upper = y + err
        else:
            y_lower = y - err[0]
            y_upper = y + err[1]

        # Vertical bars
        self._call(ax, "segment", x0=x, y0=y_lower, x1=x, y1=y_upper, **kwargs)

        # Caps
        # cap_width = (x[1] - x[0]) * 0.15 if len(x) > 1 else 0.1
        # ax.segment(x0=x - cap_width, y0=y_lower, x1=x + cap_width, y1=y_lower, **kw)
        # ax.segment(x0=x - cap_width, y0=y_upper, x1=x + cap_width, y1=y_upper, **kw)

        # Central markers
        self._call(ax, "scatter", x=x, y=y, **kwargs)

    def bar(self, ax, x, y, width, bottom=None, **kwargs):
        bottom = bottom if bottom is not None else np.zeros_like(y)
        self._call(ax, "vbar", x=x, top=y, bottom=bottom, width=width, **kwargs)

    def step(self, ax, x, y, where="pre", **kwargs) -> None:
        """
        Render a step plot.

        Bokeh's `step` glyph uses `mode` instead of `where`:
            matplotlib "pre"  → bokeh "before"
            matplotlib "post" → bokeh "after"
            matplotlib "mid"  → bokeh "center"
        """
        _where_map = {"pre": "before", "post": "after", "mid": "center"}
        kwargs["mode"] = _where_map.get(where, "before")
        self._call(ax, "step", x=x, y=y, **kwargs)

    def violin(self, ax, ys: list, positions, **kwargs):
        """
        Approximate violin via a KDE patch on each position.

        Returns a dict with key 'bodies' (list of patches) so that callers
        like plot_rain can iterate vp['bodies'] – matching the matplotlib
        violinplot return convention.
        """
        from scipy.stats import gaussian_kde

        bodies = []
        for pos, data in zip(positions, ys):
            data = np.asarray(data)
            if len(data) < 2:
                continue
            kde = gaussian_kde(data)
            support = np.linspace(data.min(), data.max(), 200)
            density = kde(support)
            density = density / density.max() * 0.4  # normalise to ±0.4 width

            xs_patch = np.concatenate([pos + density, (pos - density)[::-1]])
            ys_patch = np.concatenate([support, support[::-1]])

            patch = ax.patch(xs_patch, ys_patch, **kwargs)
            bodies.append(patch)

        return {"bodies": bodies}

    @staticmethod
    def _figsize_to_px(figsize: tuple, dpi: int = 96) -> tuple[int, int]:
        """Convert matplotlib-style inch figsize to pixel dimensions."""
        w_in, h_in = figsize
        return int(w_in * dpi), int(h_in * dpi)
