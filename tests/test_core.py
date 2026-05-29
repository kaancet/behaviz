"""
Tests for the core plot functions in behaviz/core/core.py:
  plot_line, plot_scatter, plot_errorbar,
  plot_violin, plot_step, plot_bar
"""

import numpy as np
import pytest
import matplotlib.figure
import matplotlib.pyplot as plt

from behaviz.core import (
    plot_line,
    plot_scatter,
    plot_errorbar,
    plot_violin,
    plot_step,
    plot_bar,
)
from behaviz.spec import PlotSpec, AxisSpec
from behaviz.core import get_renderer


# ── helpers ─────────────────────────────────────────────────────────────────
def _is_figure(obj):
    r = get_renderer()
    if r.name == "matplotlib":
        return isinstance(obj, matplotlib.figure.Figure)
    elif r.name == "bokeh":
        print("Not yet implemented")


def _is_axes(obj):
    r = get_renderer()
    if r.name == "matplotlib":
        return isinstance(obj, plt.Axes)
    elif r.name == "bokeh":
        print("Not yet implemented")


# =========
# plot_line
# =========
class TestPlotLine:
    def test_returns(self, xy):
        x, y = xy
        result_f, result_ax = plot_line(x, y)
        assert _is_figure(result_f)
        assert _is_axes(result_ax)

    def test_returns_with_axes(self, xy, existing_ax):
        x, y = xy
        _, ax = existing_ax
        result_f, result_ax = plot_line(x, y, ax=ax)
        assert _is_figure(result_f)
        assert _is_axes(result_ax)

    def test_adds_a_line(self, xy, existing_ax):
        x, y = xy
        _, ax = existing_ax
        plot_line(x, y, ax=ax)
        assert len(ax.lines) == 1

    def test_shape_mismatch_raises(self):
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        with pytest.raises(AssertionError):
            plot_line(x, y)

    def test_accepts_spec(self, xy):
        x, y = xy
        spec = PlotSpec.from_labels("Time", "Value", xunit="s")
        result_f, result_ax = plot_line(x, y, spec=spec)
        assert _is_figure(result_f)


# ============
# plot_scatter
# ============
class TestPlotScatter:
    def test_returns(self, xy):
        x, y = xy
        result_f, result_ax = plot_scatter(x, y)
        assert _is_figure(result_f)
        assert _is_axes(result_ax)

    def test_returns_with_axes(self, xy, existing_ax):
        x, y = xy
        _, ax = existing_ax
        result_f, result_ax = plot_scatter(x, y, ax=ax)
        assert _is_figure(result_f)
        assert _is_axes(result_ax)

    def test_shape_mismatch_raises(self):
        with pytest.raises(AssertionError):
            plot_scatter(np.array([1, 2, 3]), np.array([1, 2]))


# =============
# plot_errorbar
# =============
class TestPlotErrorbar:
    def test_returns(self, xy_err):
        x, y, err = xy_err
        result_f, result_ax = plot_errorbar(x, y, err)
        assert _is_figure(result_f)
        assert _is_axes(result_ax)

    def test_returns_with_axes(self, xy_err, existing_ax):
        x, y, err = xy_err
        _, ax = existing_ax
        result_f, result_ax = plot_errorbar(x, y, err, ax=ax)
        assert _is_figure(result_f)
        assert _is_axes(result_ax)

    def test_asymmetric_2row_errors(self, xy_err_2row, existing_ax):
        x, y, err = xy_err_2row
        _, ax = existing_ax
        result_f, result_ax = plot_errorbar(x, y, err, ax=ax)
        assert _is_axes(result_ax)

    def test_xy_shape_mismatch_raises(self):
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        err = np.array([0.1, 0.1])
        with pytest.raises(AssertionError):
            plot_errorbar(x, y, err)
