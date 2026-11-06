"""matplotlib/seaborn "bilog" scale: registration, transform, ticks, labels, wiring."""

import warnings

import matplotlib.pyplot as plt
import matplotlib.scale as mscale
import numpy as np
import pytest

import behaviz as bv
from behaviz.backends.matplotlib.backend import MatplotlibRenderer
from behaviz.backends.matplotlib.bilog_scale import BilogFormatter
from behaviz.backends.seaborn.backend import SeabornRenderer
from behaviz.core.scales import BILOG_C, bilog
from behaviz.spec import AxisSpec, PlotSpec

MINUS = "\N{MINUS SIGN}"


@pytest.fixture(autouse=True)
def reset_renderer():
    yield
    bv.set_renderer("matplotlib")


def _apply(renderer=MatplotlibRenderer, **xkw):
    fig, ax = plt.subplots()
    ax.plot([-5, 5], [0, 1])
    renderer().apply_axis_spec(ax, PlotSpec(x=AxisSpec(scale="bilog", **xkw)))
    fig.canvas.draw()  # locator/formatter errors surface here
    return ax


class TestScale:
    def test_registered_and_kwarg(self):
        assert "bilog" in mscale.get_scale_names()
        _, ax = plt.subplots()
        ax.set_xscale("bilog", C=2)
        assert ax.xaxis.get_scale() == "bilog" and ax.xaxis.get_transform().C == 2

    def test_transform_and_inverse(self):
        _, ax = plt.subplots()
        ax.set_xscale("bilog")
        t = ax.xaxis.get_transform()
        assert t.transform([100.0])[0] == pytest.approx(2.36401, abs=1e-4)
        x = np.array([-1e4, -0.3, 0, 0.3, 1e4])
        assert np.allclose(t.inverted().transform(t.transform(x)), x)

    def test_bad_c_raises(self):
        _, ax = plt.subplots()
        with pytest.raises(ValueError):
            ax.set_xscale("bilog", C=-1)


class TestWiring:
    @pytest.mark.parametrize("renderer", [MatplotlibRenderer, SeabornRenderer])
    def test_apply_axis_spec_passes_c(self, renderer):
        ax = _apply(renderer, bilog_c=0.5)
        assert ax.xaxis.get_scale() == "bilog" and ax.xaxis.get_transform().C == 0.5
        assert ax.yaxis.get_scale() == "linear"

    def test_default_c_when_none(self):
        assert _apply().xaxis.get_transform().C == BILOG_C

    def test_other_scales_do_not_get_c(self):
        _, ax = plt.subplots()
        ax.plot([1, 10], [1, 10])
        MatplotlibRenderer().apply_axis_spec(ax, PlotSpec(x=AxisSpec(scale="log", bilog_c=3)))
        assert ax.xaxis.get_scale() == "log"


class TestTicks:
    def test_majors_and_minors(self):
        ax = _apply(lim=(-1000, 1000))
        assert list(ax.xaxis.get_majorticklocs()) == [-1000, -100, -10, -1, -0.1, 0, 0.1, 1, 10, 100, 1000]
        minors = ax.xaxis.get_minorticklocs()
        assert 2 in minors and -90 in minors and 10 not in minors

    def test_larger_c_drops_fine_decades(self):
        ax = _apply(lim=(-1000, 1000), bilog_c=50)
        assert list(ax.xaxis.get_majorticklocs()) == [-1000, -100, -10, 0, 10, 100, 1000]

    def test_inverted_limits(self):
        ax = _apply(lim=(1000, -1000))
        assert 1000 in ax.xaxis.get_majorticklocs() and -1000 in ax.xaxis.get_majorticklocs()

    def test_linear_zone_falls_back_to_even_ticks(self):
        ax = _apply(lim=(-0.05, 0.05))
        assert len(ax.xaxis.get_majorticklocs()) > 1
        assert len(ax.xaxis.get_minorticklocs()) == 0

    def test_explicit_ticks_win(self):
        ax = _apply(lim=(-1000, 1000), ticks=[-100, 0, 100])
        assert list(ax.xaxis.get_majorticklocs()) == [-100, 0, 100]

    def test_crowded_labels_hidden_but_ticks_kept(self):
        ax = _apply(lim=(-1000, 1000))
        texts = [t.get_text() for t in ax.xaxis.get_majorticklabels()]
        assert len(ax.xaxis.get_majorticklocs()) == 11  # every tick mark stays
        assert {"0", "1000", f"{MINUS}1000", "100", "10"} <= set(texts)
        assert "0.1" not in texts and f"{MINUS}0.1" not in texts  # 0.09 from the "0" label

    def test_labels_return_when_zoomed_in(self):
        texts = [t.get_text() for t in _apply(lim=(-0.5, 0.5)).xaxis.get_majorticklabels()]
        assert {"0", "0.1", f"{MINUS}0.1"} <= set(texts)

    def test_labels(self):
        fmt = BilogFormatter()  # no axis -> no hiding, just the text
        assert [fmt(v) for v in (-100, 0, 0.1, 1000)] == [f"{MINUS}100", "0", "0.1", "1000"]


class TestEndToEnd:
    def test_zeros_and_negatives_plot_cleanly(self):
        bv.set_renderer("matplotlib")
        x = np.array([-1000, -10, -1, 0, 1, 10, 1000], dtype=float)
        spec = PlotSpec(x=AxisSpec(scale="bilog"), y=AxisSpec(scale="bilog", bilog_c=2))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            fig, ax = bv.plot_line(x, x, spec=spec)
            fig.canvas.draw()
        assert np.isfinite(ax.transData.transform(np.column_stack([x, x]))).all()
        # symmetric data -> symmetric display positions around the origin
        pts = ax.transData.transform(np.column_stack([x, x]))[:, 0]
        assert pts[0] + pts[-1] == pytest.approx(2 * pts[3], rel=1e-6)

    def test_set_xaxis_after_plot_and_back(self):
        bv.set_renderer("matplotlib")
        x = np.linspace(-100, 100, 21)
        fig, ax = bv.plot_line(x, x)
        bv.set_xaxis(ax, "bilog", bilog_c=2)
        assert ax.xaxis.get_scale() == "bilog" and ax.xaxis.get_transform().C == 2
        fig.canvas.draw()
        bv.set_xaxis(ax, "linear")
        assert ax.xaxis.get_scale() == "linear"
        assert ax.xaxis.get_transform().transform([7.0])[0] == 7.0

    def test_values_match_core_math(self):
        _, ax = plt.subplots()
        ax.set_xscale("bilog", C=3)
        x = np.array([-50.0, -1.0, 0.0, 2.0, 80.0])
        assert np.allclose(ax.xaxis.get_transform().transform(x), bilog(x, 3))
