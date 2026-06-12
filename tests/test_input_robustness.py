"""Input robustness of the public plot functions.

Covers the declarative Channel layer (behaviz/core/channels.py) end-to-end:
every flavour of accepted input (lists, tuples, scalars, trivial 2-D, Series,
generators, ragged groups, column names) and every rejection, asserting the
errors are BehavizDataError and that their messages name the offending
parameter and its shape.
"""

import numpy as np
import pytest

import behaviz as bv
from behaviz import BehavizDataError
from behaviz.core.errors import describe


@pytest.fixture(autouse=True)
def mpl_backend():
    bv.set_renderer("matplotlib")


# =====================================================================
# Accepted input flavours
# =====================================================================


class TestAcceptedFlavours:
    @pytest.mark.parametrize(
        "x, y",
        [
            ([0, 1, 2], [3, 1, 2]),
            ((0, 1, 2), (3.0, 1.0, 2.0)),
            (np.arange(3), np.ones(3)),
            (range(3), range(3)),
        ],
        ids=["lists", "tuples", "ndarrays", "ranges"],
    )
    def test_basic_sequences(self, x, y):
        _, ax = bv.plot_line(x, y)
        assert len(ax.lines) == 1

    def test_generator_is_materialised(self):
        _, ax = bv.plot_line((v for v in [0, 1, 2]), (v for v in [3, 1, 2]))
        assert len(ax.lines) == 1

    def test_pandas_series(self):
        pd = pytest.importorskip("pandas")
        _, ax = bv.plot_line(pd.Series([0, 1, 2]), pd.Series([3, 1, 2]))
        assert len(ax.lines) == 1

    def test_polars_series(self):
        pl = pytest.importorskip("polars")
        _, ax = bv.plot_line(pl.Series([0, 1, 2]), pl.Series([3, 1, 2]))
        assert len(ax.lines) == 1

    @pytest.mark.parametrize("shape", [(3, 1), (1, 3)], ids=["column", "row"])
    def test_trivial_2d_is_squeezed(self, shape):
        _, ax = bv.plot_line(np.arange(3).reshape(shape), [1, 2, 3])
        xdata = ax.lines[0].get_xdata()
        assert np.asarray(xdata).ndim == 1

    def test_empty_inputs_allowed(self):
        _, ax = bv.plot_line([], [])
        assert len(ax.lines) == 1

    def test_scalar_vertical_and_horizontal(self):
        # used to die with TypeError: len() of unsized object
        _, ax = bv.plot_vertical(1.5)
        _, ax2 = bv.plot_horizontal(0.5)
        assert len(ax.lines) + len(ax.collections) >= 1
        assert len(ax2.lines) + len(ax2.collections) >= 1

    def test_bar_scalar_and_per_bar_widths(self):
        bv.plot_bar([0, 1, 2], [1, 2, 3], width=0.5)
        bv.plot_bar([0, 1, 2], [1, 2, 3], width=[0.2, 0.4, 0.2])

    def test_fill_between_scalar_levels(self):
        _, ax = bv.plot_fill_between([0, 1, 2], 1.0)
        assert len(ax.collections) == 1


class TestGroupedInputs:
    def test_violin_ragged_list(self):
        rng = np.random.default_rng(0)
        _, ax, vp = bv.plot_violin([0, 1], [rng.normal(size=30), rng.normal(size=55)])
        assert len(vp["bodies"]) == 2

    def test_violin_2d_array_is_one_violin_per_row(self):
        rng = np.random.default_rng(0)
        _, ax, vp = bv.plot_violin([0, 1, 2], rng.normal(size=(3, 40)))
        assert len(vp["bodies"]) == 3

    def test_violin_list_of_lists(self):
        _, ax, vp = bv.plot_violin([0, 1], [[1.0, 2.0, 3.0], [4.0, 5.0]])
        assert len(vp["bodies"]) == 2


class TestDataframeChannels:
    def test_dict_of_arrays(self):
        _, ax = bv.plot_line("t", "v", data={"t": [0, 1, 2], "v": [5, 3, 4]})
        assert len(ax.lines) == 1

    def test_missing_column_lists_available(self):
        with pytest.raises(KeyError, match="Available columns"):
            bv.plot_line("nope", "v", data={"t": [0, 1], "v": [1, 2]})


# =====================================================================
# Rejections — error type and message quality
# =====================================================================


def _raises_naming(param, snippet=None):
    """pytest.raises wrapper asserting the message names the parameter."""
    match = rf"`{param}`"
    if snippet:
        match += rf"(.|\n)*{snippet}"
    return pytest.raises(BehavizDataError, match=match)


