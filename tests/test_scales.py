"""Non-visual tests for log/symlog decade-tick snapping (behaviz.core.scales
plus its wiring into the matplotlib and bokeh backends)."""

import matplotlib

matplotlib.use("Agg")  # must happen before any other mpl import

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pytest

import math

import numpy as np

from behaviz.core.scales import (
    BILOG_C,
    bilog,
    bilog_inv,
    bilog_ticks,
    log_decade_ticks,
    symlog_decade_ticks,
)
from behaviz.backends.matplotlib.backend import MatplotlibRenderer
from behaviz.backends.bokeh.backend import BokehRenderer, _data_range
from behaviz.spec.plot_spec import PlotSpec


# --------------------------------------------------------------------------- #
# pure math                                                                    #
# --------------------------------------------------------------------------- #
class TestLogDecadeTicks:
    def test_inside_one_decade_snaps_outward(self):
        assert log_decade_ticks(20, 80) == (10, 100, [10, 100], [20, 30, 40, 50, 60, 70, 80, 90])

    def test_higher_decade(self):
        assert log_decade_ticks(200, 900) == (100, 1000, [100, 1000], [200, 300, 400, 500, 600, 700, 800, 900])

    def test_spanning_two_decades_returns_none(self):
        assert log_decade_ticks(1, 100) is None
        assert log_decade_ticks(5, 500) is None

    def test_non_positive_returns_none(self):
        assert log_decade_ticks(-5, 80) is None
        assert log_decade_ticks(0, 80) is None

    def test_degenerate_returns_none(self):
        assert log_decade_ticks(80, 20) is None  # hi <= lo
        assert log_decade_ticks(50, 50) is None

    def test_other_base(self):
        # base 2: 5,7 sit inside the [4,8) decade -> snap to 2^2..2^3, no minors
        assert log_decade_ticks(5, 7, base=2) == (4, 8, [4, 8], [])


class TestSymlogDecadeTicks:
    def test_positive_side_matches_log(self):
        assert symlog_decade_ticks(20, 80) == log_decade_ticks(20, 80)

    def test_negative_side_is_mirrored(self):
        assert symlog_decade_ticks(-80, -20) == (-100, -10, [-100, -10], [-90, -80, -70, -60, -50, -40, -30, -20])

    def test_straddling_zero_returns_none(self):
        assert symlog_decade_ticks(-50, 50) is None
        assert symlog_decade_ticks(-5, 80) is None

    def test_negative_spanning_two_decades_returns_none(self):
        assert symlog_decade_ticks(-500, -5) is None


# --------------------------------------------------------------------------- #
# matplotlib wiring                                                            #
# --------------------------------------------------------------------------- #
def _mpl_apply(scale, lim=None, ticks=None, data=(20, 80)):
    fig, ax = plt.subplots()
    ax.plot(list(data), [1] * len(data))
    sp = PlotSpec()
    sp.x.scale = scale
    sp.x.lim = lim
    sp.x.ticks = ticks
    MatplotlibRenderer().apply_axis_spec(ax, sp)
    return ax


class TestMatplotlibWiring:
    def test_log_inside_decade_snaps(self):
        ax = _mpl_apply("log", lim=(20, 80))
        assert tuple(round(v) for v in ax.get_xlim()) == (10, 100)
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [10, 100]
        assert [round(t) for t in ax.xaxis.get_minorticklocs()] == [20, 30, 40, 50, 60, 70, 80, 90]

    def test_log_data_driven_snaps_without_lim(self):
        ax = _mpl_apply("log", data=(20, 80))
        assert tuple(round(v) for v in ax.get_xlim()) == (10, 100)
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [10, 100]

    def test_explicit_ticks_suppress_snap(self):
        ax = _mpl_apply("log", lim=(20, 80), ticks=[30, 60])
        assert not isinstance(ax.xaxis.get_major_locator(), mticker.FixedLocator) or [
            round(t) for t in ax.xaxis.get_majorticklocs()
        ] == [30, 60]
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [30, 60]

    def test_multi_decade_left_untouched(self):
        ax = _mpl_apply("log", lim=(1, 1000))
        assert isinstance(ax.xaxis.get_major_locator(), mticker.LogLocator)

    def test_symlog_positive_snaps(self):
        ax = _mpl_apply("symlog", lim=(20, 80))
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [10, 100]

    def test_symlog_negative_snaps(self):
        ax = _mpl_apply("symlog", lim=(-80, -20))
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [-100, -10]
        assert [round(t) for t in ax.xaxis.get_minorticklocs()] == [-90, -80, -70, -60, -50, -40, -30, -20]

    def test_symlog_straddling_zero_untouched(self):
        ax = _mpl_apply("symlog", lim=(-50, 50))
        assert not isinstance(ax.xaxis.get_major_locator(), mticker.FixedLocator)


# --------------------------------------------------------------------------- #
# bokeh wiring                                                                 #
# --------------------------------------------------------------------------- #
def _bokeh_apply(scale, lim=None, ticks=None, data=(20, 80)):
    r = BokehRenderer()
    sp = PlotSpec()
    sp.x.scale = scale
    sp.x.lim = lim
    sp.x.ticks = ticks
    fig, _ = r.make_figure(sp)
    if data is not None:
        fig.line(x=list(data), y=[1] * len(data))
    r.apply_axis_spec(fig, sp)
    return fig


