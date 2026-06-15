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
    plot_image,
    plot_fill_between,
    plot_pie,
    plot_hexbin,
)

from behaviz.core.auxiliary import plot_pval

# Errors (malformed data arguments, and unsupported save formats)
from behaviz.core.errors import BehavizDataError, BehavizSaveError

# Unified figure output (save + canvas context manager)
from behaviz.io import save, canvas

# Spec classes (users need these to configure plots)
from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec, LegendPosition
from behaviz.spec.colorbar_spec import ColorbarSpec

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

# composite plot styling helper
from behaviz.composite_plots.styling import split_styles

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
    "plot_image",
    "plot_fill_between",
    "plot_pie",
    "plot_hexbin",
    "plot_distribution",
    "plot_psychometric",
    "plot_impact",
    "plot_pval",
    # errors
    "BehavizDataError",
    "BehavizSaveError",
    # figure output
    "save",
    "canvas",
    # specs
    "PlotSpec",
    "AxisSpec",
    "ScaleType",
    "FigureSpec",
    "LegendPosition",
    "ColorbarSpec",
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
