"""bokeh "bilog" axis: data transform (idempotent, reversible), ticks, labels, hover."""

import numpy as np
import pytest
from bokeh.embed import json_item
from bokeh.models import BasicTicker, DataRange1d, FixedTicker, HoverTool

import behaviz as bv
from behaviz.backends.bokeh.backend import BokehRenderer
from behaviz.backends.bokeh.bilog_scale import _even_ticks
from behaviz.core.scales import BILOG_C, bilog, bilog_label, hidden_labels
from behaviz.spec import AxisSpec, PlotSpec

MINUS = "\N{MINUS SIGN}"
X = np.array([-1000.0, -10.0, -1.0, 0.0, 1.0, 10.0, 1000.0])


@pytest.fixture(autouse=True)
def reset_renderer():
    yield
    bv.set_renderer("matplotlib")


def _spec(xscale="bilog", yscale="linear", **xkw):
    return PlotSpec(x=AxisSpec(scale=xscale, **xkw), y=AxisSpec(scale=yscale))


def _draw(spec, draw=None, x=X, y=X):
    r = BokehRenderer()
    fig, _ = r.make_figure(spec)
    (draw or (lambda r, fig: r.line(fig, x, y)))(r, fig)
    r.apply_axis_spec(fig, spec)
    return r, fig, fig.renderers[0].data_source


class TestData:
    def test_transformed_and_raw_kept(self):
        _, _, ds = _draw(_spec())
        assert np.allclose(ds.data["x"], bilog(X))
        assert np.array_equal(ds.data["x__raw"], X)
        assert np.array_equal(ds.data["y"], X) and "y__raw" not in ds.data  # y is linear

    def test_c_from_spec_and_default(self):
        assert np.allclose(_draw(_spec(bilog_c=2))[2].data["x"], bilog(X, 2))
        assert np.allclose(_draw(_spec())[2].data["x"], bilog(X, BILOG_C))

    def test_idempotent(self):
        r, fig, ds = _draw(_spec())
        once = np.array(ds.data["x"])
        r.apply_axis_spec(fig, _spec())
        r.apply_axis_spec(fig, _spec())
        assert np.array_equal(ds.data["x"], once)
        assert np.array_equal(ds.data["x__raw"], X)

    def test_c_change_recomputes_from_raw(self):
        r, fig, ds = _draw(_spec(bilog_c=2))
        r.apply_axis_spec(fig, _spec(bilog_c=0.5))
        assert np.allclose(ds.data["x"], bilog(X, 0.5))

    def test_switch_back_restores_everything(self):
        r, fig, ds = _draw(_spec(lim=(-50, 50)))
        r.apply_axis_spec(fig, _spec("linear"))
        assert np.array_equal(ds.data["x"], X) and "x__raw" not in ds.data
        ax = fig.xaxis[0]
        assert not ax.major_label_overrides and isinstance(ax.ticker, BasicTicker)
        assert isinstance(fig.x_range, DataRange1d)  # back to the automatic range

    def test_both_axes_and_zero_y(self):
        _, _, ds = _draw(_spec(yscale="bilog"))
        assert np.allclose(ds.data["y"], bilog(X)) and np.isfinite(ds.data["y"]).all()

    def test_string_column_left_alone(self):
        spec = _spec()
        r = BokehRenderer()
        fig, _ = r.make_figure(spec)
        fig.scatter(x=["a", "b"], y=[1, 2])
        r.apply_axis_spec(fig, spec)
        assert list(fig.renderers[0].data_source.data["x"]) == ["a", "b"]


class TestGlyphs:
    def test_bar_top_and_bottom(self):
        y = np.array([-100.0, 0.0, 10.0, 1000.0])
        _, _, ds = _draw(_spec("linear", "bilog"), lambda r, fig: r.bar(fig, np.arange(4.0), y, 0.5), x=None, y=None)
        assert np.allclose(ds.data["top"], bilog(y)) and np.allclose(ds.data["bottom"], 0)

    def test_errorbar_and_step_smoke(self):
        for draw in (
            lambda r, fig: r.errorbar(fig, X, X, yerr=np.full_like(X, 0.5)),
            lambda r, fig: r.step(fig, X, X),
        ):
            _, fig, _ = _draw(_spec(yscale="bilog"), draw)
            json_item(fig)  # serialises

    def test_plain_number_positions_warn(self):
        with pytest.warns(UserWarning, match="plain numbers"):
            _draw(_spec(), lambda r, fig: r.image(fig, np.random.rand(3, 3), extent=(1, 4, 1, 4)))


