"""
Tests for the spec dataclasses:
  AxisSpec, FigureSpec, LineSpec, PlotSpec
"""
import pytest
from behaviz.spec import AxisSpec, ScaleType, FigureSpec, LegendPosition, PlotSpec

# ========
# AxisSpec
# ========
class TestAxisSpec:
    def test_defaults(self):
        ax = AxisSpec()
        assert ax.label == ""
        assert ax.unit == ""
        assert ax.scale == ScaleType.LINEAR
        assert ax.lim is None
        assert ax.grid is True
        assert ax.grid_minor is False
        assert ax.invert is False

    def test_full_label_with_unit(self):
        ax = AxisSpec(label="Contrast", unit="%")
        assert ax.full_label == "Contrast (%)"

    def test_full_label_without_unit(self):
        ax = AxisSpec(label="Time")
        assert ax.full_label == "Time"

    def test_full_label_empty(self):
        ax = AxisSpec()
        assert ax.full_label == ""

    def test_custom_values(self):
        ax = AxisSpec(label="X", unit="s", lim=(0, 10), ticks=[0, 5, 10], invert=True)
        assert ax.lim == (0, 10)
        assert ax.ticks == [0, 5, 10]
        assert ax.invert is True

    def test_scale_types(self):
        for scale in ScaleType:
            ax = AxisSpec(scale=scale)
            assert ax.scale == scale
            
            
# ==========
# FigureSpec
# ==========
class TestFigureSpec:
    def test_defaults(self):
        fs = FigureSpec()
        assert fs.figsize == (12, 8)
        assert fs.dpi == 120
        assert fs.tight is True
        assert fs.style == "default"

    def test_custom_values(self):
        fs = FigureSpec(figsize=(6, 4), dpi=72, style="dark_background")
        assert fs.figsize == (6, 4)
        assert fs.dpi == 72
        assert fs.style == "dark_background"        
        

# ========
# PlotSpec
# ========
class TestPlotSpec:
    def test_defaults(self):
        ps = PlotSpec()
        assert ps.title == ""
        assert isinstance(ps.x, AxisSpec)
        assert isinstance(ps.y, AxisSpec)
        assert isinstance(ps.figure, FigureSpec)
        assert ps.show_legend is False
        assert ps.legend_pos == LegendPosition.BEST
        assert ps.annotations == []
        assert ps.post_hook is None

    # -- from_labels factory -------------------------------------------------
    def test_from_labels_sets_axes(self):
        ps = PlotSpec.from_labels("Contrast", "Reaction time", xunit="%", yunit="ms")
        assert ps.x.label == "Contrast"
        assert ps.x.unit == "%"
        assert ps.y.label == "Reaction time"
        assert ps.y.unit == "ms"

    def test_from_labels_accepts_extra_kwargs(self):
        ps = PlotSpec.from_labels("X", "Y", title="My Plot")
        assert ps.title == "My Plot"

    # -- preset factory ------------------------------------------------------
    @pytest.mark.parametrize("name", ["paper", "poster", "notebook", "dark"])
    def test_preset_returns_plotspec(self, name):
        ps = PlotSpec.preset(name)
        assert isinstance(ps, PlotSpec)

    def test_preset_paper_no_grid(self):
        ps = PlotSpec.preset("paper")
        assert ps.x.grid is False
        assert ps.y.grid is False

    def test_preset_notebook_has_grid(self):
        ps = PlotSpec.preset("notebook")
        assert ps.x.grid is True
        assert ps.y.grid is True

    def test_preset_custom_requires_dict(self):
        with pytest.raises(AssertionError):
            PlotSpec.preset("custom", style_dict=None)

    def test_preset_custom_with_dict(self):
        ps = PlotSpec.preset("custom", style_dict={"figure.figsize": (5, 5), "figure.dpi": 150})
        assert isinstance(ps, PlotSpec)

    def test_preset_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            PlotSpec.preset("nonexistent")

    # -- mutation-free helpers -----------------------------------------------
    def test_with_title(self):
        ps = PlotSpec().with_title("Hello")
        assert ps.title == "Hello"

    def test_with_title_original_unchanged(self):
        original = PlotSpec()
        _ = original.with_title("Changed")
        assert original.title == ""

    def test_with_xlim(self):
        ps = PlotSpec().with_xlim(-1, 1)
        assert ps.x.lim == (-1, 1)

    def test_with_ylim(self):
        ps = PlotSpec().with_ylim(0, 100)
        assert ps.y.lim == (0, 100)

    def test_with_scale_x(self):
        ps = PlotSpec().with_scale("x", "log")
        assert ps.x.scale == ScaleType.LOG
        assert ps.y.scale == ScaleType.LINEAR  # y untouched

    def test_with_scale_y(self):
        ps = PlotSpec().with_scale("y", "log")
        assert ps.y.scale == ScaleType.LOG

    def test_with_scale_both(self):
        ps = PlotSpec().with_scale("both", "log")
        assert ps.x.scale == ScaleType.LOG
        assert ps.y.scale == ScaleType.LOG

    def test_with_size(self):
        ps = PlotSpec().with_size((6, 4))
        assert ps.figure.figsize == (6, 4)

    def test_with_annotation_appends(self):
        ps = PlotSpec()
        ps2 = ps.with_annotation(1, 2, "hello")
        assert len(ps2.annotations) == 1
        assert ps2.annotations[0]["text"] == "hello"
        assert len(ps.annotations) == 0  # original untouched

    def test_with_annotation_chaining(self):
        ps = PlotSpec().with_annotation(0, 0, "A").with_annotation(1, 1, "B")
        assert len(ps.annotations) == 2

    def test_with_hook(self):
        def my_hook(ax, spec):
            pass
        ps = PlotSpec().with_hook(my_hook)
        assert ps.post_hook is my_hook
