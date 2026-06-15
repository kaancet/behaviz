"""Unified figure output: ``bv.save`` dispatch/validation and ``bv.canvas``.

Covers behaviz/io.py, the per-backend Renderer.save/show, and the active-axes
hook the context manager installs in the plot decorator.
"""

import numpy as np
import pytest

import behaviz as bv
from behaviz import BehavizSaveError
from behaviz.core.context import get_active_canvas

ALL_BACKENDS = ["matplotlib", "seaborn", "bokeh"]


@pytest.fixture
def xy():
    x = np.linspace(0, 6, 50)
    return x, np.sin(x)


@pytest.fixture(autouse=True)
def reset_renderer():
    yield
    bv.set_renderer("matplotlib")


# =====================================================================
# bv.save — format/backend dispatch and validation
# =====================================================================


class TestSaveMatplotlib:
    @pytest.mark.parametrize("backend", ["matplotlib", "seaborn"])
    @pytest.mark.parametrize("ext", [".png", ".pdf", ".svg"])
    def test_writes_supported_formats(self, backend, ext, xy, tmp_path):
        bv.set_renderer(backend)
        fig, ax = bv.plot_line(*xy)
        out = tmp_path / f"fig{ext}"
        returned = bv.save(fig, out)
        assert out.exists() and out.stat().st_size > 0
        assert returned == str(out)

    @pytest.mark.parametrize("backend", ["matplotlib", "seaborn"])
    def test_html_rejected(self, backend, xy, tmp_path):
        bv.set_renderer(backend)
        fig, ax = bv.plot_line(*xy)
        with pytest.raises(BehavizSaveError, match="HTML"):
            bv.save(fig, tmp_path / "fig.html")

    def test_unknown_extension_lists_supported(self, xy, tmp_path):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line(*xy)
        with pytest.raises(BehavizSaveError, match=r"\.png"):
            bv.save(fig, tmp_path / "fig.xyz")

    def test_dpi_kwarg_forwarded(self, xy, tmp_path):
        bv.set_renderer("matplotlib")
        fig, ax = bv.plot_line(*xy)
        out = tmp_path / "hi.png"
        bv.save(fig, out, dpi=72)
        assert out.exists()


class TestSaveBokeh:
    def test_html_written(self, xy, tmp_path):
        bv.set_renderer("bokeh")
        fig, ax = bv.plot_line(*xy)
        out = tmp_path / "fig.html"
        bv.save(fig, out)
        assert out.exists() and out.stat().st_size > 0

    def test_png_needs_export_deps_or_raises(self, xy, tmp_path):
        bv.set_renderer("bokeh")
        fig, ax = bv.plot_line(*xy)
        out = tmp_path / "fig.png"
        try:
            import selenium  # noqa: F401
        except ImportError:
            with pytest.raises(BehavizSaveError, match="selenium"):
                bv.save(fig, out)
        else:
            # selenium present but a driver may still be missing — either it
            # works or it raises our wrapped error, never a raw bokeh error.
            try:
                bv.save(fig, out)
                assert out.exists()
            except BehavizSaveError:
                pass

    def test_unknown_extension_rejected(self, xy, tmp_path):
        bv.set_renderer("bokeh")
        fig, ax = bv.plot_line(*xy)
        with pytest.raises(BehavizSaveError):
            bv.save(fig, tmp_path / "fig.xyz")


# =====================================================================
# bv.canvas — implicit active-axes + save on exit
# =====================================================================


class TestCanvas:
    def test_implicit_axes_collects_onto_one_figure_mpl(self, xy, tmp_path):
        bv.set_renderer("matplotlib")
        out = tmp_path / "c.png"
        with bv.canvas(save=out) as ax:
            bv.plot_line(*xy)  # no ax=
            bv.plot_scatter(xy[0], xy[1] + 0.1)
        assert len(ax.lines) == 1
        assert len(ax.collections) == 1
        assert out.exists() and out.stat().st_size > 0

    def test_implicit_axes_bokeh(self, xy, tmp_path):
        bv.set_renderer("bokeh")
        out = tmp_path / "c.html"
        with bv.canvas(save=out) as fig:
            bv.plot_line(*xy)
            bv.plot_scatter(xy[0], xy[1] + 0.1)
        # one bokeh figure carrying both glyphs
        assert sum(hasattr(r, "glyph") for r in fig.renderers) >= 2
        assert out.exists()

    def test_no_save_when_save_omitted(self, xy):
        bv.set_renderer("matplotlib")
        with bv.canvas() as ax:
            bv.plot_line(*xy)
        assert len(ax.lines) == 1  # still drew, just nothing written

    def test_active_canvas_cleared_after_block(self, xy):
        bv.set_renderer("matplotlib")
        assert get_active_canvas() is None
        with bv.canvas() as ax:
            assert get_active_canvas() is not None
        assert get_active_canvas() is None

    def test_plain_call_after_block_makes_new_figure(self, xy):
        bv.set_renderer("matplotlib")
        with bv.canvas() as ax:
            bv.plot_line(*xy)
        fig2, ax2 = bv.plot_line(*xy)
        assert ax2 is not ax

    def test_exception_inside_block_does_not_save_and_clears(self, xy, tmp_path):
        bv.set_renderer("matplotlib")
        out = tmp_path / "nope.png"
        with pytest.raises(RuntimeError):
            with bv.canvas(save=out) as ax:
                bv.plot_line(*xy)
                raise RuntimeError("boom")
        assert not out.exists()
        assert get_active_canvas() is None

    def test_canvas_spec_inherited_by_bare_calls(self, xy):
        bv.set_renderer("matplotlib")
        spec = bv.PlotSpec.from_labels("Time", "Voltage")
        with bv.canvas(spec=spec) as ax:
            bv.plot_line(*xy)  # inherits the canvas spec
        assert ax.get_xlabel() == "Time"
        assert ax.get_ylabel() == "Voltage"

    def test_canvas_spec_survives_data_columns(self):
        # regression: data= columns trigger autolabel, which used to replace the
        # spec and break canvas inheritance (the title/scale were lost)
        bv.set_renderer("matplotlib")
        data = {"t": [1, 2, 3], "v": [1, 4, 9]}
        spec = bv.PlotSpec(x=bv.AxisSpec(label="Time", scale=bv.ScaleType.LOG), title="Canvas")
        with bv.canvas(spec=spec) as ax:
            bv.plot_line("t", "v", data=data)
        assert ax.get_title() == "Canvas"
        assert ax.get_xscale() == "log"

    def test_canvas_on_existing_axes_with_spec(self):
        bv.set_renderer("matplotlib")
        import matplotlib.pyplot as plt

        _, axs = plt.subplots(1, 2)
        spec = bv.PlotSpec.from_labels("Time", "Voltage")
        with bv.canvas(ax=axs[0], spec=spec):
            bv.plot_line([0, 1, 2], [1, 2, 3])
        assert axs[0].get_xlabel() == "Time"
        assert len(axs[0].lines) == 1 and len(axs[1].lines) == 0

    def test_explicit_spec_on_inner_call_wins(self, xy):
        bv.set_renderer("matplotlib")
        canvas_spec = bv.PlotSpec.from_labels("Time", "Voltage")
        inner_spec = bv.PlotSpec.from_labels("Custom", "Axis")
        with bv.canvas(spec=canvas_spec) as ax:
            bv.plot_line(*xy, spec=inner_spec)
        assert ax.get_xlabel() == "Custom"
