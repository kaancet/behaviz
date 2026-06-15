"""Backend-agnostic categorical colors for ``group``/``hue`` series.

Colors are hex strings, which every backend accepts, so one palette definition
serves matplotlib, seaborn and bokeh. Built from matplotlib's qualitative
colormaps (``tab10``/``tab20``) so it looks the same everywhere.
"""

from __future__ import annotations

from typing import Any, Sequence


def categorical_palette(n: int) -> list[str]:
    """Return ``n`` distinct hex colors, cycling once more than 20 are needed.

    Uses ``tab10`` for up to 10 categories and ``tab20`` for up to 20; beyond
    that the chosen base cycles (with a warning left to callers, since repeats
    are usually a sign of too many categories to distinguish by color anyway).
    """
    import matplotlib

    base = "tab10" if n <= 10 else "tab20"
    size = 10 if n <= 10 else 20
    cm = matplotlib.colormaps[base]
    return [matplotlib.colors.to_hex(cm(i % size)) for i in range(n)]


def resolve_palette(categories: Sequence[Any], palette: Any = None) -> dict[Any, str]:
    """Map each category to a hex color.

    Parameters
    ----------
    categories
        Ordered, unique category values (the legend/draw order).
    palette
        - ``None``  → an automatic :func:`categorical_palette`.
        - ``list``/``tuple`` → colors zipped to ``categories`` in order (cycled
          if shorter).
        - ``dict``  → explicit ``{category: color}``; any category missing from
          the dict falls back to the automatic palette.
    """
    cats = list(categories)
    if palette is None:
        return dict(zip(cats, categorical_palette(len(cats))))

    if isinstance(palette, dict):
        auto = categorical_palette(len(cats))
        return {c: palette.get(c, auto[i]) for i, c in enumerate(cats)}

    if isinstance(palette, (list, tuple)):
        colors = list(palette)
        if not colors:
            return dict(zip(cats, categorical_palette(len(cats))))
        return {c: colors[i % len(colors)] for i, c in enumerate(cats)}

    raise TypeError(f"palette must be None, a list, or a dict, got {type(palette).__name__}.")
