"""
Tests for the plot-registry architecture and multi-backend correctness.

Coverage:
  1. Registry completeness  — validate_registry() catches gaps; PlotType fields are correct
  2. Backend switching      — set_renderer() / get_renderer() work and are isolated
  3. Per-backend rendering  — every plot type produces the expected artist(s) on each backend
  4. Kwarg passthrough      — canonical overrides reach the rendered artist on each backend
  5. Canonical translation  — cross-backend aliases (color, linewidth, …) map correctly
  6. Overrider routing      — VALID_CALL_KWARGS covers every registered plot type
  7. Factory-generated fns  — generated plot functions behave identically to hand-written ones
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
import matplotlib.pyplot as plt
import matplotlib.figure

import behaviz
from behaviz import set_renderer, get_renderer
from behaviz.core.plot_registry import ALL_PLOTS, PlotType, get_plot
from behaviz.core.registry_validation import (
    validate_registry,
    _check_renderer_abc,
    _check_concrete_backends,
    _check_overriders,
    _all_concrete_subclasses,
)
from behaviz.backends.renderer import Renderer
from behaviz.backends.override import Overrider
from behaviz.backends.matplotlib.overrider import MatplotlibOverrider
from behaviz.backends.seaborn.overrider import SeabornOverrider
from behaviz.backends.bokeh.overrider import BokehOverrider


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

ALL_BACKENDS = ["matplotlib", "seaborn", "bokeh"]
MPL_BACKENDS = ["matplotlib", "seaborn"]  # both render onto mpl Axes


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture(autouse=True)
def reset_renderer():
    """Restore matplotlib renderer after every test so state never leaks."""
    yield
    set_renderer("matplotlib")


@pytest.fixture
def xy():
    x = np.linspace(0, 5, 20)
    y = np.sin(x)
    return x, y


@pytest.fixture
def xy_pos(xy):
    """Strictly positive y — needed for bar heights."""
    x, y = xy
    return x, np.abs(y) + 0.1


@pytest.fixture
def xy_err(xy):
    x, y = xy
    return x, y, np.full_like(y, 0.1)


@pytest.fixture
def group_data():
    rng = np.random.default_rng(42)
    positions = np.array([1.0, 2.0, 3.0])
    ys = [rng.normal(loc=p, scale=0.5, size=40) for p in positions]
    return positions, ys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mpl_ax(ax):
    """True when ax is a matplotlib Axes (covers both mpl and seaborn backends)."""
    return isinstance(ax, plt.Axes)


def _bokeh_fig(fig):
    from bokeh.plotting import figure as BokehFigure

    return isinstance(fig, BokehFigure)


def _glyph_prop(ax, prop: str):
    """Read a property from the first Bokeh GlyphRenderer on ax."""
    return getattr(ax.renderers[0].glyph, prop)


# ---------------------------------------------------------------------------
# 1. Registry completeness
# ---------------------------------------------------------------------------


class TestRegistryCompleteness:
    def test_validate_registry_passes_clean(self):
        """The live registry must be fully consistent — no gaps allowed."""
        validate_registry()  # raises RuntimeError if anything is missing

    def test_all_plots_not_empty(self):
        assert len(ALL_PLOTS) > 0

    def test_all_plots_keys_match_names(self):
        for key, pt in ALL_PLOTS.items():
            assert key == pt.name, f"ALL_PLOTS key '{key}' does not match PlotType.name '{pt.name}'"

    def test_every_plot_has_all_backends(self):
        for name, pt in ALL_PLOTS.items():
            for backend in ALL_BACKENDS:
                assert backend in pt.backend_methods, (
                    f"PlotType '{name}' is missing backend_methods entry for '{backend}'"
                )

    def test_mpl_dummy_args_is_tuple(self):
        for name, pt in ALL_PLOTS.items():
            assert isinstance(pt.mpl_dummy_args, tuple), (
                f"PlotType '{name}'.mpl_dummy_args should be a tuple, got {type(pt.mpl_dummy_args)}"
            )

    def test_get_plot_returns_correct_native_method(self):
        assert get_plot("line", "matplotlib") == "plot"
        assert get_plot("line", "seaborn") == "lineplot"
        assert get_plot("line", "bokeh") == "line"
        assert get_plot("scatter", "matplotlib") == "scatter"
        assert get_plot("bar", "bokeh") == "vbar"

    def test_get_plot_unknown_name_raises(self):
        with pytest.raises(KeyError):
            get_plot("nonexistent_plot", "matplotlib")

    def test_renderer_abc_has_all_methods(self):
        errors = _check_renderer_abc()
        assert errors == [], "\n".join(errors)

    def test_concrete_backends_implement_all_methods(self):
        errors = _check_concrete_backends()
        assert errors == [], "\n".join(errors)

    def test_overriders_cover_all_plot_types(self):
        errors = _check_overriders()
        assert errors == [], "\n".join(errors)

    def test_validate_registry_catches_missing_renderer_method(self):
        """Injecting an unimplemented plot type must produce errors for all three checks."""
        fake = PlotType(
            name="fake_plot",
            backend_methods={"matplotlib": "imshow", "seaborn": "heatmap", "bokeh": "image"},
        )
        ALL_PLOTS["fake_plot"] = fake
        try:
            with pytest.raises(RuntimeError) as exc_info:
                validate_registry()
            msg = str(exc_info.value)
            assert "Renderer ABC is missing abstract method 'fake_plot'" in msg
            assert "MatplotlibRenderer is missing method 'fake_plot'" in msg
            assert "SeabornRenderer is missing method 'fake_plot'" in msg
            assert "BokehRenderer is missing method 'fake_plot'" in msg
            assert "MatplotlibOverrider.VALID_CALL_KWARGS is missing entry for plot type 'fake_plot'" in msg
            assert "SeabornOverrider.VALID_CALL_KWARGS is missing entry for plot type 'fake_plot'" in msg
            assert "BokehOverrider.VALID_CALL_KWARGS is missing entry for plot type 'fake_plot'" in msg
        finally:
            del ALL_PLOTS["fake_plot"]

    def test_all_concrete_subclasses_finds_all_backends(self):
        subs = _all_concrete_subclasses(Renderer)
        names = {cls.__name__ for cls in subs}
        assert "MatplotlibRenderer" in names
        assert "SeabornRenderer" in names
        assert "BokehRenderer" in names

    def test_all_concrete_subclasses_finds_all_overriders(self):
        subs = _all_concrete_subclasses(Overrider)
        names = {cls.__name__ for cls in subs}
        assert "MatplotlibOverrider" in names
        assert "SeabornOverrider" in names
        assert "BokehOverrider" in names


# ---------------------------------------------------------------------------
# 2. Backend switching
# ---------------------------------------------------------------------------


class TestBackendSwitching:
    def test_set_renderer_changes_active_backend(self):
        for backend in ALL_BACKENDS:
            set_renderer(backend)
            assert get_renderer().name == backend

    def test_get_renderer_raises_when_none_set(self):
        from behaviz.backends import renderer_manager

        original = renderer_manager._CURRENT_RENDERER
        renderer_manager._CURRENT_RENDERER = None
        try:
            with pytest.raises(RuntimeError, match="No renderer configured"):
                get_renderer()
        finally:
            renderer_manager._CURRENT_RENDERER = original

    def test_switch_between_backends_multiple_times(self):
        sequence = ["bokeh", "matplotlib", "seaborn", "bokeh", "matplotlib"]
        for backend in sequence:
            set_renderer(backend)
            assert get_renderer().name == backend

    def test_unknown_renderer_raises(self):
        with pytest.raises(ValueError, match="Unknown renderer"):
            set_renderer("d3")

    @pytest.mark.parametrize("backend", ALL_BACKENDS)
    def test_make_figure_returns_correct_types(self, backend):
        set_renderer(backend)
        from behaviz.spec import PlotSpec

        spec = PlotSpec()
        fig, ax = get_renderer().make_figure(spec)
        if backend in MPL_BACKENDS:
            assert isinstance(fig, matplotlib.figure.Figure)
            assert isinstance(ax, plt.Axes)
        else:
            assert _bokeh_fig(fig)


# ---------------------------------------------------------------------------
# 3. Per-backend rendering — artists are actually created
# ---------------------------------------------------------------------------


class TestBackendRendering:
    # ── plot_line ────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_plot_line_adds_one_line_mpl(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        fig, ax = behaviz.plot_line(x, y)
        assert _mpl_ax(ax)
        assert len(ax.get_lines()) == 1

    def test_plot_line_bokeh_adds_renderer(self, xy):
        set_renderer("bokeh")
        x, y = xy
        fig, ax = behaviz.plot_line(x, y)
        assert len(ax.renderers) == 1

    # ── plot_scatter ─────────────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_plot_scatter_adds_collection_mpl(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        fig, ax = behaviz.plot_scatter(x, y)
        assert _mpl_ax(ax)
        assert len(ax.collections) == 1

    def test_plot_scatter_bokeh_adds_renderer(self, xy):
        set_renderer("bokeh")
        x, y = xy
        fig, ax = behaviz.plot_scatter(x, y)
        assert len(ax.renderers) == 1

    # ── plot_errorbar ─────────────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_plot_errorbar_adds_container_mpl(self, backend, xy_err):
        set_renderer(backend)
        x, y, err = xy_err
        fig, ax = behaviz.plot_errorbar(x, y, err)
        assert _mpl_ax(ax)
        assert len(ax.containers) >= 1

    def test_plot_errorbar_bokeh_adds_renderers(self, xy_err):
        set_renderer("bokeh")
        x, y, err = xy_err
        fig, ax = behaviz.plot_errorbar(x, y, err)
        # Bokeh errorbar draws segments + scatter markers
        assert len(ax.renderers) >= 1

    # ── plot_bar ──────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_plot_bar_adds_patches_mpl(self, backend, xy_pos):
        set_renderer(backend)
        x, y = xy_pos
        fig, ax = behaviz.plot_bar(x, y)
        assert _mpl_ax(ax)
        assert len(ax.patches) == len(x)

    def test_plot_bar_bokeh_adds_renderer(self, xy_pos):
        set_renderer("bokeh")
        x, y = xy_pos
        fig, ax = behaviz.plot_bar(x, y)
        assert len(ax.renderers) == 1

    # ── plot_step ─────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_plot_step_adds_line_mpl(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        fig, ax = behaviz.plot_step(x, y)
        assert _mpl_ax(ax)
        assert len(ax.get_lines()) == 1

    def test_plot_step_bokeh_adds_renderer(self, xy):
        set_renderer("bokeh")
        x, y = xy
        fig, ax = behaviz.plot_step(x, y)
        assert len(ax.renderers) == 1

    # ── plot_violin ───────────────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", ALL_BACKENDS)
    def test_plot_violin_returns_bodies(self, backend, group_data):
        set_renderer(backend)
        positions, ys = group_data
        fig, ax, vp = behaviz.plot_violin(positions, ys)
        assert "bodies" in vp
        assert len(vp["bodies"]) == len(positions)

    def test_plot_violin_mpl_adds_collections(self, group_data):
        set_renderer("matplotlib")
        positions, ys = group_data
        fig, ax, vp = behaviz.plot_violin(positions, ys)
        assert _mpl_ax(ax)
        assert len(ax.collections) >= len(positions)

    @pytest.fixture(params=["list_of_arrays", "ndarray_2d"])
    def violin_ys(self, request):
        rng = np.random.default_rng(42)
        if request.param == "list_of_arrays":
            return [rng.normal(size=30), rng.normal(size=25), rng.normal(size=40)]
        return rng.normal(size=(3, 40))  # (n_positions, n_samples)

    @pytest.mark.parametrize("backend", ALL_BACKENDS)
    def test_violin_one_body_per_position(self, backend, violin_ys):
        """One violin per position for both ragged lists and 2-D arrays."""
        set_renderer(backend)
        positions = np.array([1.0, 2.0, 3.0])
        fig, ax, vp = behaviz.plot_violin(positions, violin_ys)
        assert len(vp["bodies"]) == len(positions)

    # ── return-value contract ─────────────────────────────────────────────────

    @pytest.mark.parametrize("backend", ALL_BACKENDS)
    def test_standalone_call_returns_fig_and_ax(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        result = behaviz.plot_line(x, y)
        assert len(result) == 2
        fig, ax = result
        assert fig is not None
        assert ax is not None

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_composite_call_reuses_ax(self, backend, xy):
        """When ax is passed, the same axes object is returned."""
        set_renderer(backend)
        x, y = xy
        _, existing_ax = plt.subplots()
        _, returned_ax = behaviz.plot_line(x, y, ax=existing_ax)
        assert returned_ax is existing_ax

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_multiple_plots_accumulate_on_same_ax(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        _, ax = plt.subplots()
        behaviz.plot_line(x, y, ax=ax)
        behaviz.plot_line(x, y * 0.5, ax=ax)
        assert len(ax.get_lines()) == 2


# ---------------------------------------------------------------------------
# 4. Kwarg passthrough — overrides reach the rendered artist
# ---------------------------------------------------------------------------


class TestKwargPassthrough:
    # ── matplotlib ────────────────────────────────────────────────────────────

    def test_mpl_line_color(self, xy):
        set_renderer("matplotlib")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, color="red")
        assert ax.get_lines()[0].get_color() == "red"

    def test_mpl_line_linewidth(self, xy):
        set_renderer("matplotlib")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, linewidth=3.5)
        assert ax.get_lines()[0].get_linewidth() == pytest.approx(3.5)

    def test_mpl_line_label(self, xy):
        set_renderer("matplotlib")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, label="my series")
        assert ax.get_lines()[0].get_label() == "my series"

    def test_mpl_scatter_color(self, xy):
        set_renderer("matplotlib")
        x, y = xy
        _, ax = behaviz.plot_scatter(x, y, color="blue")
        fc = ax.collections[0].get_facecolor()
        # facecolor is an RGBA array; check that blue channel dominates
        assert fc[0][2] > 0.5

    # ── seaborn ───────────────────────────────────────────────────────────────

    def test_seaborn_line_color(self, xy):
        set_renderer("seaborn")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, color="green")
        assert ax.get_lines()[0].get_color() == "green"

    def test_seaborn_line_linewidth(self, xy):
        set_renderer("seaborn")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, linewidth=2.5)
        assert ax.get_lines()[0].get_linewidth() == pytest.approx(2.5)

    def test_seaborn_line_label(self, xy):
        set_renderer("seaborn")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, label="sns label")
        assert ax.get_lines()[0].get_label() == "sns label"

    def test_seaborn_scatter_color(self, xy):
        set_renderer("seaborn")
        x, y = xy
        _, ax = behaviz.plot_scatter(x, y, color="orange")
        fc = ax.collections[0].get_facecolor()
        # orange: R high, G mid, B low
        assert fc[0][0] > fc[0][2]

    # ── bokeh ─────────────────────────────────────────────────────────────────

    def test_bokeh_line_color(self, xy):
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, line_color="red")
        assert _glyph_prop(ax, "line_color") == "red"

    def test_bokeh_line_width(self, xy):
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, line_width=4)
        assert _glyph_prop(ax, "line_width") == 4

    def test_bokeh_scatter_fill_color(self, xy):
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_scatter(x, y, fill_color="blue")
        assert _glyph_prop(ax, "fill_color") == "blue"

    def test_bokeh_scatter_size(self, xy):
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_scatter(x, y, size=12)
        assert _glyph_prop(ax, "size") == 12


# ---------------------------------------------------------------------------
# 5. Canonical kwarg translation
# ---------------------------------------------------------------------------


class TestCanonicalTranslation:
    """
    'color', 'linewidth', 'alpha', etc. are canonical names that every backend
    must understand, regardless of its native kwarg names.
    """

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_canonical_color_mpl(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        _, ax = behaviz.plot_line(x, y, color="purple")
        assert ax.get_lines()[0].get_color() == "purple"

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_canonical_linewidth_mpl(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        _, ax = behaviz.plot_line(x, y, linewidth=4.0)
        assert ax.get_lines()[0].get_linewidth() == pytest.approx(4.0)

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_canonical_alpha_mpl(self, backend, xy):
        set_renderer(backend)
        x, y = xy
        _, ax = behaviz.plot_line(x, y, alpha=0.4)
        assert ax.get_lines()[0].get_alpha() == pytest.approx(0.4)

    def test_canonical_color_bokeh_fans_out(self, xy):
        """Canonical 'color' on Bokeh should set both line_color and fill_color."""
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_scatter(x, y, color="purple")
        glyph = ax.renderers[0].glyph
        assert glyph.line_color == "purple"
        assert glyph.fill_color == "purple"

    def test_canonical_linewidth_reaches_bokeh(self, xy):
        """Canonical 'linewidth' should translate to Bokeh's 'line_width'."""
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, linewidth=3)
        assert _glyph_prop(ax, "line_width") == 3

    def test_bokeh_alias_line_color_works(self, xy):
        """Native Bokeh alias 'line_color' must also pass through unchanged."""
        set_renderer("bokeh")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, line_color="teal")
        assert _glyph_prop(ax, "line_color") == "teal"

    def test_legend_label_alias_mpl(self, xy):
        """Bokeh-style 'legend_label' should reach mpl backends as 'label'."""
        set_renderer("matplotlib")
        x, y = xy
        _, ax = behaviz.plot_line(x, y, legend_label="my label")
        assert ax.get_lines()[0].get_label() == "my label"


