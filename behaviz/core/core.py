import numpy as np
from typing import Optional
from numpy.typing import ArrayLike
import matplotlib.pyplot as plt

from behaviz.spec.plot_spec import *
from behaviz.core.overrider import override_plots


DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10,10), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="X",scale=ScaleType.LINEAR),
    y=AxisSpec(label="Y",scale=ScaleType.LINEAR),
)

def plot_line(
    x: np.ndarray,
    y: np.ndarray,
    ax: Optional[plt.Axes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> plt.Axes | plt.Figure:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        err (np.ndarray): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        plt.Axes | plt.Figure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    override_plots()
    spec = spec or DEFAULT_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
        
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    ax._plot(
        x,
        y,
        mpl_kwargs=overrides
    )
    
    if not standalone:
        return ax
    else:
        apply_axis_spec(ax, spec)
        return f


def plot_scatter(
    x: np.ndarray,
    y: np.ndarray,
    ax: Optional[plt.Axes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> plt.Axes | plt.Figure:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        err (np.ndarray): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        plt.Axes | plt.Figure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    override_plots()
    spec = spec or DEFAULT_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
    else:
        f = ax.get_figure()

    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."
    
    ax._scatter(
        x,
        y,
        mpl_kwargs=overrides
    )
    
    if not standalone:
        return ax
    else:
        apply_axis_spec(ax, spec)
        return f


def plot_errorbar(
    x: np.ndarray,
    y: np.ndarray,
    err: np.ndarray,
    ax: Optional[plt.Axes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> plt.Axes | plt.Figure:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        err (np.ndarray): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        plt.Axes | plt.Figure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    override_plots()
    spec = spec or DEFAULT_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
    else:
        f = ax.get_figure()
        
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    if err.shape[0] != 2:
        assert y.shape == err.shape, (
            f"Shape of {spec.ylabel}({y.shape}) does not match the shape of errors ({err.shape})."
        )
    else:
        # different lower and upper error values
        assert y.shape[0] == err.shape[1], (
            f"Shape of {spec.y.label}({y.shape[0]}) does not match the shape of errors ({err.shape[1]})."
        )

    # plot the points and errorbars
    ax._errorbar(
        x,
        y,
        err,
        mpl_kwargs=overrides
    )
    
    if not standalone:
        return ax
    else:
        apply_axis_spec(ax, spec)
        return f
    

def plot_violin(
    x: np.ndarray,
    ys: list[np.ndarray],
    ax: Optional[plt.Axes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> plt.Axes | plt.Figure:
    """_summary_

    Args:
        x (np.ndarray): _description_
        ys (np.ndarray): _description_
        ax (Optional[plt.Axes], optional): _description_. Defaults to None.
        spec (Optional[PlotSpec], optional): _description_. Defaults to None.

    Returns:
        plt.Axes | plt.Figure: _description_
    """
    
    override_plots()
    spec = spec or DEFAULT_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
    else:
        f = ax.get_figure()
        
        
    x = x.ravel()
    

    assert len(x) == len(ys), f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({len(ys)})."    
    # make sure the data is in proper format -> a list 
    
    
    vplot = ax._violinplot(ys,positions=x,mpl_kwargs=overrides)
    
    if not standalone:
        return ax,vplot
    else:
        apply_axis_spec(ax, spec)
        return f,vplot
    
    
def plot_step(
    x: np.ndarray,
    y: np.ndarray,
    where: Optional[Literal["pre","post","mid"]] = "pre",
    ax: Optional[plt.Axes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> plt.Axes | plt.Figure:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        where (Optional[Literal['pre','post','mid']], optional): where the steps should be placed. Defaults to "pre".
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        plt.Axes | plt.Figure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    override_plots()
    spec = spec or DEFAULT_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
        
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    ax._step(
        x,
        y,
        where=where,
        mpl_kwargs=overrides
    )
    
    if not standalone:
        return ax
    else:
        apply_axis_spec(ax, spec)
        return f
    

def plot_bar(
    x: np.ndarray,
    y: np.ndarray,
    y_bottom: Optional[np.ndarray] = None,
    width: Optional[float|np.ndarray] = 0.2,
    ax: Optional[plt.Axes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> plt.Axes | plt.Figure:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        where (Optional[Literal['pre','post','mid']], optional): where the steps should be placed. Defaults to "pre".
        ax (Optional[plt.Axes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        plt.Axes | plt.Figure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    override_plots()
    spec = spec or DEFAULT_SPEC
        
    standalone = True if ax is None else False
    if standalone:
        f, ax = make_ax(spec)
        
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."
    
    if y_bottom is not None:
        y_bottom.ravel()
        assert y.shape == y_bottom.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y_bottom.shape})."

    ax._bar(
        x,
        y,
        width=width,
        bottom=y_bottom,
        mpl_kwargs=overrides
    )
    
    if not standalone:
        return ax
    else:
        apply_axis_spec(ax, spec)
        return f