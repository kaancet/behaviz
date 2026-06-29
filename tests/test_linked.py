"""Linked plots (shared CDS) + the Panel dashboard layout."""

import numpy as np
import pytest

import behaviz as bv


@pytest.fixture(autouse=True)
def reset_renderer():
    yield
    bv.set_renderer("matplotlib")


@pytest.fixture
def src():
    rng = np.random.default_rng(0)
    return bv.linked({"x": rng.normal(size=50), "y": rng.normal(size=50), "z": rng.normal(size=50)})


def _glyph_source(fig):
    from bokeh.models import GlyphRenderer

    return [r.data_source for r in fig.renderers if isinstance(r, GlyphRenderer)][0]


class TestLinkedBokeh:
    def test_plots_share_one_cds(self, src):
        bv.set_renderer("bokeh")
        f1, _ = bv.linked_plot(src, "scatter", "x", "y")
        f2, _ = bv.linked_plot(src, "line", "x", "z")
        assert _glyph_source(f1) is _glyph_source(f2) is src.cds  # linked selection

    def test_select_tools_added(self, src):
        from bokeh.models import BoxSelectTool, LassoSelectTool

        bv.set_renderer("bokeh")
        fig, _ = bv.linked_plot(src, "scatter", "x", "y")
        kinds = {type(t) for t in fig.tools}
        assert BoxSelectTool in kinds and LassoSelectTool in kinds

    def test_overrides_route(self, src):
        bv.set_renderer("bokeh")
        fig, _ = bv.linked_plot(src, "scatter", "x", "y", color="#123456")
        from bokeh.models import GlyphRenderer

        gr = [r for r in fig.renderers if isinstance(r, GlyphRenderer)][0]
        assert gr.glyph.fill_color == "#123456"

    def test_normal_plots_unaffected(self, src):
        # the generic pipeline is untouched: a normal plot makes its own source
        bv.set_renderer("bokeh")
        fig, _ = bv.plot_scatter("x", "y", data=src)
        assert _glyph_source(fig) is not src.cds

    def test_falls_back_on_static_backend(self, src):
        # off bokeh, linked_plot just draws the normal primitive (no linking)
        bv.set_renderer("matplotlib")
        _, ax = bv.linked_plot(src, "scatter", "x", "y")
        assert len(ax.collections) > 0


class TestDashboard:
    def test_layout_operators(self, src):
        pn = pytest.importorskip("panel")
        bv.set_renderer("bokeh")
        f1, _ = bv.linked_plot(src, "scatter", "x", "y")
        f2, _ = bv.linked_plot(src, "scatter", "x", "z")
        row = bv.view(f1) | f2
        assert isinstance(row.panel(), pn.Row) and len(row.panel()) == 2
        assert isinstance((row / f1).panel(), pn.Column)

    def test_row_col_helpers(self, src):
        pn = pytest.importorskip("panel")
        bv.set_renderer("bokeh")
        f1, _ = bv.linked_plot(src, "scatter", "x", "y")
        f2, _ = bv.linked_plot(src, "scatter", "x", "z")
        assert isinstance(bv.row(f1, f2).panel(), pn.Row)
        assert isinstance(bv.col(f1, f2).panel(), pn.Column)
