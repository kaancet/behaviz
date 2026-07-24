import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from behaviz.backends.renderer import Renderer
from behaviz.backends._save import save_matplotlib
from behaviz.backends.matplotlib.overrider import MatplotlibOverrider
from behaviz.backends._legend import dedup_legend as _dedup_legend
from behaviz.backends.matplotlib.hover_engine import MatplotlibHoverEngine
from behaviz.backends.hover import pop_hover_kwargs, extract_xy, HOVERABLE
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.figure_spec import LegendPosition
from behaviz.core.plot_registry import get_plot
from behaviz.core.scales import log_decade_ticks, symlog_decade_ticks


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
        # plt.style.use is global and cumulative, so to prevent leaking
        # "default" first resets every rcParam so one spec's colours/cycle
        # never leak into the next figure.
        plt.style.use(["default", spec.figure.style])
        fig, ax = plt.subplots(figsize=spec.figure.figsize, dpi=spec.figure.dpi)
        return fig, ax

    def get_figure(self, ax) -> plt.Figure:
        return ax.get_figure()

    def make_grid(
        self,
        spec: PlotSpec,
        placements,
        nrows: int,
        ncols: int,
        *,
        width_ratios=None,
        height_ratios=None,
        sharex: bool = False,
        sharey: bool = False,
        wspace=None,
        hspace=None,
        suptitle=None,
    ):
        plt.style.use(["default", spec.figure.style])
        fig = plt.figure(figsize=spec.figure.figsize, dpi=spec.figure.dpi)
        gs = fig.add_gridspec(
            nrows,
            ncols,
            width_ratios=width_ratios,
            height_ratios=height_ratios,
            wspace=wspace,
            hspace=hspace,
        )
        # Explicit ratios/spacing mean the caller owns the layout: tight_layout
        # would override them (and warns that it can't handle shared/spanning axes).
        if any(v is not None for v in (width_ratios, height_ratios, wspace, hspace)):
            fig._behaviz_manual_spacing = True

        axes: dict = {}
        first = None
        for p in placements:
            share = {}
            if first is not None:  # share against the first panel created
                if sharex:
                    share["sharex"] = first
                if sharey:
                    share["sharey"] = first
            ax = fig.add_subplot(gs[p.row : p.row + p.rowspan, p.col : p.col + p.colspan], **share)
            axes[p.name] = ax
            first = first if first is not None else ax
        if suptitle:
            fig.suptitle(suptitle)
        return fig, axes

    def make_inset(self, parent_ax, bounds, spec: PlotSpec = None):
        ax = parent_ax.inset_axes(bounds)
        if spec is not None:
            self.apply_axis_spec(ax, spec)
        return ax

    def shared_colorbar(self, fig, axes, mappable=None, **kwargs):
        if mappable is None:
            raise ValueError("shared_colorbar needs a `mappable` (e.g. the return of plot_image).")
        return fig.colorbar(mappable, ax=list(axes), **kwargs)

    def set_layout_engine(self, fig, engine: str) -> None:
        fig.set_layout_engine(engine)

    def save(self, fig, path, **kwargs) -> str:
        return save_matplotlib(fig, path, **kwargs)

    def show(self, fig) -> None:
        plt.show()

    def get_xlims(self, ax):
        return list(ax.get_xlim())

    def get_ylims(self, ax):
        return list(ax.get_ylim())

    def apply_axis_spec(self, ax, spec: PlotSpec) -> None:
        """Apply all AxisSpec and PlotSpec settings to an existing Axes object."""
        # Backgrounds
        if spec.figure.face_color:
            ax.get_figure().set_facecolor(spec.figure.face_color)
        if spec.figure.axes_color:
            ax.set_facecolor(spec.figure.axes_color)

        # Labels (text_color tints labels+title+ticks; font_family sets the face)
        txt = {}
        if spec.text_color:
            txt["color"] = spec.text_color
        if spec.figure.font_family:
            txt["fontfamily"] = spec.figure.font_family
        ax.set_xlabel(spec.x.full_label, fontsize=spec.x.fontsize, **txt)
        ax.set_ylabel(spec.y.full_label, fontsize=spec.y.fontsize, **txt)
        if spec.title:
            tfs = spec.title_fontsize if spec.title_fontsize is not None else spec.x.fontsize + 2
            ax.set_title(spec.title, fontsize=tfs, **txt)
        if spec.figure.font_family:
            for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                lbl.set_fontfamily(spec.figure.font_family)

        # Tick marks: direction, length/width (fall back to spine width), colour
        for axis, asp in (("x", spec.x), ("y", spec.y)):
            tp = {
                "axis": axis,
                "which": "major",
                "labelsize": asp.fontsize,
                "direction": asp.tick_dir,
                "length": asp.tick_length if asp.tick_length is not None else asp.spine_width * 3,
                "width": asp.tick_width if asp.tick_width is not None else asp.spine_width,
            }
            if asp.tick_color:
                tp["color"] = asp.tick_color
            if spec.text_color:
                tp["labelcolor"] = spec.text_color
            if asp.tick_sides is not None:
                sides = ("bottom", "top") if axis == "x" else ("left", "right")
                tp.update({side: side in asp.tick_sides for side in sides})
            ax.tick_params(**tp)

        # Scales
        ax.set_xscale(spec.x.scale)
        ax.set_yscale(spec.y.scale)

        # Limits
        if spec.x.lim:
            ax.set_xlim(*spec.x.lim)
        if spec.y.lim:
            ax.set_ylim(*spec.y.lim)

        # Log axis whose limits sit inside one decade: snap to decades so ticks show
        _decade_fn = {"log": log_decade_ticks, "symlog": symlog_decade_ticks}
        for asp, get_lim, set_lim, mpl_axis in (
            (spec.x, ax.get_xlim, ax.set_xlim, ax.xaxis),
            (spec.y, ax.get_ylim, ax.set_ylim, ax.yaxis),
        ):
            if asp.ticks is None and asp.scale in _decade_fn:
                snap = _decade_fn[asp.scale](*get_lim())
                if snap:
                    new_lo, new_hi, majors, minors = snap
                    set_lim(new_lo, new_hi)
                    mpl_axis.set_major_locator(ticker.FixedLocator(majors))
                    mpl_axis.set_minor_locator(ticker.FixedLocator(minors))

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

        # spines (visibility + width + colour; left/right take y's, top/bottom x's)
        for s in ax.spines:
            visible = s in spec.x.spines and s in spec.y.spines
            ax.spines[s].set_visible(visible)
            if visible:
                asp = spec.y if s in ("left", "right") else spec.x
                ax.spines[s].set_linewidth(asp.spine_width)
                if asp.spine_color:
                    ax.spines[s].set_edgecolor(asp.spine_color)
                if asp.spine_offset:
                    ax.spines[s].set_position(("outward", asp.spine_offset))
                if asp.spine_trim:  # clip spine to the outermost ticks in view (sns.despine trim)
                    axis_obj, lims = (ax.yaxis, ax.get_ylim()) if s in ("left", "right") else (ax.xaxis, ax.get_xlim())
                    locs = [t for t in axis_obj.get_majorticklocs() if min(lims) <= t <= max(lims)]
                    if locs:
                        ax.spines[s].set_bounds(min(locs), max(locs))

        # Invert
        if spec.x.invert:
            ax.invert_xaxis()
        if spec.y.invert:
            ax.invert_yaxis()

        # Grid
        if spec.x.grid:
            ax.grid(
                True,
                which="major",
                axis="x",
                color=spec.x.grid_color,
                alpha=spec.x.grid_alpha,
                linestyle=spec.x.grid_style,
                linewidth=spec.x.grid_width,
            )
        if spec.y.grid:
            ax.grid(
                True,
                which="major",
                axis="y",
                color=spec.y.grid_color,
                alpha=spec.y.grid_alpha,
                linestyle=spec.y.grid_style,
                linewidth=spec.y.grid_width,
            )

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

        # Legend (deduplicated by label — grouped/hued plots can repeat a label
        # across artists, e.g. every rectangle of a bar container)
        if spec.show_legend:
            handles, labels = _dedup_legend(ax.get_legend_handles_labels())
            leg_kw = {"fontsize": spec.legend_fontsize} if spec.legend_fontsize else {}
            if spec.legend_pos == LegendPosition.OUTSIDE:
                ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0, **leg_kw)
            else:
                ax.legend(handles, labels, loc=spec.legend_pos.value, **leg_kw)

        # Annotations
        for ann in spec.annotations:
            ax.annotate(
                ann["text"],
                xy=(ann["x"], ann["y"]),
                xytext=(ann["x"], ann["y"]),
                **ann.get("kwargs", {}),
            )

        # An explicit layout engine (bv.grid(layout=...)) owns the spacing —
        # calling tight_layout() on top of it overrides it and warns.
        fig_ = ax.get_figure()
        auto_layout = type(fig_.get_layout_engine()).__name__ in ("NoneType", "PlaceHolderLayoutEngine")
        if spec.figure.tight and auto_layout and not getattr(fig_, "_behaviz_manual_spacing", False):
            fig_.tight_layout()

        # Post-processing hook
        if spec.post_hook:
            spec.post_hook(ax, spec)

    def line(self, ax, x, y, **kwargs):
        self._call(ax, "line", x, y, **kwargs)

    def scatter(self, ax, x, y, **kwargs):
        self._call(ax, "scatter", x, y, **kwargs)

    def errorbar(self, ax, x, y, xerr=None, yerr=None, **kwargs):
        self._call(ax, "errorbar", x, y, xerr=xerr, yerr=yerr, **kwargs)

    def bar(self, ax, x, y, width, bottom=None, **kwargs):
        self._call(ax, "bar", x, y, width=width, bottom=bottom, **kwargs)

    def hbar(self, ax, y, x, height, left=None, **kwargs):
        self._call(ax, "hbar", y, x, height=height, left=left, **kwargs)

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

    def image(
        self, ax, data, extent=None, origin="upper", cmap="viridis", vmin=None, vmax=None, aspect="auto", **kwargs
    ):
        # aspect="auto" makes a data heatmap fill the axes (matplotlib's imshow
        # default of "equal" letterboxes it, which also leaves the colorbar
        # taller than the image). Pass aspect="equal" for square pixels.
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

    def sankey(self, ax, layout, **kwargs):
        self._draw_flows(ax, layout, **kwargs)

    def alluvial(self, ax, layout, **kwargs):
        self._draw_flows(ax, layout, **kwargs)

    def _draw_flows(self, ax, layout, flow_alpha: float = 0.5, **kwargs):
        """Draw a precomputed FlowLayout: bezier ribbons + node rectangles + edge labels."""
        from matplotlib.patches import Rectangle

        for r in layout.ribbons:
            ax.fill(r.xs, r.ys, color=r.color, alpha=flow_alpha, linewidth=0.5, edgecolor=r.color, zorder=1)
        for n in layout.nodes:
            ax.add_patch(
                Rectangle(
                    (n.x0, n.y0),
                    n.x1 - n.x0,
                    n.y1 - n.y0,
                    facecolor=n.color,
                    edgecolor="white",
                    linewidth=1.5,
                    zorder=2,
                )
            )
            if n.first:
                ax.text(n.x0 - 0.03, (n.y0 + n.y1) / 2, n.label, ha="right", va="center", fontsize=9, zorder=3)
            elif n.last:
                ax.text(n.x1 + 0.03, (n.y0 + n.y1) / 2, n.label, ha="left", va="center", fontsize=9, zorder=3)

        xs = [n.x0 for n in layout.nodes] + [n.x1 for n in layout.nodes]
        ys = [n.y0 for n in layout.nodes] + [n.y1 for n in layout.nodes]
        if xs:
            span = max(ys) - min(ys) or 1.0
            ax.set_xlim(min(xs) - 0.5, max(xs) + 0.5)
            ax.set_ylim(min(ys) - 0.05 * span, max(ys) + 0.05 * span)
        ax.axis("off")
