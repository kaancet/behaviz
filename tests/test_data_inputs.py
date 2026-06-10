"""
Tests for dataframe-agnostic data resolution (behaviz/core/data_source.py and
the ``data_args`` hook in behaviz/core/plot_setup.py).

These exercise the mixed input styles supported by plot_line / plot_scatter:

    plot_line(x, y)                                # arrays, positional
    plot_line(x="time", y="volt", data=df)        # column names, keyword
    plot_scatter("time", "volt", data=df)         # column names, positional
    plot_line(x="time", y=y_array, data=df)       # mix of column + raw array

The ``data`` source is parametrized over dict / pandas / polars. pandas and
polars are *not* dependencies of behaviz, so those params skip automatically
when the library is not installed (the dict path always runs).
"""

import numpy as np
import pytest

from behaviz.core import plot_line, plot_scatter
from behaviz.core.data_source import resolve
from behaviz.spec import PlotSpec, AxisSpec

N = 12


# ── fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def cols():
    """Raw x/y arrays that also back every dataframe fixture below."""
    x = np.linspace(0.0, 1.0, N)
    y = np.cos(x)
    return x, y


@pytest.fixture(params=["dict", "pandas", "polars"])
def frame(request, cols):
    """A data source with columns 'time' and 'volt', across each backend.

    'dict' always runs; pandas/polars skip when not installed.
    """
    x, y = cols
    if request.param == "dict":
        return {"time": x, "volt": y}
    mod = pytest.importorskip(request.param)
    return mod.DataFrame({"time": x, "volt": y})


def _line_xy(ax):
    line = ax.lines[0]
    return np.asarray(line.get_xdata()), np.asarray(line.get_ydata())


def _scatter_xy(ax):
    off = ax.collections[0].get_offsets()
    return np.asarray(off[:, 0]), np.asarray(off[:, 1])


# ── the array path must stay byte-for-byte unchanged ─────────────────────────
class TestArrayPath:
    def test_positional_arrays(self, cols):
        x, y = cols
        _, ax = plot_line(x, y)
        gx, gy = _line_xy(ax)
        np.testing.assert_allclose(gx, x)
        np.testing.assert_allclose(gy, y)

    def test_keyword_arrays(self, cols):
        x, y = cols
        _, ax = plot_scatter(x=x, y=y)
        gx, gy = _scatter_xy(ax)
        np.testing.assert_allclose(gx, x)
        np.testing.assert_allclose(gy, y)

    def test_arrays_with_blank_spec_stay_unlabeled(self, cols):
        x, y = cols
        _, ax = plot_line(x, y, spec=PlotSpec())
        assert ax.get_xlabel() == ""
        assert ax.get_ylabel() == ""


# ── column names resolved from a data source ─────────────────────────────────
class TestColumnResolution:
    def test_keyword_columns(self, frame, cols):
        x, y = cols
        _, ax = plot_line(x="time", y="volt", data=frame, spec=PlotSpec())
        gx, gy = _line_xy(ax)
        np.testing.assert_allclose(gx, x)
        np.testing.assert_allclose(gy, y)

    def test_positional_columns(self, frame, cols):
        x, y = cols
        _, ax = plot_scatter("time", "volt", data=frame, spec=PlotSpec())
        gx, gy = _scatter_xy(ax)
        np.testing.assert_allclose(gx, x)
        np.testing.assert_allclose(gy, y)

    def test_mixed_column_and_raw_array(self, frame, cols):
        """x from a column name, y from a raw array in the same call."""
        x, y = cols
        y2 = y * 2.0
        _, ax = plot_line(x="time", y=y2, data=frame, spec=PlotSpec())
        gx, gy = _line_xy(ax)
        np.testing.assert_allclose(gx, x)
        np.testing.assert_allclose(gy, y2)


# ── auto-labeling from column names ──────────────────────────────────────────
class TestAutoLabel:
    def test_blank_labels_filled_from_columns(self, frame):
        _, ax = plot_line(x="time", y="volt", data=frame, spec=PlotSpec())
        assert ax.get_xlabel() == "time"
        assert ax.get_ylabel() == "volt"

    def test_explicit_label_not_overridden(self, frame):
        spec = PlotSpec(x=AxisSpec(label="Custom T"))
        _, ax = plot_line(x="time", y="volt", data=frame, spec=spec)
        assert ax.get_xlabel() == "Custom T"  # kept
        assert ax.get_ylabel() == "volt"  # auto-filled

    def test_raw_array_channel_not_autolabeled(self, frame, cols):
        _, y = cols
        _, ax = plot_line(x="time", y=y, data=frame, spec=PlotSpec())
        assert ax.get_xlabel() == "time"
        assert ax.get_ylabel() == ""


# ── reserved keywords compose: data= alongside hover_annotate= ───────────────
class TestComposesWithHover:
    def test_hover_with_data(self, cols):
        x, y = cols
        _, ax = plot_scatter(x="time", y="volt", data={"time": x, "volt": y}, hover_annotate=True)
        # hover state was attached and the reserved kwargs did not leak into mpl
        assert hasattr(ax, "_behaviz_hover")
        assert len(ax._behaviz_hover.series) == 1


# ── friendly errors ──────────────────────────────────────────────────────────
class TestErrors:
    def test_missing_column_raises(self, cols):
        x, y = cols
        with pytest.raises(KeyError, match="not found"):
            plot_line(x="nope", y="volt", data={"time": x, "volt": y})

    def test_lazyframe_is_rejected(self, cols):
        pl = pytest.importorskip("polars")
        x, y = cols
        lf = pl.LazyFrame({"time": x, "volt": y})
        with pytest.raises(TypeError, match="collect"):
            plot_line(x="time", y="volt", data=lf)


# ── unit tests for the resolver itself ───────────────────────────────────────
class TestResolve:
    def test_array_passthrough(self):
        a = np.array([1.0, 2.0, 3.0])
        out = resolve(a, None)
        np.testing.assert_array_equal(out, a)
        assert isinstance(out, np.ndarray)

    def test_list_becomes_array(self):
        out = resolve([1, 2, 3], None)
        assert isinstance(out, np.ndarray)
        np.testing.assert_array_equal(out, np.array([1, 2, 3]))

    def test_string_resolves_column(self):
        data = {"a": np.array([10, 20, 30])}
        np.testing.assert_array_equal(resolve("a", data), np.array([10, 20, 30]))

    def test_missing_column_message_lists_available(self):
        with pytest.raises(KeyError, match=r"Available columns: \['a', 'b'\]"):
            resolve("c", {"a": [1], "b": [2]})
