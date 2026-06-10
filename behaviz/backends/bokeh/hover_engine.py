from __future__ import annotations

from typing import Any

from bokeh.models import HoverTool

from behaviz.backends.hover import HoverEngine


def _field(glyph: Any, *names: str) -> str | None:
    """Return the data-source column a glyph property is bound to, if any.

    When a glyph is built from raw arrays (``fig.scatter(x, y)``) Bokeh creates a
    ColumnDataSource whose columns are named after the glyph properties, and the
    property holds that column name as a string (sometimes wrapped as
    ``{"field": "x"}``).  We use those names to build ``@column`` tooltips that
    snap to real data points.
    """
    if glyph is None:
        return None
    for n in names:
        v = getattr(glyph, n, None)
        if isinstance(v, str):
            return v
        if isinstance(v, dict) and "field" in v:
            return v["field"]
    return None


class BokehHoverEngine(HoverEngine):
    """Adds a native Bokeh ``HoverTool`` scoped to the drawn glyph(s).

    This is the most natural fit of the three backends — Bokeh renders to
    interactive HTML, so hover works out of the box once the tool is attached.
    """

    def attach(self, fig, result: Any, x, y, opts: dict | None = None) -> None:
        renderers = result if isinstance(result, (list, tuple)) else [result]
        renderers = [r for r in renderers if r is not None]
        if not renderers:
            return

        opts = opts or {}
        labels = opts.get("labels") or ("x", "y")
        xlabel, ylabel = labels[0], labels[1]

        custom = opts.get("format")
        if custom:
            tooltips: Any = custom
            point_policy = "snap_to_data"
        else:
            glyph = getattr(renderers[0], "glyph", None)
            xf = _field(glyph, "x", "x0")
            yf = _field(glyph, "y", "top", "y0")
            if xf and yf:
                # Snap to the actual data values of the nearest point.
                xref, yref = "@{%s}{0.00}" % xf, "@{%s}{0.00}" % yf
                point_policy = "snap_to_data"
            else:
                # Fall back to the cursor position in data coordinates.
                xref, yref = "$x{0.00}", "$y{0.00}"
                point_policy = "follow_mouse"
            tooltips = [(xlabel, xref), (ylabel, yref)]

        hover = HoverTool(renderers=renderers, tooltips=tooltips, mode="mouse")
        hover.point_policy = point_policy
        fig.add_tools(hover)
