from __future__ import annotations

import inspect
from collections.abc import Sequence, Mapping
from typing import Any

import matplotlib.axes
import matplotlib.pyplot as plt
from matplotlib.artist import ArtistInspector

from behaviz.backends.override import Overrider, KwargDict, PlotType
from behaviz.core.plot_registry import ALL_PLOTS


_CANON_TO_MPL: dict[str, list[str]] = {
    # color
    "color": ["color"],
    "fillcolor": ["facecolor"],
    "edgecolor": ["edgecolor"],
    # line
    "linewidth": ["linewidth"],
    "linestyle": ["linestyle"],
    "linedash": ["linestyle"],
    "line_width": ["linewidth"],  # Bokeh-style alias → mpl native
    "line_color": ["color"],
    "line_dash": ["linestyle"],
    "line_alpha": ["alpha"],
    # marker / scatter
    "markersize": ["markersize"],
    "marker": ["marker"],
    "markerfacecolor": ["markerfacecolor"],
    "markeredgecolor": ["markeredgecolor"],
    "size": ["markersize"],  # Bokeh-style alias
    "fill_color": ["facecolor"],
    "fill_alpha": ["alpha"],
    # label / legend
    "label": ["label"],
    "legend_label": ["label"],  # Bokeh-style alias
    # misc
    "alpha": ["alpha"],
    "zorder": ["zorder"],
    "capsize": ["capsize"],
}


def _build_call_kwargs_table() -> dict[PlotType, set[str]]:
    """
    For each supported plot type, collect the parameters that the matplotlib
    Axes method accepts at call time (from its signature).

    This replaces get_valid_call_kwargs's per-call inspect.signature
    call with a one-time table built at import.
    """
    _methods = {name: plot.backend_methods["matplotlib"] for name, plot in ALL_PLOTS.items()}

    table: dict[PlotType, set[str]] = {}
    for plot_type, mpl_method in _methods.items():
        fn = getattr(matplotlib.axes.Axes, mpl_method, None)
        if fn is None:  # composite plot (e.g. sankey) with no native Axes method
            table[plot_type] = set()
            continue
        sig = inspect.signature(fn)
        table[plot_type] = set(sig.parameters.keys()) - {"self"}
    return table


def _build_artist_kwargs_table() -> dict[PlotType, set[str]]:
    """
    For each supported plot type, collect the property names exposed by the
    returned artist(s) via their set_* methods.
    """
    dummy_fig, dummy_ax = plt.subplots()
    table: dict[PlotType, set[str]] = {}

    try:
        for name, plot in ALL_PLOTS.items():
            mpl_method = plot.backend_methods["matplotlib"]
            fn = getattr(matplotlib.axes.Axes, mpl_method, None)
            if fn is None:  # composite plot (e.g. sankey) — no native Axes artist
                table[name] = set()
                continue
            args = plot.mpl_dummy_args
            try:
                result = fn(dummy_ax, *args)
            except Exception:
                table[name] = set()
                continue

            valid: set[str] = set()
            for artist in _flatten_artists(result):
                try:
                    valid.update(ArtistInspector(artist).get_setters())
                except Exception:
                    pass
            table[name] = valid
    finally:
        plt.close(dummy_fig)

    return table


def _flatten_artists(obj):
    """Recursively yield matplotlib artists from arbitrary containers."""
    from matplotlib.container import ErrorbarContainer, BarContainer, StemContainer

    if isinstance(obj, (ErrorbarContainer, BarContainer, StemContainer)):
        for child in obj.get_children():
            yield from _flatten_artists(child)
    elif isinstance(obj, Mapping):
        for v in obj.values():
            yield from _flatten_artists(v)
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        for item in obj:
            yield from _flatten_artists(item)
    else:
        yield obj


class MatplotlibOverrider(Overrider):
    """
    Overrider for the matplotlib backend.

    Two-phase approach (identical to the original overrider.py logic):
      Phase 1 - call-time:  kwargs whose names appear in the Axes method
                            signature are passed directly to the call.
      Phase 2 - post-hoc:  remaining kwargs are applied via artist.set_*()
                            setters on the returned artist(s).
    """

    CANON_TO_NATIVE = _CANON_TO_MPL
    VALID_CALL_KWARGS = _build_call_kwargs_table()
    _ARTIST_KWARGS = _build_artist_kwargs_table()  # extra: post-hoc table

    def route(
        self,
        plot_type: PlotType,
        kwargs: KwargDict,
    ) -> tuple[KwargDict, KwargDict]:
        """
        Translate, then split into:
          call_kwargs   - accepted by the mpl Axes method signature
          post_kwargs   - valid on the returned artist(s) AND anything
                          unrouted (the "unrouted passthrough" from the
                          original overrider is preserved).
        """
        translated = self._translate(kwargs)
        valid_call = self.VALID_CALL_KWARGS.get(plot_type, set())
        valid_artist = self._ARTIST_KWARGS.get(plot_type, set())

        call_kwargs: KwargDict = {k: v for k, v in translated.items() if k in valid_call}

        # post = artist-valid OR unrouted (not consumed by the call)
        post_kwargs: KwargDict = {
            k: v for k, v in translated.items() if k not in call_kwargs and (k in valid_artist or k not in valid_call)
        }

        return call_kwargs, post_kwargs

    def apply_post(self, result: Any, post_kwargs: KwargDict) -> None:
        """Apply post_kwargs to the returned artist(s) via set_* setters."""
        from matplotlib.container import ErrorbarContainer

        if isinstance(result, ErrorbarContainer):
            self._apply_errorbar(result, post_kwargs)
        else:
            self._apply_artists(result, post_kwargs)

    def _apply_artists(self, obj: Any, kwargs: KwargDict) -> None:
        for artist in _flatten_artists(obj):
            for k, v in kwargs.items():
                setter = f"set_{k}"
                if hasattr(artist, setter):
                    try:
                        getattr(artist, setter)(v)
                    except Exception:
                        pass

    def _apply_errorbar(self, result, kwargs: KwargDict) -> None:
        """
        Special-case for ErrorbarContainer.

        Kwargs targeting specific child types via dedicated call-time params
        (elinewidth -> LineCollection, capthick -> cap Line2Ds) are not
        re-applied post-hoc to avoid double-styling.
        """
        data_line = result.lines[0]  # may be None when fmt="none"
        shared = {k: v for k, v in kwargs.items() if k not in ["linewidth", "lw"]}

        for child in result.get_children():
            applied = kwargs if child is data_line else shared
            for k, v in applied.items():
                setter = f"set_{k}"
                if hasattr(child, setter):
                    try:
                        getattr(child, setter)(v)
                    except Exception:
                        pass


_instance: MatplotlibOverrider | None = None


def get_overrider() -> MatplotlibOverrider:
    global _instance
    if _instance is None:
        _instance = MatplotlibOverrider()
    return _instance