# ---------------------------------------------------------------------------
# 6. Overrider routing
# ---------------------------------------------------------------------------


class TestOverriderRouting:
    @pytest.mark.parametrize("overrider_cls", [MatplotlibOverrider, SeabornOverrider, BokehOverrider])
    def test_valid_call_kwargs_covers_all_plot_types(self, overrider_cls):
        missing = set(ALL_PLOTS.keys()) - set(overrider_cls.VALID_CALL_KWARGS.keys())
        assert missing == set(), f"{overrider_cls.__name__}.VALID_CALL_KWARGS missing: {missing}"

    def test_mpl_route_splits_call_and_post(self):
        ovr = MatplotlibOverrider()
        call_kw, post_kw = ovr.route("line", {"color": "red", "linewidth": 2})
        # color and linewidth are call-time for mpl plot()
        assert "color" in call_kw or "color" in post_kw  # must end up somewhere
        assert "linewidth" in call_kw or "linewidth" in post_kw

    def test_mpl_route_unknown_kwarg_goes_to_post(self):
        ovr = MatplotlibOverrider()
        call_kw, post_kw = ovr.route("line", {"completely_unknown_kwarg": 99})
        # Unknown kwargs must not silently vanish — they go to post
        all_kw = {**call_kw, **post_kw}
        assert "completely_unknown_kwarg" in all_kw

    def test_bokeh_route_drops_zorder(self, xy):
        """'zorder' has no Bokeh equivalent and is mapped to [] (silently dropped)."""
        set_renderer("bokeh")
        x, y = xy
        # Should not raise even though zorder means nothing to Bokeh
        _, ax = behaviz.plot_line(x, y, zorder=5)
        assert len(ax.renderers) == 1

    def test_seaborn_route_uses_canonical_keys(self):
        """After the table-key fix, SNS overrider must key by canonical names."""
        ovr = SeabornOverrider()
        for name in ALL_PLOTS:
            assert name in ovr.VALID_CALL_KWARGS, f"SeabornOverrider.VALID_CALL_KWARGS missing canonical key '{name}'"

    def test_canon_to_native_not_empty(self):
        for cls in [MatplotlibOverrider, SeabornOverrider, BokehOverrider]:
            assert len(cls.CANON_TO_NATIVE) > 0, f"{cls.__name__}.CANON_TO_NATIVE is empty"