class TestRejections:
    def test_is_a_value_error(self):
        assert issubclass(BehavizDataError, ValueError)

    def test_length_mismatch_names_param_and_shapes(self):
        with pytest.raises(BehavizDataError) as exc:
            bv.plot_line([1, 2, 3], [1, 2])
        msg = str(exc.value)
        assert "plot_line" in msg
        assert "`y`" in msg
        assert "(3,)" in msg and "(2,)" in msg

    def test_true_2d_rejected(self):
        with _raises_naming("x", "1-D"):
            bv.plot_scatter(np.zeros((2, 100)), np.zeros(200))

    def test_string_without_data(self):
        with _raises_naming("x", "data="):
            bv.plot_line("t", "v")

    def test_non_numeric(self):
        with _raises_naming("x", "numeric"):
            bv.plot_line(["a", "b"], [1, 2])

    def test_mixed_scalars_and_strings(self):
        with _raises_naming("x", "numeric"):
            bv.plot_line([1, "a", 3], [1, 2, 3])

    def test_violin_flat_ys_suggests_wrapping(self):
        with _raises_naming("ys", "wrap"):
            bv.plot_violin([0], [1, 2, 3])

    def test_violin_group_count_mismatch(self):
        with _raises_naming("ys"):
            bv.plot_violin([0, 1, 2], np.random.default_rng(0).normal(size=(5, 30)))

    def test_bar_bottom_length_mismatch(self):
        with _raises_naming("bottom"):
            bv.plot_bar([0, 1, 2], [1, 2, 3], bottom=[1, 2])

    def test_errorbar_bad_err_shape(self):
        with _raises_naming("err", r"\(2, N\)"):
            bv.plot_errorbar([1, 2, 3], [1, 2, 3], [0.1, 0.2])

    def test_errorbar_symmetric_n_equals_2(self):
        # err of shape (2,) with N == 2 is symmetric — used to be ambiguous
        bv.plot_errorbar([1, 2], [1, 2], [0.1, 0.2])

    def test_image_3d_rejected(self):
        with _raises_naming("values", "2-D"):
            bv.plot_image(np.zeros((3, 4, 3)))

    def test_image_1d_rejected(self):
        with _raises_naming("values", "2-D"):
            bv.plot_image(np.zeros(5))

    def test_image_values_keyword_works(self):
        # `data=` stays reserved for dataframes; the grid is `values`
        _, ax = bv.plot_image(values=np.zeros((3, 4)))
        assert len(ax.images) == 1

    def test_parallel_ragged_rows(self):
        from behaviz.composite_plots.parallelplot import plot_parallel

        with _raises_naming("ys"):
            plot_parallel([0, 1, 2], [[1, 2, 3], [1, 2]])

    def test_required_none_rejected(self):
        with _raises_naming("y", "required"):
            bv.plot_line([1, 2, 3], None)


# =====================================================================
# describe() — the vocabulary all messages share
# =====================================================================


class TestDescribe:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (np.zeros((2, 100)), "ndarray shape (2, 100)"),
            (4.2, "scalar 4.2"),
            ("rt", "str 'rt'"),
            (None, "None"),
            ([1, 2, 3], "list of length 3"),
        ],
    )
    def test_simple_values(self, value, expected):
        assert describe(value) == expected

    def test_list_of_arrays_shows_lengths(self):
        assert describe([np.zeros(50), np.zeros(48)]) == "list of 2 arrays (lengths 50, 48)"


# =====================================================================
# Docstring conformance — every public plot function documents itself
# =====================================================================


class TestDocstrings:
    PUBLIC_PLOTS = [name for name in bv.__all__ if name.startswith("plot_") and hasattr(bv, name)]

    @pytest.mark.parametrize("name", PUBLIC_PLOTS)
    def test_has_args_and_returns_sections(self, name):
        doc = getattr(bv, name).__doc__
        assert doc, f"{name} has no docstring"
        assert "Args:" in doc, f"{name} docstring lacks an Args: section"
        assert "Returns:" in doc, f"{name} docstring lacks a Returns: section"

    @pytest.mark.parametrize("name", PUBLIC_PLOTS)
    def test_summary_line_is_not_placeholder(self, name):
        doc = getattr(bv, name).__doc__ or ""
        first = doc.strip().splitlines()[0]
        assert "_summary_" not in first and first.strip(), f"{name} has a placeholder summary"
