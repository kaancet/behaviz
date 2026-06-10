from __future__ import annotations

from behaviz.backends.matplotlib.hover_engine import MatplotlibHoverEngine


class SeabornHoverEngine(MatplotlibHoverEngine):
    """Hover engine for the seaborn backend.

    Seaborn draws onto a plain matplotlib ``Axes``, so hover behaviour is
    identical to the matplotlib engine.  Kept as its own subclass so each
    backend owns a ``hover_engine.py`` and the wiring stays symmetric.
    """

    pass
