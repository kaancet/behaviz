# Plot functions
from behaviz.core.core import (
    plot_line,
    plot_scatter,
    plot_errorbar,
    plot_violin,
    plot_step,
    plot_bar,
)

from behaviz.core.auxiliary import plot_pval

# Spec classes (users need these to configure plots)
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec, LegendPosition

# Visual manipulations
import behaviz.manipulations

# Backend switcher
import behaviz.backends
from behaviz.backends.renderer_manager import set_renderer, get_renderer


__all__ = [
    # plot functions
    "plot_line",
    "plot_scatter",
    "plot_errorbar",
    "plot_violin",
    "plot_step",
    "plot_bar",
    "plot_rain",
    "plot_distribution",
    "plot_psychometric",
    "plot_impact",
    # specs
    "PlotSpec",
    "AxisSpec",
    "ScaleType",
    "FigureSpec",
    "LegendPosition",
    # backend
    "set_renderer",
]

set_renderer("matplotlib")
