"""Multi-panel layout: the shared placement core, the three backends' grids,
and the capabilities bokeh deliberately refuses."""

import matplotlib
matplotlib.use("Agg")  # must happen before any other mpl import

import numpy as np
import pytest

import behaviz as bv
from behaviz import set_renderer
from behaviz.core.layout import Placement, parse_mosaic, plain_grid, resolve, check_ratios
from behaviz.backends.matplotlib.backend import MatplotlibRenderer
from behaviz.backends.seaborn.backend import SeabornRenderer

BACKENDS = ["matplotlib", "seaborn", "bokeh"]
MPL_ONLY = ["matplotlib", "seaborn"]


@pytest.fixture
def xy():
    x = np.arange(1, 11)
    return x, x**2


@pytest.fixture(autouse=True)
def restore_backend():
    yield
    set_renderer("matplotlib")


# ── shared placement core (no backend) ───────────────────────────────────────
class TestMosaicParsing:
    def test_spans(self):
        placements, nrows, ncols = parse_mosaic("AAB\nCCB")
        assert (nrows, ncols) == (2, 3)
        by_name = {p.name: p for p in placements}
        assert by_name["A"] == Placement("A", 0, 0, 1, 2)
        assert by_name["B"] == Placement("B", 0, 2, 2, 1)
        assert by_name["C"] == Placement("C", 1, 0, 1, 2)

    def test_dot_leaves_cell_empty(self):
        placements, nrows, ncols = parse_mosaic("A.B")
        assert (nrows, ncols) == (1, 3)
        assert {p.name for p in placements} == {"A", "B"}

    def test_list_of_lists_accepted(self):
        placements, nrows, ncols = parse_mosaic([["A", "A"], ["B", "C"]])
        assert (nrows, ncols) == (2, 2)
        assert {p.name for p in placements} == {"A", "B", "C"}

    def test_ragged_rejected(self):
        with pytest.raises(ValueError, match="same width"):
            parse_mosaic("AAB\nCC")

    def test_non_rectangular_panel_rejected(self):
        with pytest.raises(ValueError, match="solid rectangle"):
            parse_mosaic("ABA\nCCC")

    def test_all_empty_rejected(self):
        with pytest.raises(ValueError, match="no panels"):
            parse_mosaic("..\n..")


class TestPlainGrid:
    def test_one_placement_per_cell(self):
        placements = plain_grid(2, 3)
        assert len(placements) == 6
        assert all(p.rowspan == 1 and p.colspan == 1 for p in placements)

    def test_zero_rejected(self):
        with pytest.raises(ValueError, match="at least 1"):
            plain_grid(0, 2)

    def test_resolve_rejects_both_forms(self):
        with pytest.raises(ValueError, match="not both"):
            resolve(nrows=2, ncols=2, mosaic="AB")

    def test_check_ratios_length(self):
        with pytest.raises(ValueError, match="width_ratios"):
            check_ratios([1, 2, 3], None, nrows=2, ncols=2)
        with pytest.raises(ValueError, match="height_ratios"):
            check_ratios(None, [1], nrows=2, ncols=2)