class TestAxis:
    def test_ticks_and_labels(self):
        _, fig, _ = _draw(_spec(lim=(-1000, 1000)))
        ax = fig.xaxis[0]
        assert isinstance(ax.ticker, FixedTicker)
        majors = [-1000, -100, -10, -1, -0.1, 0, 0.1, 1, 10, 100, 1000]
        assert np.allclose(ax.ticker.ticks, bilog(majors))
        ov = ax.major_label_overrides
        assert ov[float(bilog(1000))] == "1000" and ov[float(bilog(-1000))] == f"{MINUS}1000"
        assert ov[0.0] == "0"
        assert ov[float(bilog(0.1))] == "" and ov[float(bilog(-0.1))] == ""  # crowds the "0"

    def test_lim_is_transformed(self):
        _, fig, _ = _draw(_spec(lim=(-100, 1000), bilog_c=2))
        assert fig.x_range.start == pytest.approx(float(bilog(-100, 2)))
        assert fig.x_range.end == pytest.approx(float(bilog(1000, 2)))

    def test_limits_from_data_when_no_lim(self):
        _, fig, _ = _draw(_spec())
        assert float(bilog(1000)) in fig.xaxis[0].ticker.ticks

    def test_explicit_ticks_are_transformed_and_all_labelled(self):
        _, fig, _ = _draw(_spec(ticks=[-100, 0, 100]))
        ax = fig.xaxis[0]
        assert np.allclose(ax.ticker.ticks, bilog([-100, 0, 100]))
        assert sorted(ax.major_label_overrides.values()) == sorted([f"{MINUS}100", "0", "100"])

    def test_tick_fmt_used_for_labels(self):
        _, fig, _ = _draw(_spec(lim=(-1000, 1000), tick_fmt="%.1f"))
        assert fig.xaxis[0].major_label_overrides[float(bilog(1000))] == "1000.0"

    def test_linear_zone_falls_back_to_even_ticks(self):
        x = np.array([-0.04, 0.0, 0.04])
        _, fig, _ = _draw(_spec(), x=x, y=x)
        ticks = fig.xaxis[0].ticker.ticks
        assert len(ticks) > 1 and fig.xaxis[0].major_label_overrides

    def test_serialises(self):
        _, fig, _ = _draw(_spec(yscale="bilog"))
        json_item(fig)


class TestHover:
    def test_tooltips_use_raw_and_revert(self):
        spec = _spec()
        r = BokehRenderer()
        fig, _ = r.make_figure(spec)
        r.scatter(fig, X, X, hover_annotate=True)
        tip = lambda: next(t for t in fig.tools if isinstance(t, HoverTool)).tooltips
        r.apply_axis_spec(fig, spec)
        assert ("x", "@{x__raw}{0.00}") in tip() and ("y", "@{y}{0.00}") in tip()
        r.apply_axis_spec(fig, spec)  # idempotent
        assert ("x", "@{x__raw}{0.00}") in tip()
        r.apply_axis_spec(fig, _spec("linear"))
        assert ("x", "@{x}{0.00}") in tip()


class TestEndToEnd:
    def test_set_xaxis_after_plot_and_back(self):
        bv.set_renderer("bokeh")
        fig, ax = bv.plot_line(X, X)
        bv.set_xaxis(ax, "bilog", bilog_c=2)
        ds = ax.renderers[0].data_source
        assert np.allclose(ds.data["x"], bilog(X, 2))
        bv.set_xaxis(ax, "linear")
        assert np.array_equal(ds.data["x"], X)


class TestShared:
    def test_hidden_labels_priority_and_gap(self):
        values = [0.0, 0.1, 1.0, 10.0]
        pos = [0.0, 0.09, 0.52, 1.38]
        assert hidden_labels(values, pos, span=6.0, slots=10) == {0.1, 1.0}  # gap 0.6
        assert hidden_labels(values, pos, span=6.0, slots=100) == set()  # gap 0.06
        assert hidden_labels(values, pos, span=0, slots=10) == set()

    def test_bilog_label(self):
        assert [bilog_label(v) for v in (-100, 0, 0.1, 1e6)] == [f"{MINUS}100", "0", "0.1", "1e+06"]
        assert bilog_label(-5, unicode_minus=False) == "-5"

    def test_even_ticks(self):
        assert _even_ticks(-0.04, 0.04) == pytest.approx([-0.04, -0.02, 0, 0.02, 0.04])
        assert _even_ticks(3, 3) == [3]
