import numpy as np
from typing import Optional
import matplotlib.pyplot as plt
from numpy.typing import ArrayLike
from scipy.optimize import curve_fit
from scipy.stats import gaussian_kde

from behaviz.core.core import *
from behaviz.spec.plot_spec import *
from behaviz.core.overrider import override_plots


DISTRIBUTION_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10,10), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="X", unit="", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Counts", unit="", scale=ScaleType.LINEAR),
    title="Distribution plot"
)


def plot_distribution(data:ArrayLike,
                      bin_width:float,
                      density:bool=False,
                      ax:Optional[plt.Axes] = None,
                      spec:Optional[PlotSpec] = None,
                      **overrides
                      ) -> plt.Axes | plt.Figure:
    
    
    override_plots()
    spec = spec or DISTRIBUTION_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
    
    data = data.ravel()
    
    # make bins
    data_min = np.nanmin(data)
    data_max = np.nanmax(data)
    bin_edges = np.arange(data_min, data_max + bin_width, bin_width)
    counts, bin_edges = np.histogram(data, bins=bin_edges)

    bar_overrides = {k.lstrip("bar_"):v for k,v in overrides.items() if "bar_" in k}
    ax = plot_bar(bin_edges[:-1],counts,width=bin_width,ax=ax,spec=spec,**bar_overrides)
    
    if density:
        dx = overrides.get("density_step",1)
        kernel = gaussian_kde(data)
        x = np.arange(data_min,data_max+dx,dx)
        pdf = kernel(x)
        
        ax_twin = ax.twinx()
        kde_overrides = {k:v for k,v in overrides.items() if "bar_" not in k}
        ax = plot_line(x,pdf,ax=ax_twin,width=bin_width,spec=spec,**kde_overrides)
    
    apply_axis_spec(ax, spec)
    if density:
        apply_axis_spec(ax_twin, spec)
    return ax if not standalone else f
    
    
    