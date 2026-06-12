from __future__ import annotations

from typing import Any

from behaviz.backends.override import Overrider, KwargDict, PlotType


# ---------------------------------------------------------------------------
# Canonical → Bokeh translation table
# ---------------------------------------------------------------------------

_CANON_TO_BOKEH: dict[str, list[str]] = {
    # Generic color — fans out to both line and fill
    "color": ["line_color", "fill_color"],
    "alpha": ["line_alpha", "fill_alpha"],
    # Line-specific
    "linewidth": ["line_width"],
    "line_width": ["line_width"],
    "linestyle": ["line_dash"],
    "linedash": ["line_dash"],
    "line_dash": ["line_dash"],
    "line_color": ["line_color"],
    "line_alpha": ["line_alpha"],
    "line_cap": ["line_cap"],
    "line_join": ["line_join"],
    # Fill-specific
    "fillcolor": ["fill_color"],
    "fill_color": ["fill_color"],
    "edgecolor": ["line_color"],
    "fill_alpha": ["fill_alpha"],
    # Marker / scatter
    "markersize": ["size"],
    "size": ["size"],
    "marker": ["marker"],
    # text
    "ha": ["text_align"],
    "va": ["text_baseline"],
    "fontsize": ["text_font_size"],
    # Label / legend
    "label": ["legend_label"],
    "legend_label": ["legend_label"],
    # Misc
    "zorder": [],  # TODO: level kwargs?
    "capsize": [],  # handled manually in errorbar — silently dropped
}


def _build_call_kwargs_table() -> dict[PlotType, set[str]]:
    """
    Collect the property names accepted at call-time by each Bokeh glyph method.

    We introspect the glyph *model* properties (e.g. ``bokeh.models.glyphs.Line``)
    rather than the ``figure`` method signature (which has ``**kwargs`` and hides
    the actual accepted names).
    """
    from bokeh.models.glyphs import (
        Line,
        Scatter,
        VBar,
        Step,
        Segment,
        Patch,
        Text,
        VSpan,
        HSpan,
        Image,
        VArea,
        Wedge,
        HexTile,
    )

    _glyph_map: dict[PlotType, type] = {
        "line": Line,
        "scatter": Scatter,
        "bar": VBar,
        "step": Step,
        "errorbar": Segment,  # errorbar is drawn as segments in Bokeh
        "violin": Patch,  # violin is drawn as patches in Bokeh
        "text": Text,
        "vertical": VSpan,
        "horizontal": HSpan,
        "image": Image,
        "fill_between": VArea,
        "pie": Wedge,
        "hexbin": HexTile,
    }

    table: dict[PlotType, set[str]] = {}
    for plot_type, glyph_cls in _glyph_map.items():
        table[plot_type] = set(glyph_cls().properties())

    return table


class BokehOverrider(Overrider):
    """
    Overrider for the Bokeh backend.

    Since Bokeh glyph properties are set at call time (passed as keyword
    arguments to ``fig.line()``, ``fig.scatter()``, etc.), there is effectively
    no post-hoc phase for standard glyphs — all valid properties can be passed
    directly.
    """

    CANON_TO_NATIVE = _CANON_TO_BOKEH
    VALID_CALL_KWARGS = _build_call_kwargs_table()

    def apply_post(self, result: Any, post_kwargs: KwargDict) -> None:
        """
        Apply remaining kwargs to the glyph model(s) of the returned renderer(s).

        ``result`` may be:
          - a single ``GlyphRenderer``
          - a list of ``GlyphRenderer``s  (e.g. from errorbar segments)
          - None / other  (ignored)
        """
        if not post_kwargs:
            return

        renderers = self._collect_renderers(result)
        for renderer in renderers:
            glyph = getattr(renderer, "glyph", None)
            if glyph is None:
                continue
            glyph_props = set(glyph.properties())
            for k, v in post_kwargs.items():
                if k in glyph_props:
                    try:
                        setattr(glyph, k, v)
                    except Exception:
                        pass

    @staticmethod
    def _collect_renderers(result: Any) -> list:
        """Flatten result into a list of GlyphRenderers."""
        from bokeh.models import GlyphRenderer

        if result is None:
            return []
        if isinstance(result, GlyphRenderer):
            return [result]
        if isinstance(result, (list, tuple)):
            out = []
            for item in result:
                if isinstance(item, GlyphRenderer):
                    out.append(item)
            return out
        return []


_instance: BokehOverrider | None = None


def get_overrider() -> BokehOverrider:
    global _instance
    if _instance is None:
        _instance = BokehOverrider()
    return _instance
