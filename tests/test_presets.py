import warnings

import pytest

import behaviz as bv
from behaviz import PlotSpec, AxisSpec, FigureSpec, ScaleType, LegendPosition
from behaviz.presets import (
    save_preset,
    load_preset,
    list_presets,
    delete_preset,
    export_preset,
    import_preset,
)
from behaviz.spec.serialization import spec_to_dict, spec_from_dict


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Point BEHAVIZ_HOME at a throwaway dir for every test."""
    monkeypatch.setenv("BEHAVIZ_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def rich_spec():
    """A spec exercising string scales, tuples, units, annotations, legend options
    and the full style layer (spines/ticks/colours/fonts) that serialization must
    now preserve."""
    return PlotSpec(
        title="My Style",
        title_fontsize=20,
        text_color="#222222",
        x=AxisSpec(
            label="Time",
            unit="s",
            fontsize=14,
            scale="linear",
            lim=(0, 10),
            spines=["bottom", "left"],
            spine_width=2.5,
            spine_color="#000000",
            tick_dir="out",
            tick_width=2.5,
            tick_color="#000000",
        ),
        y=AxisSpec(label="Voltage", unit="mV", scale="log", ticks=[1, 10, 100]),
        figure=FigureSpec(figsize=(6, 4), dpi=200, face_color="#ffffff", axes_color="#fafafa", font_family="Arial"),
        show_legend=True,
        legend_pos=LegendPosition.OUTSIDE,
        annotations=[{"x": 5, "y": 0.8, "text": "peak", "kwargs": {"color": "red"}}],
    )


# ── serializer (filesystem-free) ─────────────────────────────────────────────
class TestSerialization:
    def test_round_trip_preserves_fields(self, rich_spec):
        restored = spec_from_dict(spec_to_dict(rich_spec))
        assert restored.title == "My Style"
        assert restored.x.label == "Time" and restored.x.unit == "s"
        assert restored.x.fontsize == 14
        assert restored.y.scale == ScaleType.LOG
        assert restored.show_legend is True
        assert restored.legend_pos == LegendPosition.OUTSIDE
        assert restored.annotations == rich_spec.annotations

    def test_round_trip_preserves_style_fields(self, rich_spec):
        """The whole point of the field-driven serializer: no style field is dropped."""
        restored = spec_from_dict(spec_to_dict(rich_spec))
        assert restored.title_fontsize == 20
        assert restored.text_color == "#222222"
        assert restored.x.spine_width == 2.5
        assert restored.x.spine_color == "#000000"
        assert restored.x.tick_dir == "out"
        assert restored.x.tick_width == 2.5
        assert restored.x.tick_color == "#000000"
        assert restored.figure.face_color == "#ffffff"
        assert restored.figure.axes_color == "#fafafa"
        assert restored.figure.font_family == "Arial"

    def test_scale_round_trips_as_string(self, rich_spec):
        restored = spec_from_dict(spec_to_dict(rich_spec))
        assert restored.x.scale == "linear" and isinstance(restored.x.scale, str)
        assert restored.y.scale == "log" and isinstance(restored.y.scale, str)

    def test_tuples_restored_as_tuples(self, rich_spec):
        restored = spec_from_dict(spec_to_dict(rich_spec))
        assert restored.x.lim == (0, 10)
        assert isinstance(restored.x.lim, tuple)
        assert isinstance(restored.figure.figsize, tuple)

    def test_dict_is_json_safe(self, rich_spec):
        import json

        # Should not raise — every value must be a JSON primitive.
        json.dumps(spec_to_dict(rich_spec))

    def test_post_hook_dropped_with_warning(self):
        spec = PlotSpec().with_hook(lambda ax, s: None)
        with pytest.warns(UserWarning, match="post_hook"):
            d = spec_to_dict(spec)
        assert spec_from_dict(d).post_hook is None

    def test_unknown_keys_warn_and_are_ignored(self):
        with pytest.warns(UserWarning, match="unknown"):
            spec = spec_from_dict({"title": "x", "x": {"label": "T", "bogus": 1}})
        assert spec.x.label == "T"

    def test_defaults_when_keys_missing(self):
        spec = spec_from_dict({})  # empty dict → all defaults
        assert isinstance(spec, PlotSpec)
        assert spec.title == ""


# ── built-in presets ─────────────────────────────────────────────────────────
class TestBuiltins:
    def test_builtins_available_without_saving(self):
        names = list_presets()
        for n in ("default", "paper", "poster", "notebook", "dark"):
            assert names[n] == "builtin"

    def test_load_builtin_returns_plotspec(self):
        assert isinstance(load_preset("paper"), PlotSpec)

    def test_load_builtin_returns_independent_copy(self):
        a = load_preset("default")
        a.title = "mutated"
        b = load_preset("default")
        assert b.title != "mutated"  # mutation must not leak into the shared builtin

    def test_builtin_cannot_be_deleted(self):
        with pytest.raises(ValueError, match="built-in"):
            delete_preset("default")


# ── user presets ─────────────────────────────────────────────────────────────
class TestUserPresets:
    def test_save_then_load(self, rich_spec):
        save_preset("mine", rich_spec)
        loaded = load_preset("mine")
        assert loaded.title == "My Style"
        assert loaded.y.scale == ScaleType.LOG

    def test_saved_file_lands_in_home(self, rich_spec, isolated_home):
        path = save_preset("mine", rich_spec)
        assert path == isolated_home / "presets" / "mine.json"
        assert path.exists()

    def test_loaded_preset_plugs_into_plot(self, rich_spec):
        import numpy as np

        save_preset("mine", rich_spec)
        spec = load_preset("mine")
        fig, ax = bv.plot_line(np.arange(1, 11), np.arange(1, 11), spec=spec)
        assert ax.get_xlabel() == "Time (s)"
        assert ax.get_title() == "My Style"

    def test_user_preset_shadows_builtin(self, rich_spec):
        save_preset("paper", rich_spec)
        assert list_presets()["paper"] == "user"
        assert load_preset("paper").title == "My Style"

    def test_overwrite_false_raises(self, rich_spec):
        save_preset("mine", rich_spec)
        with pytest.raises(FileExistsError):
            save_preset("mine", rich_spec, overwrite=False)

    def test_delete_user_preset(self, rich_spec):
        save_preset("mine", rich_spec)
        delete_preset("mine")
        with pytest.raises(FileNotFoundError):
            load_preset("mine")


# ── export / import (sharing between machines) ───────────────────────────────
class TestExportImport:
    def test_export_then_import_round_trips(self, rich_spec, tmp_path):
        save_preset("mine", rich_spec)
        external = tmp_path / "shared" / "mine.json"
        export_preset("mine", external)
        assert external.exists()

        # simulate another machine: a fresh user library
        delete_preset("mine")
        assert "mine" not in [n for n, src in list_presets().items() if src == "user"]

        import_preset(external)
        restored = load_preset("mine")
        assert restored.title == "My Style"
        assert restored.y.scale == ScaleType.LOG
        assert restored.legend_pos == LegendPosition.OUTSIDE

    def test_export_to_directory_uses_name(self, rich_spec, tmp_path):
        save_preset("mine", rich_spec)
        out = export_preset("mine", tmp_path)  # tmp_path is a dir
        assert out == tmp_path / "mine.json"
        assert out.exists()

    def test_export_builtin(self, tmp_path):
        out = export_preset("paper", tmp_path)
        assert out.exists()
        import_preset(out, name="paper_copy")
        assert load_preset("paper_copy").figure.figsize == load_preset("paper").figure.figsize

    def test_import_with_custom_name(self, rich_spec, tmp_path):
        export_preset_path = tmp_path / "whatever.json"
        save_preset("mine", rich_spec)
        export_preset("mine", export_preset_path)
        import_preset(export_preset_path, name="renamed")
        assert list_presets()["renamed"] == "user"
        assert load_preset("renamed").title == "My Style"

    def test_import_defaults_name_to_file_stem(self, rich_spec, tmp_path):
        save_preset("mine", rich_spec)
        export_preset("mine", tmp_path / "from_colleague.json")
        import_preset(tmp_path / "from_colleague.json")
        assert "from_colleague" in list_presets()

    def test_import_respects_overwrite_false(self, rich_spec, tmp_path):
        save_preset("mine", rich_spec)
        export_preset("mine", tmp_path / "mine.json")
        with pytest.raises(FileExistsError):
            import_preset(tmp_path / "mine.json", overwrite=False)

    def test_import_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_preset(tmp_path / "nope.json")

    def test_import_non_json_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("this is not json {{{")
        with pytest.raises(ValueError, match="not valid JSON"):
            import_preset(bad)

    def test_import_unrelated_json_rejected(self, tmp_path):
        bad = tmp_path / "unrelated.json"
        bad.write_text('{"foo": 1, "bar": 2}')
        with pytest.raises(ValueError, match="does not look like"):
            import_preset(bad)

    def test_export_unknown_preset_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            export_preset("ghost", tmp_path)


# ── error handling ───────────────────────────────────────────────────────────
class TestErrors:
    def test_load_unknown_raises_with_listing(self):
        with pytest.raises(FileNotFoundError, match="Available presets"):
            load_preset("does_not_exist")

    @pytest.mark.parametrize("bad", ["../evil", "sub/../../evil", "/etc/passwd", ""])
    def test_invalid_names_rejected(self, bad, rich_spec):
        # traversal / absolute / empty are rejected; plain subpaths are allowed (see below)
        with pytest.raises(ValueError):
            save_preset(bad, rich_spec)

    def test_save_non_spec_rejected(self):
        with pytest.raises(TypeError):
            save_preset("mine", {"not": "a spec"})


# ── nested preset paths (subdirectories) ─────────────────────────────────────
class TestNestedPaths:
    def test_save_and_load_nested(self, rich_spec, isolated_home):
        path = save_preset("my_presets/my_new", rich_spec)
        assert path == isolated_home / "presets" / "my_presets" / "my_new.json"
        assert path.exists()
        assert load_preset("my_presets/my_new").title == "My Style"

    def test_load_accepts_explicit_json_suffix(self, rich_spec):
        save_preset("my_presets/my_new", rich_spec)
        assert load_preset("my_presets/my_new.json").title == "My Style"

    def test_nested_preset_listed_with_relative_key(self, rich_spec):
        save_preset("my_presets/my_new", rich_spec)
        assert list_presets()["my_presets/my_new"] == "user"

    def test_delete_nested(self, rich_spec):
        save_preset("my_presets/my_new", rich_spec)
        delete_preset("my_presets/my_new")
        with pytest.raises(FileNotFoundError):
            load_preset("my_presets/my_new")

    def test_flat_names_still_work(self, rich_spec):
        save_preset("flat", rich_spec)
        assert load_preset("flat").title == "My Style"
