"""Dashboard layout — compose behaviz figures (and Panel widgets) with operators.

Patchwork/cowplot-style grammar over `panel <https://panel.holoviz.org>`_:

    from behaviz.dashboard import view

    (view(fig1) | fig2) / fig3        # | = side by side (Row), / = stacked (Column)

Requires the optional ``panel`` extra (``pip install behaviz[panel]``). Linked
selection comes from the figures sharing a :func:`behaviz.linked` source — the
layout only arranges them.
"""

from __future__ import annotations

from typing import Any

try:
    import panel as pn
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "behaviz.dashboard needs Panel. Install the extra: pip install behaviz[panel]"
    ) from exc


def _pane(obj: Any):
    """Coerce a behaviz figure / (fig, ax) tuple / Panel object into a pane."""
    if isinstance(obj, View):
        return obj.obj
    if isinstance(obj, tuple):  # behaviz returns (fig, ax)
        obj = obj[0]
    if isinstance(obj, pn.viewable.Viewable):
        return obj
    return pn.pane.Bokeh(obj)  # a bokeh figure


class View:
    """A composable Panel layout. ``|`` makes a Row, ``/`` makes a Column."""

    def __init__(self, obj: Any):
        self.obj = _pane(obj)

    def __or__(self, other: Any) -> "View":
        return View(pn.Row(self.obj, _pane(other)))

    def __truediv__(self, other: Any) -> "View":
        return View(pn.Column(self.obj, _pane(other)))

    def servable(self):
        return self.obj.servable()

    def show(self, **kwargs):
        return self.obj.show(**kwargs)

    def panel(self):
        return self.obj

    def _repr_mimebundle_(self, *args, **kwargs):  # render in notebooks
        return self.obj._repr_mimebundle_(*args, **kwargs)


def view(obj: Any) -> View:
    """Wrap a figure/widget so it composes with ``|`` and ``/``."""
    return View(obj)


def row(*objs: Any) -> View:
    return View(pn.Row(*(_pane(o) for o in objs)))


def col(*objs: Any) -> View:
    return View(pn.Column(*(_pane(o) for o in objs)))
