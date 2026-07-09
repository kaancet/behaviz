from importlib.metadata import version as _version, PackageNotFoundError

try:
    __version__ = _version("behaviz")
except PackageNotFoundError:  # not installed (e.g. running from source tree)
    __version__ = "0.0.0+unknown"

# Plot functions
from behaviz.core.core import (
    plot_line,
    plot_scatter,
    plot_errorbar,
    plot_violin,
    plot_step,
    plot_bar,
    plot_hbar,
    plot_vertical,
    plot_horizontal,
    plot_image,
    plot_fill_between,
    plot_pie,
    plot_hexbin,
)

from behaviz.core.auxiliary import plot_pval, plot_text
from behaviz.core.flows import plot_sankey, plot_alluvial

# Errors (malformed data arguments, and unsupported save formats)
from behaviz.core.errors import BehavizDataError, BehavizSaveError

# Unified figure output (save + canvas context manager)
from behaviz.io import save, canvas

# Linked plots — shared ColumnDataSource for cross-plot brushing (bokeh)
from behaviz.linked import linked, linked_plot


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

# composite plots
from behaviz.composite_plots.boxplot import plot_boxplot
from behaviz.composite_plots.hist1dplot import plot_hist1d
from behaviz.composite_plots.lollipopplot import plot_lollipop
from behaviz.composite_plots.parallelplot import plot_parallel
from behaviz.composite_plots.raincloudplot import plot_raincloud
from behaviz.composite_plots.ridgeplot import plot_ridge

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
    "plot_hbar",
    "plot_vertical",
    "plot_horizontal",
    "plot_image",
    "plot_fill_between",
    "plot_pie",
    "plot_hexbin",
    "plot_distribution",
    "plot_pval",
    "plot_text",
    "plot_sankey",
    "plot_alluvial",
    # composite plots
    "plot_boxplot",
    "plot_hist1d",
    "plot_lollipop",
    "plot_parallel",
    "plot_raincloud",
    "plot_ridge",
    "split_styles",
    # errors
    "BehavizDataError",
    "BehavizSaveError",
    # figure output
    "save",
    "canvas",
    # linked plots + dashboards
    "linked",
    "linked_plot",
    "view",
    "row",
    "col",
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
    "__version__",
]

set_renderer("matplotlib")


def __getattr__(name):
    # Dashboard layout helpers need the optional `panel` extra, so import them
    # lazily — behaviz stays usable without Panel installed.
    if name in ("view", "row", "col"):
        from behaviz import dashboard

        return getattr(dashboard, name)
    raise AttributeError(f"module 'behaviz' has no attribute '{name}'")
