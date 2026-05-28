
# Plot functions 
from behaviz.core.core import (
    plot_line,
    plot_scatter,
    plot_errorbar,
    plot_violin,
    plot_step,
    plot_bar,
)

from behaviz.rainplot import plot_rain
from behaviz.distribution import plot_distribution
from behaviz.psychometric import plot_psychometric
from behaviz.impact import plot_impact

# Spec classes (users need these to configure plots)
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec, LegendPosition

# Backend switcher
from behaviz.core.renderer import set_renderer


__all__ = [
    # plot functions
    "plot_line", "plot_scatter", "plot_errorbar",
    "plot_violin", "plot_step", "plot_bar",
    "plot_rain", "plot_distribution", "plot_psychometric", "plot_impact",
    # specs
    "PlotSpec", "AxisSpec", "ScaleType",
    "FigureSpec", "LegendPosition",
    # backend
    "set_renderer",
]