"""Backend-agnostic tick generation for log scales.

matplotlib's ``LogLocator`` and bokeh's ``LogTicker`` both place major ticks
only on decade boundaries (powers of the base). When the view limits fall
inside a single decade (e.g. 20–80 on a base-10 axis) there is no decade
boundary between them, so neither backend draws any tick and the axis comes up
blank. We detect that case, snap the limits outward to the enclosing decades,
and hand every backend the same explicit major/minor tick lists.
"""

from __future__ import annotations

import math


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
