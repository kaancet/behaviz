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

from behaviz.backends.renderer import Renderer
from behaviz.backends.bokeh.overrider import BokehOverrider
from behaviz.backends.bokeh.hover_engine import BokehHoverEngine
from behaviz.backends.hover import pop_hover_kwargs, extract_xy, HOVERABLE
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import ScaleType
from behaviz.spec.figure_spec import LegendPosition
from behaviz.core.plot_registry import get_plot


def _scale_type(scale: ScaleType) -> str:
    """Return the Bokeh scale string for a ScaleType value."""
    return "log" if scale == ScaleType.LOG else "linear"


class BokehRenderer(Renderer):
    name = "bokeh"

    def __init__(self):
        self._ovr = BokehOverrider()
        self._hover = BokehHoverEngine()

    def _call(self, fig, method: str, *args, **kwargs):
        """Route kwargs, call fig.<method>, apply post-hoc glyph property update."""
        # Opt-in hover keys are stripped before routing so they never reach Bokeh.
        hover_opts = pop_hover_kwargs(kwargs)

        native_method = get_plot(method, "bokeh")
        call_kw, post_kw = self._ovr.route(method, kwargs)
        result = getattr(fig, native_method)(*args, **call_kw)
        self._ovr.apply_post(result, post_kw)

        if hover_opts is not None and method in HOVERABLE:
            x, y = extract_xy(args, kwargs)
            if x is not None and y is not None:
                self._hover.attach(fig, result, x, y, hover_opts)
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
        if not spec.x.grid:
            fig.xgrid.grid_line_color = None
        else:
            fig.xgrid.grid_line_color = spec.x.grid_color
            fig.xgrid.grid_line_alpha = spec.x.grid_alpha

        if not spec.y.grid:
            fig.ygrid.grid_line_color = None
        else:
            fig.ygrid.grid_line_color = spec.y.grid_color
            fig.ygrid.grid_line_alpha = spec.y.grid_alpha

        if spec.x.grid_minor:
            fig.xgrid.minor_grid_line_color = spec.x.grid_color
            fig.xgrid.minor_grid_line_alpha = spec.x.grid_alpha

        if spec.y.grid_minor:
            fig.ygrid.minor_grid_line_color = spec.y.grid_color
            fig.ygrid.minor_grid_line_alpha = spec.y.grid_alpha

        return fig, fig

    def get_figure(self, ax: Any) -> Any:
        # ax IS the figure in bokeh
        return ax

    def save(self, fig, path, **kwargs) -> str:
        import os

        from behaviz.core.errors import BehavizSaveError

        ext = os.path.splitext(os.fspath(path))[1].lower()

        if ext in (".html", ".htm"):
            from bokeh.io import save as bokeh_save
            from bokeh.resources import CDN

            title = (fig.title.text if fig.title and fig.title.text else None) or "behaviz"
            # Default to CDN resources so the standalone HTML stays small and we
            # avoid bokeh's "no resources supplied" warning; caller can override.
            kwargs.setdefault("resources", CDN)
            bokeh_save(fig, filename=os.fspath(path), title=title, **kwargs)
            return os.fspath(path)

        if ext == ".png":
            from bokeh.io import export_png

            try:
                export_png(fig, filename=os.fspath(path), **kwargs)
            except (ImportError, RuntimeError) as exc:
                raise BehavizSaveError(
                    "PNG export on the bokeh backend needs the optional export "
                    "dependencies (`pip install selenium pillow` plus a browser "
                    "driver such as geckodriver/chromedriver). Save to .html for "
                    "interactive output that needs no extra dependencies."
                ) from exc
            return os.fspath(path)

        if ext == ".svg":
            from bokeh.io import export_svg

            fig.output_backend = "svg"
            try:
                export_svg(fig, filename=os.fspath(path), **kwargs)
            except (ImportError, RuntimeError) as exc:
                raise BehavizSaveError(
                    "SVG export on the bokeh backend needs the optional export "
                    "dependencies (`pip install selenium` plus a browser driver). "
                    "Save to .html for interactive output that needs no extra "
                    "dependencies."
                ) from exc
            return os.fspath(path)

        raise BehavizSaveError(
            f"Unsupported file format '{ext or path}' for the bokeh backend. "
            "Supported: .html (interactive), .png and .svg (need export deps)."
        )

    def show(self, fig) -> None:
        import sys

        from bokeh.io import show as bokeh_show

        if "ipykernel" in sys.modules:
            from bokeh.io import output_notebook

            output_notebook(hide_banner=True)
        bokeh_show(fig)

    def get_xlims(self, ax):
        return [ax.x_range.start, ax.x_range.end]

    def get_ylims(self, ax):
        return [ax.y_range.start, ax.y_range.end]

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
        Bokeh has no native errorbar glyph; we compose it from a connecting
        line, segments (error lines), dash markers (caps) and scatter centres.

        err may be:
            shape (N,)    → symmetric ±err
            shape (2, N)  → [lower_err, upper_err] (both positive magnitudes)

        Override routing mirrors matplotlib's ``ax.errorbar``:
            linewidth / lw → the connecting data line (0 hides it); also the
                             error lines unless ``elinewidth`` overrides
            elinewidth     → the error lines only
            ecolor         → the error lines + caps (defaults to ``color``)
            capsize        → cap length in px (caps are 2*capsize wide, as mpl)
            capthick       → cap line width (defaults to the error-line width)
        """

        err = np.asarray(err)
        if err.ndim == 1:
            y_lower = y - err
            y_upper = y + err
        else:
            y_lower = y - err[0]
            y_upper = y + err[1]

        linewidth = kwargs.pop("linewidth", kwargs.pop("lw", None))
        elinewidth = kwargs.pop("elinewidth", linewidth)
        ecolor = kwargs.pop("ecolor", kwargs.get("color"))
        capsize = kwargs.pop("capsize", None)
        capthick = kwargs.pop("capthick", elinewidth)

        # Connecting line through the data points (matplotlib draws one by
        # default; linewidth=0 hides it)
        if linewidth is None or linewidth > 0:
            line_kw = dict(kwargs)
            if linewidth is not None:
                line_kw["line_width"] = linewidth
            self._call(ax, "line", x, y, **line_kw)

        # Vertical error lines
        err_kw = dict(kwargs)
        if ecolor is not None:
            err_kw["color"] = ecolor
        if elinewidth is not None:
            err_kw["line_width"] = elinewidth
        self._call(ax, "errorbar", x0=x, y0=y_lower, x1=x, y1=y_upper, **err_kw)

        # Caps: horizontal "dash" markers sized in px, like matplotlib's cap
        # markers (which are drawn 2*capsize wide)
        if capsize:
            cap_kw = dict(err_kw)
            cap_kw.pop("line_width", None)
            cap_kw["size"] = 2 * capsize
            if capthick is not None:
                cap_kw["line_width"] = capthick
            self._call(
                ax,
                "scatter",
                x=np.concatenate([np.asarray(x), np.asarray(x)]),
                y=np.concatenate([y_lower, y_upper]),
                marker="dash",
                **cap_kw,
            )

    def bar(self, ax, x, y, width, bottom=None, **kwargs):
        # behaviz bar semantics follow matplotlib: y is the bar *height*
        # measured from `bottom`, but bokeh's vbar wants absolute top/bottom.
        bottom = np.zeros_like(y, dtype=float) if bottom is None else np.broadcast_to(bottom, np.shape(y))
        self._call(ax, "bar", x=x, top=np.asarray(y) + bottom, bottom=bottom, width=width, **kwargs)

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

        pop_hover_kwargs(kwargs)

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

    def text(self, ax, x, y, s, **kwargs):
        kwargs = {k: f"{v}px" if k.endswith("font_size") else v for k, v in kwargs.items()}
        return self._call(ax, "text", x, y, [s], **kwargs)

    def vertical(self, ax, x, ymin, ymax, **kwargs):
        return self._call(ax, "vertical", x=x, **kwargs)

    def horizontal(self, ax, y, xmin, xmax, **kwargs):
        return self._call(ax, "horizontal", y=y, **kwargs)

    def image(self, ax, data, extent=None, origin="upper", cmap="viridis", vmin=None, vmax=None, **kwargs):
        """Render a 2-D scalar array via Bokeh's ``image`` glyph.

        Bokeh draws rows bottom-up and needs an explicit colour mapper, so we
        flip for ``origin="upper"`` (to match matplotlib) and build a
        ``LinearColorMapper`` from a palette derived from the matplotlib colormap.
        """
        from bokeh.models import LinearColorMapper

        data = np.asarray(data, dtype=float)
        if data.ndim != 2:
            raise ValueError(f"The bokeh backend currently supports 2-D scalar images only, got shape {data.shape}.")

        h, w = data.shape
        x0, x1, y0, y1 = (0, w, 0, h) if extent is None else extent
        # matplotlib origin="upper" puts row 0 at the top; bokeh draws bottom-up.
        img = data if origin == "lower" else np.flipud(data)

        low = float(np.nanmin(data)) if vmin is None else vmin
        high = float(np.nanmax(data)) if vmax is None else vmax
        mapper = LinearColorMapper(palette=self._mpl_cmap_to_palette(cmap), low=low, high=high)

        call_kw, post_kw = self._ovr.route("image", kwargs)
        renderer = ax.image(image=[img], x=x0, y=y0, dw=x1 - x0, dh=y1 - y0, color_mapper=mapper, **call_kw)
        self._ovr.apply_post(renderer, post_kw)
        return renderer

    def colorbar(self, ax, mappable, cbar_spec):
        import warnings
        from bokeh.models import ColorBar, FixedTicker, PrintfTickFormatter

        mapper = self._color_mapper_of(mappable)
        if mapper is None:
            warnings.warn("No colour mapper found on the glyph; skipping bokeh colorbar.", stacklevel=2)
            return None

        _loc = {"top": "above", "bottom": "below", "right": "right", "left": "left"}
        cbar = ColorBar(
            color_mapper=mapper,
            title=cbar_spec.label,
            title_text_font_size=f"{cbar_spec.fontsize}pt",
            major_label_text_font_size=f"{cbar_spec.fontsize}pt",
        )
        if cbar_spec.ticks is not None:
            cbar.ticker = FixedTicker(ticks=list(cbar_spec.ticks))
        if cbar_spec.tick_fmt:
            cbar.formatter = PrintfTickFormatter(format=cbar_spec.tick_fmt)
        ax.add_layout(cbar, _loc.get(cbar_spec.location, "right"))
        return cbar

    def fill_between(self, ax, x, y1, y2=0, **kwargs):
        return self._call(ax, "fill_between", x=x, y1=y1, y2=y2, **kwargs)

    def pie(self, ax, sizes, labels=None, colors=None, autopct=None, **kwargs):
        """Pie via wedge glyphs. Slice labels are drawn inside the wedges (Bokeh
        has no native pie); ``autopct`` is not supported and is ignored."""
        sizes = np.asarray(sizes, dtype=float)
        ends = np.cumsum(sizes) / sizes.sum() * 2 * np.pi
        starts = np.concatenate([[0.0], ends[:-1]])
        if colors is None:
            colors = self._category_palette(len(sizes))

        renderers = []
        for i in range(len(sizes)):
            renderers.append(
                ax.wedge(
                    x=0,
                    y=0,
                    radius=0.8,
                    start_angle=starts[i],
                    end_angle=ends[i],
                    fill_color=colors[i],
                    line_color="white",
                )
            )
            if labels is not None:
                mid = (starts[i] + ends[i]) / 2
                ax.text(
                    x=[0.5 * np.cos(mid)],
                    y=[0.5 * np.sin(mid)],
                    text=[str(labels[i])],
                    text_align="center",
                    text_baseline="middle",
                )
        ax.match_aspect = True
        ax.axis.visible = False
        ax.grid.visible = False
        return renderers

    def hexbin(self, ax, x, y, gridsize=30, cmap="viridis", **kwargs):
        """2-D histogram via Bokeh's hexbin (HexTile glyph), colour-mapped by count."""
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        span = (x.max() - x.min()) if x.size > 1 else 1.0
        size = span / gridsize if gridsize else span
        ax.match_aspect = True
        result = ax.hexbin(x, y, size=size, palette=self._mpl_cmap_to_palette(cmap))
        # bokeh's hexbin returns either a GlyphRenderer or (renderer, bins)
        return result[0] if isinstance(result, tuple) else result

    @staticmethod
    def _mpl_cmap_to_palette(cmap, n: int = 256) -> list[str]:
        """Convert a matplotlib colormap (name or object) to a Bokeh hex palette.

        Lets ``cmap="viridis"`` mean the same thing on every backend without users
        needing to learn Bokeh palette names.
        """
        import matplotlib

        cm = matplotlib.colormaps[cmap] if isinstance(cmap, str) else cmap
        return [matplotlib.colors.to_hex(cm(i / (n - 1))) for i in range(n)]

    @staticmethod
    def _category_palette(n: int) -> list[str]:
        """``n`` distinct hex colours from matplotlib's ``tab10`` cycle (for pies)."""
        """``n`` distinct hex colours (shared categorical palette; used by pies)."""
        from behaviz.core.palette import categorical_palette

        return categorical_palette(n)

    @staticmethod
    def _color_mapper_of(mappable):
        """Find a colour mapper on a glyph renderer (image's color_mapper, or a
        ``linear_cmap`` transform on a glyph's fill_color, as hexbin uses)."""
        glyph = getattr(mappable, "glyph", None)
        if glyph is None:
            return None
        cm = getattr(glyph, "color_mapper", None)
        if cm is not None:
            return cm
        # A colour-mapped fill (e.g. hexbin's linear_cmap) carries the mapper as a
        # `transform`, on either a Field object or a plain dict.
        fill = getattr(glyph, "fill_color", None)
        transform = getattr(fill, "transform", None)
        if transform is not None:
            return transform
        if isinstance(fill, dict):
            return fill.get("transform")
        return None

    @staticmethod
    def _figsize_to_px(figsize: tuple, dpi: int = 96) -> tuple[int, int]:
        """Convert matplotlib-style inch figsize to pixel dimensions."""
        w_in, h_in = figsize
        return int(w_in * dpi), int(h_in * dpi)
