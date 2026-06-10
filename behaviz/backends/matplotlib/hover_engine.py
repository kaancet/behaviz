from __future__ import annotations

from typing import Any

import numpy as np

from behaviz.backends.hover import HoverEngine


class _HoverState:
    """Per-axes hover controller.

    A single annotation box and one ``motion_notify_event`` callback are shared
    across every series drawn on the axes, so adding three traces does not stack
    three independent tooltips.  On each mouse move we find the nearest data
    point (in *display* pixels) across all registered series and, if it falls
    within ``pixel_radius``, show its value.
    """

    def __init__(self, ax, pixel_radius: float = 25.0) -> None:
        self.ax = ax
        self.fig = ax.figure
        self.radius = pixel_radius
        self.series: list[dict] = []

        self.annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.4", fc="#ffffe0", ec="0.4", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color="0.4"),
            fontsize=8,
            zorder=10_000,
            annotation_clip=False,
        )
        self.annot.set_visible(False)
        self.cid = self.fig.canvas.mpl_connect("motion_notify_event", self._on_move)

    def add_series(self, x, y, xlabel: str, ylabel: str, fmt: str | None = None) -> None:
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        self.series.append(
            dict(
                x=x,
                y=y,
                xlabel=xlabel,
                ylabel=ylabel,
                fmt=fmt or "{xl} = {x:.3g}\n{yl} = {y:.3g}",
            )
        )

    def _on_move(self, event) -> None:
        if event.inaxes is not self.ax or event.x is None:
            self._hide()
            return

        best = None  # (dist2, x_value, y_value, series)
        for s in self.series:
            if not len(s["x"]):
                continue
            pts = self.ax.transData.transform(np.column_stack([s["x"], s["y"]]))
            d2 = (pts[:, 0] - event.x) ** 2 + (pts[:, 1] - event.y) ** 2
            i = int(np.argmin(d2))
            if best is None or d2[i] < best[0]:
                best = (d2[i], s["x"][i], s["y"][i], s)

        if best is None or best[0] > self.radius**2:
            self._hide()
            return

        _, xv, yv, s = best
        self.annot.xy = (xv, yv)
        self.annot.set_text(s["fmt"].format(xl=s["xlabel"], yl=s["ylabel"], x=xv, y=yv))
        self.annot.set_visible(True)
        self.fig.canvas.draw_idle()

    def _hide(self) -> None:
        if self.annot.get_visible():
            self.annot.set_visible(False)
            self.fig.canvas.draw_idle()


class MatplotlibHoverEngine(HoverEngine):
    """Attaches an interactive 'nearest point' tooltip to a matplotlib axes.

    Note
    ----
    Hover events only fire on an *interactive* matplotlib backend (Qt, TkAgg,
    ``%matplotlib widget`` / ``notebook`` in Jupyter, …).  With the non-interactive
    Agg backend the annotation is created but never triggered — it does not error,
    it simply has nothing to listen to.
    """

    def attach(self, ax, result: Any, x, y, opts: dict | None = None) -> None:
        opts = opts or {}
        labels = opts.get("labels") or ("x", "y")
        xlabel, ylabel = labels[0], labels[1]

        state = getattr(ax, "_behaviz_hover", None)
        if state is None:
            state = _HoverState(ax)
            # Stash on the axes so subsequent series share one annotation/callback.
            ax._behaviz_hover = state

        state.add_series(x, y, xlabel, ylabel, fmt=opts.get("format"))
