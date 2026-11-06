"""bv.set_xaxis / bv.set_yaxis: string-based axis changes on the active canvas."""

import matplotlib

matplotlib.use("Agg")

import pytest

import behaviz as bv


@pytest.fixture
def bokeh():
    bv.set_renderer("bokeh")
    yield
    bv.set_renderer("matplotlib")


def test_scale_and_fields_matplotlib():
    with bv.canvas() as ax:
        bv.plot_line([1, 10, 100], [1, 2, 3])
        bv.set_xaxis("log", lim=(1, 100), label="Time", unit="s")
        bv.set_yaxis("symlog")
    assert ax.get_xscale() == "log" and ax.get_yscale() == "symlog"
    assert ax.get_xlim() == (1, 100)
    assert ax.get_xlabel() == "Time (s)"


def test_later_plots_inherit_change():
    with bv.canvas() as ax:
        bv.set_xaxis("log")
        bv.plot_line([1, 10, 100], [1, 2, 3])  # re-applies the canvas spec
    assert ax.get_xscale() == "log"


def test_axes_positional_and_keyword_outside_canvas():
    _, ax = bv.plot_line([1, 10, 100], [1, 2, 3])
    bv.set_xaxis(ax, "log")
    bv.set_yaxis("log", ax=ax)
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "log")


def test_older_axes_keeps_its_style():
    spec = bv.PlotSpec(x=bv.AxisSpec(label="Time"))
    _, first = bv.plot_line([1, 10, 100], [1, 2, 3], spec=spec)
    _, second = bv.plot_line([1, 10, 100], [1, 2, 3])
    bv.set_xaxis(first, "log")
    assert first.get_xscale() == "log" and first.get_xlabel() == "Time"
    assert second.get_xscale() == "linear"


def test_no_canvas_no_ax_raises():
    with pytest.raises(ValueError, match="canvas"):
        bv.set_xaxis("log")


def test_bad_call_shapes_raise():
    _, ax = bv.plot_line([1, 10, 100], [1, 2, 3])
    with pytest.raises(TypeError):
        bv.set_xaxis(ax, "log", ax=ax)
    with pytest.raises(TypeError):
        bv.set_xaxis("log", "linear")


def test_bad_scale_and_field_raise():
    with bv.canvas():
        with pytest.raises(ValueError, match="Invalid scale"):
            bv.set_xaxis("loog")
        with pytest.raises(TypeError):
            bv.set_xaxis("log", bogus=1)


def test_bokeh_switches_scale_after_creation(bokeh):
    with bv.canvas() as fig:
        bv.plot_line([1, 10, 100], [1, 2, 3])
        bv.set_xaxis("log")
        assert type(fig.x_scale).__name__ == "LogScale"
        assert type(fig.xaxis[0].ticker).__name__ == "LogTicker"
        bv.set_xaxis("linear")
        assert type(fig.x_scale).__name__ == "LinearScale"
