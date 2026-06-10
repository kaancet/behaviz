from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# ---------------------------------------------------------------------------
# Reserved, opt-in hover keywords
# ---------------------------------------------------------------------------
# Users turn the feature on from any plot call, e.g.
#     bv.plot_scatter(x, y, hover_annotate=True)
#     bv.plot_line(x, y, hover_annotate=True, hover_labels=("Time", "Voltage"))
#
# These keys are stripped from the kwargs *before* they reach the backend's
# overrider/route machinery, so they never leak into a native plot call.
HOVER_KW = "hover_annotate"  # bool — the opt-in switch
HOVER_LABELS_KW = "hover_labels"  # tuple[str, str] — (xlabel, ylabel) shown in tooltip
HOVER_FORMAT_KW = "hover_format"  # str — custom tooltip template (backend-specific)

_RESERVED = (HOVER_KW, HOVER_LABELS_KW, HOVER_FORMAT_KW)

# Plot types that carry scalar (x, y) data and can therefore be annotated.
HOVERABLE: frozenset[str] = frozenset({"line", "scatter", "bar", "step", "errorbar"})


def pop_hover_kwargs(kwargs: dict) -> dict | None:
    """Strip the reserved hover keys out of ``kwargs`` (mutating it in place).

    Returns
    -------
    dict | None
        ``None`` when the user did not opt in, otherwise a small options dict
        ``{"labels": (xlabel, ylabel) | None, "format": str | None}`` that the
        backend hover engine knows how to consume.

    The reserved keys are always removed — even when hover is *disabled* — so a
    stray ``hover_labels`` can never reach a native plot call.
    """
    enabled = bool(kwargs.pop(HOVER_KW, False))
    labels = kwargs.pop(HOVER_LABELS_KW, None)
    fmt = kwargs.pop(HOVER_FORMAT_KW, None)

    if not enabled:
        return None
    return {"labels": labels, "format": fmt}


def extract_xy(args: tuple, kwargs: dict) -> tuple[Any, Any]:
    """Best-effort pull of the x / y data from a renderer ``_call``.

    Backends pass x/y either positionally (``_call(ax, "line", x, y)``) or as
    keywords (``_call(ax, "bar", x=x, top=y)``), so we check both and fall back
    through the handful of native names used across matplotlib/seaborn/bokeh.
    """
    x = args[0] if len(args) >= 1 else kwargs.get("x", kwargs.get("x0"))
    y = args[1] if len(args) >= 2 else kwargs.get("y", kwargs.get("top", kwargs.get("y0")))
    return x, y


class HoverEngine(ABC):
    """Backend-specific 'hover to see values' attacher.

    One concrete subclass lives next to each backend (``hover_engine.py``).
    The renderer owns an instance and calls :meth:`attach` after a glyph/artist
    has been drawn, but only when the user opted in via ``hover_annotate=True``.
    """

    @abstractmethod
    def attach(self, target: Any, result: Any, x: Any, y: Any, opts: dict | None = None) -> None:
        """Wire up hover annotations for a freshly drawn artist/glyph.

        Parameters
        ----------
        target
            The axes (matplotlib/seaborn) or figure (bokeh) being drawn on.
        result
            Whatever the native plot call returned (artist, glyph renderer, …).
        x, y
            The data that was plotted, used to look up values on hover.
        opts
            The dict produced by :func:`pop_hover_kwargs` (``labels`` / ``format``).
        """
        raise NotImplementedError
