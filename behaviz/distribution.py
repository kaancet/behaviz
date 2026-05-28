import numpy as np
from typing import Optional
from numpy.typing import ArrayLike
from scipy.stats import gaussian_kde

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_bar, plot_line
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec


DISTRIBUTION_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10,10), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="X", unit="", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Counts", unit="", scale=ScaleType.LINEAR),
    title="Distribution plot"
)


@plot_function(default_spec=DISTRIBUTION_SPEC)
def plot_distribution(data:ArrayLike,
                      bin_width:float,
                      density:bool=False,
                      ax:Optional[BehavizAxes] = None,
                      spec:Optional[PlotSpec] = None,
                      **overrides
                      ) -> BehavizAxes | BehavizFigure:
    
    
    data = data.ravel()
    
    # make bins
    data_min = np.nanmin(data)
    data_max = np.nanmax(data)
    bin_edges = np.arange(data_min, data_max + bin_width, bin_width)
    counts, bin_edges = np.histogram(data, bins=bin_edges)

    bar_overrides = {k.lstrip("bar_"):v for k,v in overrides.items() if "bar_" in k}
    _,ax = plot_bar(bin_edges[:-1],counts,width=bin_width,ax=ax,spec=spec,**bar_overrides)
    
    if density:
        dx = overrides.get("density_step",1)
        kernel = gaussian_kde(data)
        x = np.arange(data_min,data_max+dx,dx)
        pdf = kernel(x)
        
        ax_twin = ax.twinx()
        kde_overrides = {k:v for k,v in overrides.items() if "bar_" not in k}
        _,ax = plot_line(x,pdf,ax=ax_twin,width=bin_width,spec=spec,**kde_overrides)
    

    return ax
    
    
    