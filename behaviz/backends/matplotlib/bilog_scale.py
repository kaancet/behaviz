"""matplotlib ``"bilog"`` scale: ``ax.set_xscale("bilog", C=...)``.

Math lives in :mod:`behaviz.core.scales`; this file only adapts it to
matplotlib's transform / locator / formatter API. Importing the module registers
the scale, and ``MatplotlibRenderer`` (hence seaborn too) imports it.
"""

from __future__ import annotations

import matplotlib as mpl
import numpy as np
import matplotlib.ticker as ticker
from matplotlib import scale as mscale
from matplotlib.transforms import Transform

from behaviz.core.scales import BILOG_C, bilog, bilog_inv, bilog_label, bilog_ticks, hidden_labels


class BilogTransform(Transform):
    input_dims = output_dims = 1
    is_separable = True
    has_inverse = True

    def __init__(self, C: float = BILOG_C):
        super().__init__()
        self.C = C

    def transform_non_affine(self, values):
        return bilog(values, self.C)

    def inverted(self):
        return InvertedBilogTransform(self.C)


class InvertedBilogTransform(Transform):
    input_dims = output_dims = 1
    is_separable = True
    has_inverse = True

    def __init__(self, C: float = BILOG_C):
        super().__init__()
        self.C = C

    def transform_non_affine(self, values):
        return bilog_inv(values, self.C)

    def inverted(self):
        return BilogTransform(self.C)


class BilogLocator(ticker.Locator):
    """Major (0, ±10^k) or minor (±m·10^k) ticks from :func:`bilog_ticks`."""

    def __init__(self, C: float = BILOG_C, minor: bool = False):
        self.C = C
        self.minor = minor

    def __call__(self):
        return self.tick_values(*self.axis.get_view_interval())

    def tick_values(self, vmin, vmax):
        if vmax < vmin:  # inverted axis
            vmin, vmax = vmax, vmin
        ticks = bilog_ticks(vmin, vmax, self.C)
        if ticks is None:  # inside the linear zone / one decade: plain even ticks
            return [] if self.minor else ticker.MaxNLocator(6).tick_values(vmin, vmax)
        return ticks[1 if self.minor else 0]


def _format(value, _pos=None) -> str:
    return bilog_label(value, mpl.rcParams["axes.unicode_minus"])


class BilogFormatter(ticker.Formatter):
    """``{v:g}`` labels; a label that would overprint a neighbour is left blank.

    Near 0 the decades (0.1, 1, ...) sit close together on the axis. Tick marks all
    stay; labels are kept in priority order 0 first, then larger |value| first, and a
    label is dropped when it is closer than one label slot (matplotlib's own
    ``axis.get_tick_space`` estimate) to a label already kept.
    """

    def __init__(self):
        self._hidden = frozenset()

    def __call__(self, x, pos=None):
        return "" if x in self._hidden else _format(x)

    def set_locs(self, locs):
        self._hidden = frozenset()
        axis = self.axis
        if axis is None or len(locs) < 2:
            return
        trans = axis.get_transform()
        lo, hi = trans.transform(np.asarray(axis.get_view_interval(), dtype=float))
        slots = axis.get_tick_space()
        locs = np.asarray(locs, dtype=float)
        self._hidden = frozenset(hidden_labels(locs, trans.transform(locs), abs(hi - lo), slots))


class BilogScale(mscale.ScaleBase):
    """``sgn(x) * log10(1 + |x|/C)`` axis; ``C`` defaults to ``1/ln(10)``."""

    name = "bilog"

    def __init__(self, axis, *, C: float = BILOG_C):
        super().__init__(axis)
        bilog(0.0, C)  # validates C (positive, finite)
        self.C = C

    def get_transform(self):
        return BilogTransform(self.C)

    def set_default_locators_and_formatters(self, axis):
        axis.set_major_locator(BilogLocator(self.C))
        axis.set_major_formatter(BilogFormatter())
        axis.set_minor_locator(BilogLocator(self.C, minor=True))
        axis.set_minor_formatter(ticker.NullFormatter())


mscale.register_scale(BilogScale)
