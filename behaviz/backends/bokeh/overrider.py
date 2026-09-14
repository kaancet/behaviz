from __future__ import annotations

from typing import Any

from behaviz.backends.override import Overrider, KwargDict, PlotType


# ---------------------------------------------------------------------------
# Canonical → Bokeh translation table
# ---------------------------------------------------------------------------

_CANON_TO_BOKEH: dict[str, list[str]] = {
    # Generic color — fans out to both line and fill
    "c": ["line_color", "fill_color"],
    "color": ["line_color", "fill_color"],
    "alpha": ["line_alpha", "fill_alpha"],
    # Line-specific
    "lw": ["line_width"],
    "linewidth": ["line_width"],
    "line_width": ["line_width"],
    "ls": ["line_dash"],
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
    "edgecolors": ["line_color"],
    "fill_alpha": ["fill_alpha"],
    "markerfacecolor": ["fill_color"],
    # Marker / scatter
    "s": ["size"],
    "markersize": ["size"],
    "size": ["size"],
    "linewidths": ["line_width"],
    "marker": ["marker"],
    # Hatch
    "hatch": ["hatch_pattern"],
    # text
    "ha": ["text_align"],
    "va": ["text_baseline"],
    "fontsize": ["text_font_size"],
    "rotation": ["angle"],
    # Label / legend
    "label": ["legend_label"],
    "legend_label": ["legend_label"],
    # Misc
    "zorder": [],  # TODO: level kwargs?
    "capsize": [],  # handled manually in errorbar — silently dropped
}

# Canonical → Bokeh translation table
# ---------------------------------------------------------------------------

# matplotlib's shorthand linestyles → bokeh's named dash patterns. Bokeh's own
# names ("solid", "dashed", "dotted", "dashdot", "dotdash") pass through as-is.
_MPL_TO_BOKEH_DASH: dict[str, str] = {
    "-": "solid",
    "--": "dashed",
    ":": "dotted",
    "-.": "dashdot",
}


_MPL_SINGLE_LETTER_COLORS: dict[str, str] = {
    "b": "blue",
    "g": "green",
    "r": "red",
    "c": "cyan",
    "m": "magenta",
    "y": "yellow",
    "k": "black",
    "w": "white",
}

_COLOR_KEYS = {"color", "line_color", "fill_color", "text_color"}


def _to_bokeh_color(value: Any) -> Any:
    """Translate matplotlib single-letter color codes to CSS names."""
    if isinstance(value, str):
        return _MPL_SINGLE_LETTER_COLORS.get(value, value)
    return value


def _to_bokeh_dash(value: Any) -> Any:
    """Translate a matplotlib linestyle value into what ``line_dash`` expects."""
    if isinstance(value, str):
        return _MPL_TO_BOKEH_DASH.get(value, value)
    if isinstance(value, (tuple, list)):
        # mpl dash tuples: (offset, (on, off, ...)) — bokeh has no offset, so
        # keep the on/off pattern; flat numeric sequences map directly.
        if len(value) == 2 and isinstance(value[1], (tuple, list)):
            return [int(v) for v in value[1]]
        return [int(v) for v in value]
    return value


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
        HBar,
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
        "segment": Segment,
        "bar": VBar,
        "hbar": HBar,
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

    # Legend kwargs are accepted by the figure glyph *methods* (e.g. fig.line)
    # but are not glyph-model properties, so they must be whitelisted explicitly
    # or they would be filtered out of the call and the legend never built.
    _METHOD_LEVEL = {"legend_label", "legend_group", "legend_field"}

    table: dict[PlotType, set[str]] = {}
    for plot_type, glyph_cls in _glyph_map.items():
        table[plot_type] = set(glyph_cls().properties()) | _METHOD_LEVEL

        # Composite flow plots draw a precomputed layout directly (no single glyph),
    # so they route no call-kwargs — but must be present for registry validation.
    table["sankey"] = set()
    table["alluvial"] = set()

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

    def _translate(self, kwargs: KwargDict) -> KwargDict:
        """Key translation from the base class, plus value translation for
        ``line_dash`` and single-letter matplotlib color codes."""
        out = super()._translate(kwargs)
        if "line_dash" in out:
            out["line_dash"] = _to_bokeh_dash(out["line_dash"])
        for k in _COLOR_KEYS & out.keys():
            out[k] = _to_bokeh_color(out[k])
        return out

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
