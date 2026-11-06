"""Backend-agnostic tick generation for log scales.

matplotlib's ``LogLocator`` and bokeh's ``LogTicker`` both place major ticks
only on decade boundaries (powers of the base). When the view limits fall
inside a single decade (e.g. 20–80 on a base-10 axis) there is no decade
boundary between them, so neither backend draws any tick and the axis comes up
blank. We detect that case, snap the limits outward to the enclosing decades,
and hand every backend the same explicit major/minor tick lists.

Also holds the math for the ``"bilog"`` scale (Webber 2013, Meas. Sci. Technol.
24 027001).
"""

from __future__ import annotations

import math

import numpy as np

_LN10 = math.log(10)
BILOG_C = 1 / _LN10  # default: unit slope at the origin


def log_decade_ticks(lo: float, hi: float, base: int = 10):
    """Snap ``(lo, hi)`` outward to decade boundaries with major+minor ticks.

    Returns ``(new_lo, new_hi, majors, minors)`` when the limits sit inside a
    single decade (the empty-axis case), else ``None`` — leave the backend's
    own locator alone when it already has a decade boundary to anchor to.
    """
    if not (lo > 0 and hi > 0) or hi <= lo:
        return None  # non-positive or degenerate — not our case
    lo_e = math.floor(math.log(lo, base))
    hi_e = math.floor(math.log(hi, base))
    if lo_e != hi_e:
        return None  # a decade boundary already lies between them
    new_lo = base**lo_e
    new_hi = base ** (hi_e + 1)
    majors = [new_lo, new_hi]
    minors = [m * base**lo_e for m in range(2, base)]
    return new_lo, new_hi, majors, minors


def symlog_decade_ticks(lo: float, hi: float, base: int = 10):
    """Symlog analog of :func:`log_decade_ticks`.

    Only the same-sign, inside-one-decade case is empty-axis-prone — that log
    side has no decade boundary to anchor. When the limits straddle 0 (or cross
    the linear band) the backend's ``SymmetricalLogLocator`` already anchors on
    0 and the decades on each side, so return ``None`` and leave it alone.
    Negative side is the positive result mirrored through 0.
    """
    if lo > 0 and hi > 0:
        return log_decade_ticks(lo, hi, base)
    if lo < 0 and hi < 0:
        res = log_decade_ticks(-hi, -lo, base)  # work on magnitudes (|hi| < |lo|)
        if res is None:
            return None
        p_lo, p_hi, majors, minors = res
        return -p_hi, -p_lo, [-t for t in reversed(majors)], [-t for t in reversed(minors)]
    return None  # straddles 0 / linear band — locator handles it


def _check_c(C: float) -> float:
    if not (C > 0 and math.isfinite(C)):
        raise ValueError(f"bilog C must be a positive finite number, got {C!r}")
    return C


def bilog(x, C: float = BILOG_C):
    """Bi-symmetric log: ``sgn(x) * log10(1 + |x|/C)`` (paper eq. 4).

    Linear (slope ``1/(C ln10)``) for ``|x| << C``, log10 for ``|x| >> C``,
    odd, finite at 0. Works on scalars and arrays; NaN passes through.
    """
    _check_c(C)
    x = np.asarray(x, dtype=float)
    return np.copysign(np.log1p(np.abs(x) / C), x) / _LN10


def bilog_inv(y, C: float = BILOG_C):
    """Inverse of :func:`bilog`: ``sgn(y) * C * (10**|y| - 1)`` (paper eq. 5)."""
    _check_c(C)
    y = np.asarray(y, dtype=float)
    return np.copysign(C * np.expm1(np.abs(y) * _LN10), y)


def bilog_ticks(lo: float, hi: float, C: float = BILOG_C):
    """Major/minor tick positions (data units) for a bilog axis spanning ``(lo, hi)``.

    Majors: 0 and ``±10**k``; minors: ``±m * 10**k`` for ``m`` in 2..9. The
    smallest decade is ``10**floor(log10 C)``, i.e. the decade at or just below
    ``C``, so nothing finer than the linear zone is labelled.

    Returns ``(majors, minors)`` as sorted lists inside ``[lo, hi]``, or ``None``
    when no non-zero major lands in range (limits inside the linear zone or inside
    a single decade) — the backend should then fall back to its own locator.
    """
    _check_c(C)
    if not hi > lo:
        return None
    kmin = math.floor(math.log10(C))
    kmax = math.ceil(math.log10(max(abs(lo), abs(hi), 1e-300)))
    ks = range(kmin, max(kmin, kmax) + 1)
    # float("1e-1") etc. avoids 3 * 0.1 == 0.30000000000000004 style drift
    mags = [float(f"1e{k}") for k in ks]
    minor_mags = [float(f"{m}e{k}") for k in ks for m in range(2, 10)]
    inside = lambda ts: sorted(t for t in ts if lo <= t <= hi)
    majors = inside([0.0] + mags + [-m for m in mags])
    if not any(majors):
        return None
    return majors, inside(minor_mags + [-m for m in minor_mags])


def hidden_labels(values, positions, span: float, slots: float) -> set:
    """Tick values whose labels would overprint a neighbour on a bilog axis.

    ``positions`` are the ticks' transformed coordinates, ``span`` the transformed
    length of the axis and ``slots`` how many labels fit along it, so one label
    needs ``span / slots``. Labels are kept in priority order: 0 first, then larger
    ``|value|`` first; one closer than a slot to a kept label is hidden.
    """
    if len(values) < 2 or not (span > 0 and slots >= 1):
        return set()
    gap = span / slots
    kept, hidden = [], set()
    for i in sorted(range(len(values)), key=lambda i: (values[i] != 0, -abs(values[i]))):
        if all(abs(positions[i] - p) >= gap for p in kept):
            kept.append(positions[i])
        else:
            hidden.add(float(values[i]))
    return hidden


def bilog_label(value: float, unicode_minus: bool = True) -> str:
    """Tick text for a bilog axis: ``{v:g}``, ``0`` for zero, real minus sign."""
    if value == 0:
        return "0"
    s = f"{value:g}"
    return s.replace("-", "\N{MINUS SIGN}") if unicode_minus else s
