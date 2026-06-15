"""group= / hue= — per-category series, colors, legends, and dodging.

Covers behaviz/core/grouping.py, the palette + dodger helpers, and the
decorator's grouping hook, end to end across backends.
"""

import numpy as np
import pytest

import behaviz as bv
from behaviz import BehavizDataError
from behaviz.core.palette import categorical_palette, resolve_palette
from behaviz.manipulations.dodger import dodge_offsets, get_dodge, CenteredDodge, StackedDodge

pd = pytest.importorskip("pandas")

ALL_BACKENDS = ["matplotlib", "seaborn", "bokeh"]
MPL_BACKENDS = ["matplotlib", "seaborn"]


@pytest.fixture(autouse=True)
def reset_renderer():
    yield
    bv.set_renderer("matplotlib")


@pytest.fixture
def tidy():
    """3 conditions x 2 subjects x 10 timepoints, tidy long-form."""
    rows = []
    for cond in ["A", "B", "C"]:
        for subj in ["s1", "s2"]:
            for ti in np.linspace(0, 1, 10):
                rows.append({"t": ti, "v": np.sin(ti * 6) + {"A": 0, "B": 1, "C": 2}[cond], "cond": cond, "subj": subj})
    return pd.DataFrame(rows)


@pytest.fixture
def agg(tidy):
    a = tidy.groupby(["cond", "subj"], as_index=False)["v"].mean()
    a["ci"] = a["cond"].map({"A": 0, "B": 1, "C": 2})
    return a


def _legend_n(ax):
    leg = ax.get_legend()
    return 0 if leg is None else len(leg.get_texts())


# =====================================================================
# Leaf helpers
# =====================================================================


class TestHelpers:
    def test_categorical_palette_distinct(self):
        assert len(set(categorical_palette(8))) == 8
        assert len(categorical_palette(15)) == 15  # spills into tab20

    def test_resolve_palette_none_list_dict(self):
        assert resolve_palette(["a", "b"]) == dict(zip(["a", "b"], categorical_palette(2)))
        assert resolve_palette(["a", "b", "c"], ["#111", "#222"]) == {"a": "#111", "b": "#222", "c": "#111"}
        out = resolve_palette(["a", "b"], {"a": "#abc"})
        assert out["a"] == "#abc" and out["b"] != "#abc"

    def test_dodge_offsets_center_and_width(self):
        assert dodge_offsets(1) == ([0.0], 0.8)
        offs, w = dodge_offsets(2, total_width=0.8)
        assert offs == [-0.2, 0.2] and w == 0.4
        offs, _ = dodge_offsets(4)
        assert abs(sum(offs)) < 1e-12  # symmetric about 0

    def test_dodge_registry(self):
        assert isinstance(get_dodge("centered"), CenteredDodge)
        assert isinstance(get_dodge("stacked"), StackedDodge)
        assert get_dodge("stacked").needs_bottom is True
        with pytest.raises(ValueError, match="Unknown dodge"):
            get_dodge("nope")

    def test_stacked_strategy_accumulates_bottom(self):
        s = StackedDodge()
        state: dict = {}
        x = np.array([0.0, 1.0])
        p0 = s.place(0, 2, x, np.array([3.0, 5.0]), total_width=0.8, state=state)
        p1 = s.place(1, 2, x, np.array([4.0, 1.0]), total_width=0.8, state=state)
        assert list(p0.bottom) == [0.0, 0.0]
        assert list(p1.bottom) == [3.0, 5.0]      # sits on level 0
        assert p1.width == 0.8                     # full width, shared x
        assert list(p1.x) == [0.0, 1.0]


# =====================================================================
# Overlay grouping (line / scatter / step / fill_between)
# =====================================================================


class TestHueOverlay:
    @pytest.mark.parametrize("backend", ALL_BACKENDS)
    def test_hue_makes_one_series_per_category(self, backend, tidy):
        bv.set_renderer(backend)
        fig, ax = bv.plot_line("t", "v", data=tidy, hue="cond")
        if backend == "bokeh":
            lines = [r for r in ax.renderers if type(r.glyph).__name__ == "Line"]
            assert len(lines) == 3
            assert len({r.glyph.line_color for r in lines}) == 3
            assert len(ax.legend) > 0 and len(ax.legend[0].items) == 3
        else:
            assert len(ax.lines) == 3
            assert len({l.get_color() for l in ax.lines}) == 3
            assert _legend_n(ax) == 3

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_hue_scatter(self, backend, tidy):
        bv.set_renderer(backend)
        fig, ax = bv.plot_scatter("t", "v", data=tidy, hue="cond")
        assert len(ax.collections) == 3

    def test_hue_order_overrides_category_order(self, tidy):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line("t", "v", data=tidy, hue="cond", hue_order=["C", "B", "A"])
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        assert labels == ["C", "B", "A"]

    def test_palette_dict_controls_colors(self, tidy):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line("t", "v", data=tidy, hue="cond", palette={"A": "#ff0000", "B": "#00ff00", "C": "#0000ff"})
        colors = {l.get_color() for l in ax.lines}
        assert {"#ff0000", "#00ff00", "#0000ff"} == colors


class TestGroupOverlay:
    def test_group_same_color_no_legend(self, tidy):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line("t", "v", data=tidy, group="subj")
        assert len(ax.lines) == 2
        assert len({l.get_color() for l in ax.lines}) == 1
        assert _legend_n(ax) == 0

    def test_group_respects_user_color(self, tidy):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line("t", "v", data=tidy, group="subj", color="#aa0000")
        assert {l.get_color() for l in ax.lines} == {"#aa0000"}

    def test_group_and_hue(self, tidy):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line("t", "v", data=tidy, group="subj", hue="cond")
        assert len(ax.lines) == 6                      # 2 subjects x 3 conditions
        assert len({l.get_color() for l in ax.lines}) == 3   # colored by hue only
        assert _legend_n(ax) == 3                      # deduped to hue categories