# ---------------------------------------------------------------------------
# 7. Factory-generated functions
# ---------------------------------------------------------------------------


class TestFactoryGeneratedFunctions:
    def test_generated_functions_are_callable(self):
        from behaviz.core.core_factory import plot_line, plot_scatter, plot_step

        assert callable(plot_line)
        assert callable(plot_scatter)
        assert callable(plot_step)

    def test_generated_function_names(self):
        from behaviz.core.core_factory import plot_line, plot_scatter, plot_step

        assert plot_line.__name__ == "plot_line"
        assert plot_scatter.__name__ == "plot_scatter"
        assert plot_step.__name__ == "plot_step"

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_generated_line_produces_artist(self, backend, xy):
        set_renderer(backend)
        from behaviz.core.core_factory import plot_line

        x, y = xy
        fig, ax = plot_line(x, y)
        assert _mpl_ax(ax)
        assert len(ax.get_lines()) == 1

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_generated_scatter_produces_artist(self, backend, xy):
        set_renderer(backend)
        from behaviz.core.core_factory import plot_scatter

        x, y = xy
        fig, ax = plot_scatter(x, y)
        assert _mpl_ax(ax)
        assert len(ax.collections) == 1

    @pytest.mark.parametrize("backend", MPL_BACKENDS)
    def test_generated_step_produces_artist(self, backend, xy):
        set_renderer(backend)
        from behaviz.core.core_factory import plot_step

        x, y = xy
        fig, ax = plot_step(x, y)
        assert _mpl_ax(ax)
        assert len(ax.get_lines()) == 1

    def test_generated_fn_accepts_spec(self, xy):
        from behaviz.core.core_factory import plot_line
        from behaviz.spec import PlotSpec

        set_renderer("matplotlib")
        x, y = xy
        spec = PlotSpec.from_labels("Time", "Value", xunit="s")
        fig, ax = plot_line(x, y, spec=spec)
        assert ax.get_xlabel().startswith("Time")

    def test_generated_fn_passes_overrides(self, xy):
        from behaviz.core.core_factory import plot_line

        set_renderer("matplotlib")
        x, y = xy
        _, ax = plot_line(x, y, color="magenta", linewidth=3)
        assert ax.get_lines()[0].get_color() == "magenta"
        assert ax.get_lines()[0].get_linewidth() == pytest.approx(3.0)

    def test_generated_fn_shape_mismatch_raises(self):
        from behaviz.core.core_factory import plot_line

        set_renderer("matplotlib")
        with pytest.raises(AssertionError):
            plot_line(np.array([1, 2, 3]), np.array([1, 2]))
