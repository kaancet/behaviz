"""Non-visual tests for log/symlog decade-tick snapping (behaviz.core.scales
plus its wiring into the matplotlib and bokeh backends)."""

import matplotlib
matplotlib.use("Agg")  # must happen before any other mpl import

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pytest

from behaviz.core.scales import log_decade_ticks, symlog_decade_ticks
from behaviz.backends.matplotlib.backend import MatplotlibRenderer
from behaviz.backends.bokeh.backend import BokehRenderer, _data_range
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import ScaleType


# --------------------------------------------------------------------------- #
# pure math                                                                    #
# --------------------------------------------------------------------------- #
class TestLogDecadeTicks:
    def test_inside_one_decade_snaps_outward(self):
        assert log_decade_ticks(20, 80) == (10, 100, [10, 100], [20, 30, 40, 50, 60, 70, 80, 90])

    def test_higher_decade(self):
        assert log_decade_ticks(200, 900) == (
            100, 1000, [100, 1000], [200, 300, 400, 500, 600, 700, 800, 900])

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
        assert symlog_decade_ticks(-80, -20) == (
            -100, -10, [-100, -10], [-90, -80, -70, -60, -50, -40, -30, -20])

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
        ax = _mpl_apply(ScaleType.LOG, lim=(20, 80))
        assert tuple(round(v) for v in ax.get_xlim()) == (10, 100)
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [10, 100]
        assert [round(t) for t in ax.xaxis.get_minorticklocs()] == [20, 30, 40, 50, 60, 70, 80, 90]

    def test_log_data_driven_snaps_without_lim(self):
        ax = _mpl_apply(ScaleType.LOG, data=(20, 80))
        assert tuple(round(v) for v in ax.get_xlim()) == (10, 100)
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [10, 100]

    def test_explicit_ticks_suppress_snap(self):
        ax = _mpl_apply(ScaleType.LOG, lim=(20, 80), ticks=[30, 60])
        assert not isinstance(ax.xaxis.get_major_locator(), mticker.FixedLocator) \
            or [round(t) for t in ax.xaxis.get_majorticklocs()] == [30, 60]
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [30, 60]

    def test_multi_decade_left_untouched(self):
        ax = _mpl_apply(ScaleType.LOG, lim=(1, 1000))
        assert isinstance(ax.xaxis.get_major_locator(), mticker.LogLocator)

    def test_symlog_positive_snaps(self):
        ax = _mpl_apply(ScaleType.SYMLOG, lim=(20, 80))
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [10, 100]

    def test_symlog_negative_snaps(self):
        ax = _mpl_apply(ScaleType.SYMLOG, lim=(-80, -20))
        assert [round(t) for t in ax.xaxis.get_majorticklocs()] == [-100, -10]
        assert [round(t) for t in ax.xaxis.get_minorticklocs()] == \
            [-90, -80, -70, -60, -50, -40, -30, -20]

    def test_symlog_straddling_zero_untouched(self):
        ax = _mpl_apply(ScaleType.SYMLOG, lim=(-50, 50))
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
        fig = _bokeh_apply(ScaleType.LOG, lim=(20, 80), data=None)
        assert (fig.x_range.start, fig.x_range.end) == (10, 100)
        assert fig.xaxis[0].ticker.ticks == [10, 100]
        assert fig.xaxis[0].ticker.minor_ticks == [20, 30, 40, 50, 60, 70, 80, 90]

    def test_log_data_driven_snaps_without_lim(self):
        fig = _bokeh_apply(ScaleType.LOG, data=(20, 80))
        assert (fig.x_range.start, fig.x_range.end) == (10, 100)
        assert fig.xaxis[0].ticker.ticks == [10, 100]

    def test_multi_decade_keeps_native_ticker(self):
        fig = _bokeh_apply(ScaleType.LOG, data=(1, 10, 1000))
        assert type(fig.xaxis[0].ticker).__name__ == "LogTicker"

    def test_explicit_ticks_suppress_snap(self):
        fig = _bokeh_apply(ScaleType.LOG, lim=(20, 80), ticks=[30, 60], data=None)
        assert fig.xaxis[0].ticker.ticks == [30, 60]

    def test_empty_figure_no_crash(self):
        fig = _bokeh_apply(ScaleType.LOG, data=None)
        assert type(fig.xaxis[0].ticker).__name__ == "LogTicker"