# =====================================================================
# Dodge grouping (bar / errorbar)
# =====================================================================


class TestDodge:
    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_bar_hue_dodges_and_narrows(self, backend, agg):
        bv.set_renderer(backend)
        fig, ax = bv.plot_bar("ci", "v", data=agg, hue="subj")
        assert len(ax.patches) == 6
        centers = sorted({round(p.get_x() + p.get_width() / 2, 3) for p in ax.patches})
        assert len(centers) == 6                       # every bar at a distinct x
        assert all(abs(p.get_width() - 0.4) < 1e-9 for p in ax.patches)  # 0.8 / 2 levels
        assert _legend_n(ax) == 2

    def test_bar_group_dodges_same_color(self, agg):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_bar("ci", "v", data=agg, group="subj")
        assert len(ax.patches) == 6
        assert len({p.get_facecolor() for p in ax.patches}) == 1
        assert _legend_n(ax) == 0

    def test_errorbar_hue_dodges(self, agg):
        bv.set_renderer("matplotlib")
        agg = agg.assign(err=0.1)
        fig, ax = bv.plot_errorbar("ci", "v", "err", data=agg, hue="subj")
        # two colored containers, x shifted per level
        assert _legend_n(ax) == 2

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_bar_stacked(self, backend):
        bv.set_renderer(backend)
        data = {"ci": [0, 1, 0, 1], "v": [3, 5, 4, 1], "year": ["a", "a", "b", "b"]}
        fig, ax = bv.plot_bar("ci", "v", data=data, hue="year", dodge="stacked")
        # full width, shared x, level "b" stacked on "a"
        assert all(abs(p.get_width() - 0.8) < 1e-9 for p in ax.patches)
        assert len({round(p.get_x() + p.get_width() / 2, 6) for p in ax.patches}) == 2
        at0 = sorted((round(p.get_y(), 3), round(p.get_y() + p.get_height(), 3))
                     for p in ax.patches if abs(p.get_x() + p.get_width() / 2) < 0.01)
        assert at0 == [(0.0, 3.0), (3.0, 7.0)]

    def test_bar_stacked_bokeh(self):
        bv.set_renderer("bokeh")
        data = {"ci": [0, 1, 0, 1], "v": [3, 5, 4, 1], "year": ["a", "a", "b", "b"]}
        fig, ax = bv.plot_bar("ci", "v", data=data, hue="year", dodge="stacked")
        tops = {round(t, 3) for r in ax.renderers if hasattr(r, "data_source")
                for t in r.data_source.data.get("top", [])}
        assert 7.0 in tops  # 3 + 4 stacked at ci=0

    def test_stacked_default_is_centered(self, agg):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_bar("ci", "v", data=agg, hue="subj")  # no dodge= → centered
        assert all(abs(p.get_width() - 0.4) < 1e-9 for p in ax.patches)


# =====================================================================
# Validation
# =====================================================================


class TestErrors:
    def test_hue_without_data_raises(self):
        bv.set_renderer("matplotlib")
        with pytest.raises(BehavizDataError, match="no `data=`"):
            bv.plot_line("t", "v", hue="cond")

    def test_grouping_on_unsupported_plot_raises(self):
        bv.set_renderer("matplotlib")
        rng = np.random.default_rng(0)
        with pytest.raises(BehavizDataError, match="does not support"):
            bv.plot_violin([0, 1], [rng.normal(size=5), rng.normal(size=5)], hue="x")

    def test_dodge_plot_rejects_group_and_hue_together(self, agg):
        bv.set_renderer("matplotlib")
        with pytest.raises(BehavizDataError, match="not both"):
            bv.plot_bar("ci", "v", data=agg, group="subj", hue="cond")

    def test_length_mismatch_raises(self):
        bv.set_renderer("matplotlib")
        data = {"x": [0, 1, 2], "y": [1, 2, 3], "g": ["a", "b"]}  # g shorter
        with pytest.raises(BehavizDataError):
            bv.plot_line("x", "y", data=data, hue="g")

    def test_dodge_on_overlay_plot_raises(self):
        bv.set_renderer("matplotlib")
        data = {"x": [0, 1], "y": [1, 2], "g": ["a", "b"]}
        with pytest.raises(BehavizDataError, match="dodge="):
            bv.plot_line("x", "y", data=data, hue="g", dodge="centered")

    def test_stacked_errorbar_raises(self):
        bv.set_renderer("matplotlib")
        data = {"ci": [0, 1], "v": [1, 2], "e": [0.1, 0.1], "g": ["a", "b"]}
        with pytest.raises(BehavizDataError, match="stack"):
            bv.plot_errorbar("ci", "v", "e", data=data, hue="g", dodge="stacked")


# =====================================================================
# Isolation — no group/hue is unchanged
# =====================================================================


class TestIsolation:
    def test_plain_call_unaffected(self):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line([0, 1, 2], [1, 2, 3])
        assert len(ax.lines) == 1
        assert _legend_n(ax) == 0

    def test_stray_palette_without_hue_does_not_leak(self):
        bv.set_renderer("matplotlib")
        # palette with no group/hue is dropped, not forwarded to the backend
        fig, ax = bv.plot_line([0, 1, 2], [1, 2, 3], palette=["#111"])
        assert len(ax.lines) == 1
