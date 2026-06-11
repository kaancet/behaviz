# Plot functions
from behaviz.core.core import (
    plot_line,
    plot_scatter,
    plot_errorbar,
    plot_violin,
    plot_step,
    plot_bar,
    plot_vertical,
    plot_horizontal,
)

from behaviz.core.auxiliary import plot_pval

# Spec classes (users need these to configure plots)
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec, LegendPosition

# Preset save/load system
from behaviz.presets import (
    load_preset,
    save_preset,
    list_presets,
    delete_preset,
    export_preset,
    import_preset,
    init_home,
    presets_dir,
    examples_dir,
)

# Compound plot styling helper
from behaviz.compound_plots.styling import split_styles

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
    "plot_vertical",
    "plot_horizontal",
    "plot_distribution",
    "plot_psychometric",
    "plot_impact",
    "plot_pval",
    # specs
    "PlotSpec",
    "AxisSpec",
    "ScaleType",
    "FigureSpec",
    "LegendPosition",
    # presets
    "load_preset",
    "save_preset",
    "list_presets",
    "delete_preset",
    "export_preset",
    "import_preset",
    "init_home",
    "presets_dir",
    "examples_dir",
    # backend
    "set_renderer",
    "get_renderer",
]

set_renderer("matplotlib")
