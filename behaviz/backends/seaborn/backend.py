from __future__ import annotations
from typing import Literal

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.collections import PolyCollection

from behaviz.backends.matplotlib.backend import MatplotlibRenderer
from behaviz.spec.plot_spec import PlotSpec
from behaviz.backends.seaborn.overrider import SeabornOverrider
from behaviz.backends.seaborn.hover_engine import SeabornHoverEngine
from behaviz.backends.hover import pop_hover_kwargs, extract_xy, HOVERABLE
from behaviz.core.plot_registry import get_plot


class SeabornRenderer(MatplotlibRenderer):
    """seaborn is matplotlib under the hood, so this inherits everything from
    :class:`MatplotlibRenderer` (apply_axis_spec, save/show, and every primitive
    that just calls ``self._call``) and overrides only what genuinely differs:
    theme handling, the sns dispatch in ``_call``, and the plots that need a
    seaborn function (line/scatter/bar/hbar/violin)."""

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
        """``method`` is the canonical plot name; the native seaborn/mpl function
        is looked up separately so ``route()`` gets the canonical key matching the
        VALID_CALL_KWARGS table."""
        hover_opts = pop_hover_kwargs(kwargs)

        plot_f = None
        try:
            native_method = get_plot(method, "seaborn")
            plot_f = getattr(sns, native_method)
        except AttributeError:
            native_method = get_plot(method, "matplotlib")

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
        sns.set_theme(context=self.context, style=self.style, palette=self.palette, font_scale=self.font_scale)

    def make_figure(self, spec: PlotSpec) -> tuple[Figure, Axes]:
        self._apply_theme()  # re-apply in case another renderer changed it
        # Layer a preset's matplotlib style on top of the seaborn theme so dark
        # (and other rcParam) presets take effect. "default" is skipped so it
        # doesn't wipe the theme; the next _apply_theme() resets any leak.
        plt.style.use(["default", spec.figure.style])
        return plt.subplots(figsize=spec.figure.figsize, dpi=spec.figure.dpi)

    # seaborn plotters take x/y as keywords (the sns dispatch pops them); the
    # rest of the primitives are inherited from MatplotlibRenderer unchanged.
    def line(self, ax, x, y, **kwargs):
        self._call(ax, "line", x=x, y=y, **kwargs)

    def scatter(self, ax, x, y, **kwargs):
        self._call(ax, "scatter", x=x, y=y, **kwargs)

    def bar(self, ax, x, y, width=0.8, bottom=None, **kwargs):
        # native_scale=True keeps x numeric (barplot defaults to ordinal categories).
        before = set(map(id, ax.patches))
        self._call(ax, "bar", x=x, y=y, width=width, native_scale=True, **kwargs)
        if bottom is not None:
            self._shift_new_patches(ax, before, x, bottom, axis="y")

    def hbar(self, ax, y, x, height=0.8, left=None, **kwargs):
        before = set(map(id, ax.patches))
        self._call(ax, "hbar", y=y, x=x, height=height, native_scale=True, **kwargs)
        if left is not None:
            self._shift_new_patches(ax, before, x, left, axis="x")

    def violin(self, ax, ys, positions, **kwargs):
        """Draw one violin per position and return ``{"bodies": [...]}``.

        seaborn's ``violinplot`` returns the Axes, not the violin artists, so we
        snapshot the Axes' collections, draw, and collect the newly-added
        ``PolyCollection`` bodies — matching the matplotlib/bokeh return shape so
        composite plots (e.g. rainplot) can post-process them.

        ``native_scale=True`` places violins at real numeric positions; ``inner=None``
        drops the median/quartile box for a clean body (overridable via kwargs).
        """
        df = pd.DataFrame({"x": np.repeat(positions, [len(y) for y in ys]), "y": np.concatenate(ys)})
        kwargs.setdefault("inner", None)
        before = set(ax.collections)
        self._call(ax, "violin", df, x="x", y="y", native_scale=True, **kwargs)
        bodies = [c for c in ax.collections if c not in before and isinstance(c, PolyCollection)]
        return {"bodies": bodies}

    def _shift_new_patches(self, ax, before, positions, offsets, axis):
        # sns.barplot draws from the baseline with no stacked concept, so behaviz's
        # bottom/left offsets are applied by shifting the freshly created patches.
        # axis="y": match each patch by x-centre, shift y (vertical bars);
        # axis="x": match by y-centre, shift x (horizontal). barplot may reorder.
        pos = np.asarray(positions, dtype=float)
        offs = np.broadcast_to(offsets, pos.shape)
        for patch in ax.patches:
            if id(patch) in before:
                continue
            if axis == "y":
                i = int(np.argmin(np.abs(pos - (patch.get_x() + patch.get_width() / 2))))
                patch.set_y(patch.get_y() + float(offs[i]))
            else:
                i = int(np.argmin(np.abs(pos - (patch.get_y() + patch.get_height() / 2))))
                patch.set_x(patch.get_x() + float(offs[i]))
