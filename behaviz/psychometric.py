import numpy as np
from typing import Optional
import matplotlib.pyplot as plt
from numpy.typing import ArrayLike
from scipy.optimize import curve_fit

from behaviz.core.core import *
from behaviz.spec.plot_spec import *
from behaviz.core.overrider import override_plots


PSYCHOMETRIC_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10,10), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="Contrast", unit="%", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Hit rate", unit="%", scale=ScaleType.LINEAR),
    title="Psychometric plot"
)

def plot_psychometric(x:ArrayLike,
                      y:ArrayLike,
                      err:ArrayLike,
                      fit_func:Optional[Callable] = None,
                      ax:Optional[plt.Axes] = None,
                      spec:Optional[PlotSpec] = None,
                      **overrides
                      ) -> plt.Axes | plt.Figure:
    """ Plots the psychometric curve with a fit

    Args:
        x (ArrayLike): x-axis values
        y (ArrayLike): y-axis values
        err (ArrayLike): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        fit_func (Optional[Callable], optional): _description_. Defaults to None.
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.
    Returns:
        plt.Axes | plt.Figure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    
    override_plots()
    spec = spec or PSYCHOMETRIC_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
    
    # data points
    err_overrides = {k:v for k,v in overrides.items() if "fit_" not in k}
    ax = plot_errorbar(x,y,err,ax=ax,spec=spec,**err_overrides)
    
    if fit_func is not None:
        popt,pcov = curve_fit(fit_func, 
                              x, 
                              y,)
        x_fit = np.linspace(x[0],x[-1],100)
        y_fit = fit_func(x_fit, *popt)
        
        fit_overrides = {k.strip("fit_"):v for k,v in overrides.items() if "fit_" in k}
        ax = plot_line(x_fit,y_fit,ax=ax,spec=spec,**fit_overrides,zorder=2)
        
    apply_axis_spec(ax, spec)
    return ax if not standalone else f