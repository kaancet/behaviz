from __future__ import annotations

import inspect
from collections.abc import Sequence, Mapping
from typing import Any
import seaborn as sns

from behaviz.core.override import Overrider, KwargDict, PlotType


_CANON_TO_SNS: dict[str, list[str]] = {
    # color
    "color": ["color"],
    "fillcolor": ["facecolor"],
    "edgecolor": ["edgecolor"],
    # Bokeh-style aliases → mpl names
    "line_color": ["color"],
    "fill_color": ["facecolor"],
    "line_alpha": ["alpha"],
    "fill_alpha": ["alpha"],
    "line_width": ["linewidth"],
    "line_dash": ["linestyle"],
    # Line
    "linewidth": ["linewidth"],
    "linestyle": ["linestyle"],
    "linedash": ["linestyle"],
    # Marker / scatter
    # Note: for scatter specifically, 'markersize' and 'size' are remapped to
    # 's' inside route() because sns.scatterplot forwards 's' (not 'markersize')
    # to the underlying PathCollection.  For line/errorbar, markersize is correct.
    "markersize": ["markersize"],
    "marker": ["marker"],
    "markerfacecolor": ["markerfacecolor"],
    "markeredgecolor": ["markeredgecolor"],
    "size": ["markersize"],  # remapped to 's' for scatter in route()
    # Label / legend
    "label": ["label"],
    "legend_label": ["label"],  # Bokeh alias
    # Misc
    "alpha": ["alpha"],
    "zorder": ["zorder"],
    "capsize": ["capsize"],
}


def _build_call_kwargs_table() -> dict[PlotType, set[str]]:
    """
    Collect the parameter names each Seaborn function accepts at call time.

    Seaborn functions expose ``**kwargs`` that are forwarded to matplotlib, so
    we include a broad set of common matplotlib artist properties in addition to
    the explicitly named Seaborn parameters.
    """
    _sns_fns = {
        "line": sns.lineplot,
        "scatter": sns.scatterplot,
        "errorbar": sns.lineplot,  # fallback; real errorbar uses ax.errorbar
        "bar": sns.barplot,
        "violin": sns.violinplot,
    }

    # Common matplotlib artist kwargs forwarded through Seaborn's **kwargs
    _mpl_passthrough = {
        "color",
        "alpha",
        "linewidth",
        "linestyle",
        "marker",
        "markersize",
        "markerfacecolor",
        "markeredgecolor",
        "facecolor",
        "edgecolor",
        "label",
        "zorder",
        "capsize",
        "elinewidth",
        "capthick",
        "ecolor",
        "dashes",
        "dash_capstyle",
        "dash_joinstyle",
        "solid_capstyle",
        "solid_joinstyle",
        "s",  # PathCollection point size (used by scatter via **kwargs)
    }

    table: dict[PlotType, set[str]] = {}
    for plot_type, fn in _sns_fns.items():
        sig = inspect.signature(fn)
        params = set(sig.parameters.keys()) - {"ax", "data", "x", "y", "args", "kwargs"}
        table[plot_type] = params | _mpl_passthrough

    # step has no Seaborn equivalent — falls back to ax.step (mpl params)
    import matplotlib.axes

    step_sig = inspect.signature(matplotlib.axes.Axes.step)
    table["step"] = set(step_sig.parameters.keys()) - {"self"}

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


class SeabornOverrider(Overrider):
    """
    Overrider for the Seaborn backend.

    Because Seaborn draws on matplotlib Axes, post-hoc styling uses the same
    artist-setter walk as ``MatplotlibOverrider``.  The key difference is the
    translation table, which accepts both Bokeh-style aliases and native
    matplotlib/Seaborn names.
    """

    CANON_TO_NATIVE = _CANON_TO_SNS
    VALID_CALL_KWARGS = _build_call_kwargs_table()
    _SCATTER_REMAP = {"markersize": "s"}  # markersize/size → 's' only for scatter

    def route(
        self,
        plot_type: PlotType,
        kwargs: KwargDict,
    ) -> tuple[KwargDict, KwargDict]:
        call_kwargs, post_kwargs = super().route(plot_type, kwargs)
        if plot_type == "scatter":
            # Remap markersize → s so sns.scatterplot's **kwargs passthrough
            # delivers it to PathCollection correctly.
            for old_key, new_key in self._SCATTER_REMAP.items():
                if old_key in call_kwargs:
                    call_kwargs[new_key] = call_kwargs.pop(old_key)
                if old_key in post_kwargs:
                    post_kwargs[new_key] = post_kwargs.pop(old_key)
        return call_kwargs, post_kwargs

    def apply_post(self, result: Any, post_kwargs: KwargDict) -> None:
        """
        Apply remaining kwargs to the returned artist(s) via set_* setters.

        Since Seaborn axes are matplotlib axes, this is the same mechanism as
        in MatplotlibOverrider.
        """
        if not post_kwargs:
            return

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
        """Mirror of MatplotlibOverrider._apply_errorbar."""
        from matplotlib.collections import LineCollection

        call_kwargs, _ = self.route("errorbar", kwargs)
        skip_types: set[type] = set()
        if "elinewidth" in call_kwargs or "capthick" in call_kwargs:
            skip_types.add(LineCollection)

        for child in result.get_children():
            if type(child) in skip_types:
                continue
            for k, v in kwargs.items():
                setter = f"set_{k}"
                if hasattr(child, setter):
                    try:
                        getattr(child, setter)(v)
                    except Exception:
                        pass


_instance: SeabornOverrider | None = None


def get_overrider() -> SeabornOverrider:
    global _instance
    if _instance is None:
        _instance = SeabornOverrider()
    return _instance