# ── grids on every backend ───────────────────────────────────────────────────
@pytest.mark.parametrize("backend", BACKENDS)
class TestGridAllBackends:
    def test_shape_and_plotting(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        with bv.grid(2, 2) as axs:
            assert axs.shape == (2, 2)
            assert all(a is not None for a in np.ravel(axs))
            bv.plot_line(x, y, ax=axs[0, 0])

    def test_mosaic_yields_dict(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        with bv.grid(mosaic="AAB\nCCB") as axs:
            assert set(axs) == {"A", "B", "C"}
            bv.plot_line(x, y, ax=axs["A"])

    def test_ratios_spacing_sharing_suptitle(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        with bv.grid(
            2, 2, width_ratios=[2, 1], height_ratios=[1, 3],
            sharex=True, sharey=True, wspace=5, hspace=5, suptitle="Fig 1",
        ) as axs:
            bv.plot_line(x, y, ax=axs[0, 0])

    def test_per_panel_spec(self, backend, xy):
        """Feature #4: each panel takes its own spec via the plot call."""
        set_renderer(backend)
        x, y = xy
        a = bv.PlotSpec(x=bv.AxisSpec(label="Left"))
        b = bv.PlotSpec(x=bv.AxisSpec(label="Right"))
        with bv.grid(1, 2) as axs:
            bv.plot_line(x, y, ax=axs[0, 0], spec=a)
            bv.plot_line(x, y, ax=axs[0, 1], spec=b)

    def test_bad_ratio_length_rejected(self, backend):
        set_renderer(backend)
        with pytest.raises(ValueError, match="width_ratios"):
            with bv.grid(2, 2, width_ratios=[1, 2, 3]):
                pass


class TestMatplotlibGridDetails:
    def test_spans_map_to_gridspec(self, xy):
        set_renderer("matplotlib")
        with bv.grid(mosaic="AAB\nCCB") as axs:
            # B spans both rows, so it is taller than A
            assert axs["B"].get_position().height > axs["A"].get_position().height
            # A spans two columns, so it is wider than B
            assert axs["A"].get_position().width > axs["B"].get_position().width

    def test_sharex_links_axes(self, xy):
        set_renderer("matplotlib")
        with bv.grid(1, 2, sharex=True) as axs:
            axs[0, 0].set_xlim(3, 7)
            assert tuple(axs[0, 1].get_xlim()) == (3, 7)

    def test_suptitle_set(self):
        set_renderer("matplotlib")
        with bv.grid(1, 1, suptitle="Fig 1") as axs:
            assert axs[0, 0].get_figure()._suptitle.get_text() == "Fig 1"


class TestBokehGridDetails:
    def test_returns_gridplot_with_spans(self, xy):
        set_renderer("bokeh")
        from behaviz.backends.renderer_manager import get_renderer
        from behaviz.core.layout import parse_mosaic

        placements, nrows, ncols = parse_mosaic("AAB\nCCB")
        fig, axes = get_renderer().make_grid(bv.PlotSpec(), placements, nrows, ncols)
        assert type(fig).__name__ == "GridPlot"
        spans = {c[0]: (c[3], c[4]) for c in fig.children}
        assert spans[axes["B"]] == (2, 1)  # B spans two rows
        assert spans[axes["A"]] == (1, 2)  # A spans two columns

    def test_sharex_shares_range_object(self):
        set_renderer("bokeh")
        from behaviz.backends.renderer_manager import get_renderer
        from behaviz.core.layout import plain_grid

        _, axes = get_renderer().make_grid(bv.PlotSpec(), plain_grid(1, 2), 1, 2, sharex=True)
        a, b = axes["r0c0"], axes["r0c1"]
        assert a.x_range is b.x_range

    def test_grid_saves_to_html(self, xy, tmp_path):
        """Regression guard: GridPlot has no .title — save() must not blow up."""
        set_renderer("bokeh")
        x, y = xy
        out = tmp_path / "g.html"
        with bv.grid(2, 2, save=str(out)) as axs:
            bv.plot_line(x, y, ax=axs[0, 0])
        assert out.exists() and out.stat().st_size > 0


# ── seaborn inherits rather than reimplements ────────────────────────────────
def test_seaborn_inherits_matplotlib_layout():
    for name in ("make_grid", "make_inset", "shared_colorbar", "set_layout_engine"):
        assert getattr(SeabornRenderer, name) is getattr(MatplotlibRenderer, name)


# ── optional capabilities: mpl/seaborn do them, bokeh refuses ────────────────
@pytest.mark.parametrize("backend", MPL_ONLY)
class TestOptionalCapabilitiesSupported:
    def test_layout_engine(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        with bv.grid(1, 2, layout="constrained") as axs:
            bv.plot_line(x, y, ax=axs[0, 0])
            assert type(axs[0, 0].get_figure().get_layout_engine()).__name__ == "ConstrainedLayoutEngine"

    def test_inset(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        with bv.grid(1, 1) as axs:
            ins = bv.inset(axs[0, 0], (0.6, 0.1, 0.35, 0.3))
            bv.plot_line(x, y, ax=ins)
            assert ins is not axs[0, 0]

    def test_shared_colorbar(self, backend):
        set_renderer(backend)
        img = np.random.rand(6, 6)
        with bv.grid(1, 2) as axs:
            mappable = None
            for c in range(2):
                fig, ax = bv.plot_image(img, ax=axs[0, c])
                mappable = ax.images[-1]
            cb = bv.shared_colorbar(fig, axs, mappable=mappable)
            assert type(cb).__name__ == "Colorbar"

    def test_layout_engine_does_not_fight_tight_layout(self, backend, xy, recwarn):
        set_renderer(backend)
        x, y = xy
        with bv.grid(1, 2, layout="constrained") as axs:
            bv.plot_line(x, y, ax=axs[0, 0])
        assert not [w for w in recwarn if "layout has changed" in str(w.message)]


class TestBokehRefusesUnsupported:
    def test_layout_engine_raises(self):
        set_renderer("bokeh")
        with pytest.raises(NotImplementedError, match="layout engine"):
            with bv.grid(1, 2, layout="tight"):
                pass

    def test_inset_raises(self):
        set_renderer("bokeh")
        with pytest.raises(NotImplementedError, match="inset"):
            bv.inset(None, (0, 0, 1, 1))

    def test_shared_colorbar_raises(self):
        set_renderer("bokeh")
        with pytest.raises(NotImplementedError, match="colorbar"):
            bv.shared_colorbar(None, [None], mappable=object())

    def test_default_grid_does_not_raise(self, xy):
        """layout=None must stay silent — only an explicit engine refuses."""
        set_renderer("bokeh")
        x, y = xy
        with bv.grid(1, 2) as axs:
            bv.plot_line(x, y, ax=axs[0, 0])
