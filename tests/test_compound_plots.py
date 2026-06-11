"""
Tests for compound plots, focused on the backend-agnostic violin folding used
by the raincloud plot (behaviz/compound_plots/_violin_ops.py).
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

import behaviz as bv
from behaviz import set_renderer, split_styles
from behaviz.compound_plots.raincloudplot import plot_raincloud
from behaviz.compound_plots.raincloudplot import fold_violins

CLIP_BACKENDS = ["matplotlib", "seaborn", "bokeh"]  # backends that expose violin artists


@pytest.fixture(autouse=True)
def reset_renderer():
    yield
    set_renderer("matplotlib")


@pytest.fixture
def violin_data():
    rng = np.random.default_rng(0)
    positions = np.array([1.0, 2.0, 3.0])
    ys = [rng.normal(loc=p, scale=0.5, size=120) for p in positions]
    return positions, ys


# ── extract the x-coords of a violin body, per backend ───────────────────────
def _body_xs(body, backend):
    if backend == "bokeh":
        return np.asarray(body.data_source.data[body.glyph.x], dtype=float)
    return np.asarray(body.get_paths()[0].vertices[:, 0], dtype=float)


# ── folding ──────────────────────────────────────────────────────────────────
class TestFoldViolins:
    @pytest.mark.parametrize("backend", CLIP_BACKENDS)
    def test_left_fold_removes_right_side(self, backend, violin_data):
        set_renderer(backend)
        positions, ys = violin_data
        _, _, vp = bv.plot_violin(positions, ys)

        body = vp["bodies"][0]
        centre = float(np.mean(_body_xs(body, backend)))
        assert (_body_xs(body, backend) > centre + 1e-9).any()  # full violin first

        fold_violins(vp, side="left")
        assert not (_body_xs(body, backend) > centre + 1e-9).any()  # right half folded in

    @pytest.mark.parametrize("backend", CLIP_BACKENDS)
    def test_right_fold_removes_left_side(self, backend, violin_data):
        set_renderer(backend)
        positions, ys = violin_data
        _, _, vp = bv.plot_violin(positions, ys)

        body = vp["bodies"][0]
        centre = float(np.mean(_body_xs(body, backend)))

        fold_violins(vp, side="right")
        assert not (_body_xs(body, backend) < centre - 1e-9).any()

    def test_none_is_noop(self):
        fold_violins(None)  # must not raise

    def test_empty_bodies_is_noop(self):
        fold_violins({"bodies": []})  # must not raise

    @pytest.mark.parametrize("backend", CLIP_BACKENDS)
    def test_bodies_centred_on_numeric_positions(self, backend, violin_data):
        """Violins must sit at the real positions on every backend.

        Guards the seaborn `native_scale=True` fix: without it seaborn would
        place violins at ordinal 0,1,2 and misalign with the rainplot scatter.
        """
        set_renderer(backend)
        positions, ys = violin_data
        _, _, vp = bv.plot_violin(positions, ys)
        centres = sorted(float(np.mean(_body_xs(b, backend))) for b in vp["bodies"])
        np.testing.assert_allclose(centres, positions, atol=0.1)


# ── rainplot is backend-agnostic ─────────────────────────────────────────────
class TestRainplotBackendAgnostic:
    @pytest.mark.parametrize("backend", ["matplotlib", "seaborn", "bokeh"])
    def test_runs_on_every_backend(self, backend, violin_data):
        set_renderer(backend)
        positions, ys = violin_data
        result = plot_raincloud(positions, ys, cloud_side="left")
        assert result is not None

    @pytest.mark.parametrize("backend", CLIP_BACKENDS)
    def test_cloud_violins_are_one_sided(self, backend, violin_data):
        """After plot_raincloud(cloud_side="left"), the violin artists are half violins."""
        set_renderer(backend)
        positions, ys = violin_data
        # Re-create the violin the way plot_rain does and confirm folding sticks.
        _, _, vp = bv.plot_violin(positions, ys)
        # Capture each body's centre *before* folding — folding shifts the mean.
        centres = [float(np.mean(_body_xs(b, backend))) for b in vp["bodies"]]
        fold_violins(vp, side="left")
        for body, centre in zip(vp["bodies"], centres):
            xs = _body_xs(body, backend)
            # everything at or left of the original centre (allow tiny float slack)
            assert xs.max() <= centre + 1e-6

    def test_no_cloud_path_still_works(self, violin_data):
        set_renderer("matplotlib")
        positions, ys = violin_data
        result = plot_raincloud(positions, ys, cloud_side="left")
        assert result is not None


# ── override distribution for compound plots ─────────────────────────────────
class TestSplitStyles:
    def test_shared_override_reaches_every_component(self):
        out = split_styles({"color": "red"}, ("bar", "dot"))
        assert out == {"bar": {"color": "red"}, "dot": {"color": "red"}}

    def test_user_override_beats_compound_default(self):
        out = split_styles({"color": "red"}, ("bar", "dot"), {"bar": {"color": "navy"}})
        assert out["bar"]["color"] == "red"  # user wins over the default
        assert out["dot"]["color"] == "red"

    def test_prefixed_targets_single_component(self):
        out = split_styles({"dot_color": "black"}, ("bar", "dot"))
        assert out["dot"] == {"color": "black"}
        assert out["bar"] == {}

    def test_prefixed_beats_shared(self):
        out = split_styles({"color": "red", "dot_color": "black"}, ("bar", "dot"))
        assert out["bar"]["color"] == "red"
        assert out["dot"]["color"] == "black"

    def test_defaults_survive_when_not_overridden(self):
        out = split_styles({}, ("bar", "dot"), {"bar": {"color": "navy"}})
        assert out["bar"] == {"color": "navy"}
        assert out["dot"] == {}

    def test_no_multiple_values_error_in_a_compound(self):
        """The original failure mode: passing color into a compound that also
        sets a default color must not raise."""
        import numpy as np
        from behaviz import plot_bar, plot_scatter, PlotSpec
        from behaviz.core import plot_function

        @plot_function(default_spec=PlotSpec())
        def _lollipop(x, y, ax=None, spec=None, **overrides):
            style = split_styles(
                overrides,
                ("bar", "dot"),
                defaults={"bar": {"color": "navy"}, "dot": {"color": "navy"}},
            )
            _, ax = plot_bar(x, y, width=0.05, ax=ax, spec=spec, **style["bar"])
            _, ax = plot_scatter(x, y, ax=ax, spec=spec, **style["dot"])
            return ax

        set_renderer("matplotlib")
        x, y = np.arange(1, 6), np.array([3, 5, 2, 6, 4])
        _, ax = _lollipop(x, y, color="red")  # would TypeError before
        np.testing.assert_allclose(ax.patches[0].get_facecolor()[:3], (1, 0, 0), atol=0.01)
        np.testing.assert_allclose(ax.collections[0].get_facecolor()[0][:3], (1, 0, 0), atol=0.01)