class TestDataRange:
    def test_pools_glyph_columns(self):
        fig, _ = BokehRenderer().make_figure(PlotSpec())
        fig.line(x=[20, 50, 80], y=[1, 2, 3])
        assert _data_range(fig, "x") == (20.0, 80.0)
        assert _data_range(fig, "y") == (1.0, 3.0)

    def test_empty_figure_returns_none(self):
        fig, _ = BokehRenderer().make_figure(PlotSpec())
        assert _data_range(fig, "x") is None


class TestBokehWiring:
    def test_log_explicit_lim_snaps(self):
        fig = _bokeh_apply("log", lim=(20, 80), data=None)
        assert (fig.x_range.start, fig.x_range.end) == (10, 100)
        assert fig.xaxis[0].ticker.ticks == [10, 100]
        assert fig.xaxis[0].ticker.minor_ticks == [20, 30, 40, 50, 60, 70, 80, 90]

    def test_log_data_driven_snaps_without_lim(self):
        fig = _bokeh_apply("log", data=(20, 80))
        assert (fig.x_range.start, fig.x_range.end) == (10, 100)
        assert fig.xaxis[0].ticker.ticks == [10, 100]

    def test_multi_decade_keeps_native_ticker(self):
        fig = _bokeh_apply("log", data=(1, 10, 1000))
        assert type(fig.xaxis[0].ticker).__name__ == "LogTicker"

    def test_explicit_ticks_suppress_snap(self):
        fig = _bokeh_apply("log", lim=(20, 80), ticks=[30, 60], data=None)
        assert fig.xaxis[0].ticker.ticks == [30, 60]

    def test_empty_figure_no_crash(self):
        fig = _bokeh_apply("log", data=None)
        assert type(fig.xaxis[0].ticker).__name__ == "LogTicker"


# --------------------------------------------------------------------------- #
# bilog math (Webber 2013)                                                     #
# --------------------------------------------------------------------------- #
class TestBilog:
    def test_zero_and_odd(self):
        assert bilog(0) == 0
        x = np.array([0.1, 1, 50, 1e4])
        assert np.allclose(bilog(-x), -bilog(x))

    def test_known_values(self):
        # default C: y = log10(1 + x ln10); 100 -> 2.364 (see paper eq. 4)
        assert bilog(100) == pytest.approx(2.36401, abs=1e-4)
        assert bilog(1) == pytest.approx(0.51884, abs=1e-4)

    def test_unit_slope_at_origin_for_default_c(self):
        h = 1e-6
        assert (bilog(h) - bilog(-h)) / (2 * h) == pytest.approx(1.0, rel=1e-4)

    def test_log_asymptote(self):
        # large x: log10|x| + log10(ln10) for the default C
        assert bilog(1e9) == pytest.approx(9 + math.log10(math.log(10)), abs=1e-6)

    @pytest.mark.parametrize("C", [0.01, BILOG_C, 1, 100])
    def test_roundtrip(self, C):
        x = np.array([-1e5, -3.2, -1e-3, 0, 1e-3, 3.2, 1e5])
        assert np.allclose(bilog_inv(bilog(x, C), C), x, rtol=1e-9, atol=1e-12)

    def test_c_scales_linear_zone(self):
        # |x| << C stays ~linear: y ~ x / (C ln10)
        assert bilog(0.01, C=100) == pytest.approx(0.01 / (100 * math.log(10)), rel=1e-3)

    def test_nan_passes_and_scalar_array(self):
        assert np.isnan(bilog(np.nan))
        assert bilog([1, 2]).shape == (2,)

    @pytest.mark.parametrize("C", [0, -1, np.inf, np.nan])
    def test_bad_c(self, C):
        for f in (bilog, bilog_inv):
            with pytest.raises(ValueError):
                f(1.0, C)
        with pytest.raises(ValueError):
            bilog_ticks(-10, 10, C)


class TestBilogTicks:
    def test_symmetric_range(self):
        majors, minors = bilog_ticks(-1000, 1000)
        assert majors == [-1000, -100, -10, -1, -0.1, 0, 0.1, 1, 10, 100, 1000]
        assert 2 in minors and -90 in minors and 10 not in minors

    def test_smallest_decade_is_floor_of_log10_c(self):
        # default C = 0.434 -> floor(log10 C) = -1 -> smallest decade 0.1; no 0.01
        majors, _ = bilog_ticks(-5, 5)
        assert majors == [-1, -0.1, 0, 0.1, 1]

    def test_larger_c_raises_smallest_decade(self):
        majors, _ = bilog_ticks(-1000, 1000, C=50)
        assert majors == [-1000, -100, -10, 0, 10, 100, 1000]  # floor(log10 50) = 1

    def test_small_c_adds_fine_decades(self):
        majors, _ = bilog_ticks(-1, 1, C=0.01)
        assert majors == [-1, -0.1, -0.01, 0, 0.01, 0.1, 1]

    def test_clipped_to_limits_and_exact_floats(self):
        majors, minors = bilog_ticks(0, 50, C=0.01)
        assert majors == [0, 0.01, 0.1, 1, 10]
        assert 0.03 in minors  # not 0.030000000000000002
        assert max(minors) <= 50

    def test_none_when_inside_linear_zone_or_one_decade(self):
        assert bilog_ticks(-0.05, 0.05) is None  # only 0 would be a major
        assert bilog_ticks(20, 80) is None  # no decade boundary inside
        assert bilog_ticks(5, 5) is None  # degenerate
