import numpy as np
from typing import Optional
import matplotlib.pyplot as plt
from numpy.typing import ArrayLike

from behaviz.spec.axis_spec import AxisSpec, ScaleType
from behaviz.spec.figure_spec import FigureSpec
from behaviz.spec.plot_spec import PlotSpec
from behaviz.core.plot_setup import plot_function
from behaviz.core.core import plot_scatter, plot_line
from behaviz.core.renderer import BehavizAxes, BehavizFigure

IMPACT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10,10), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="X", unit="", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Y", unit="", scale=ScaleType.LINEAR),
    title="Impact plot"
)

@plot_function(default_spec=IMPACT_SPEC)
def plot_impact(x:ArrayLike,
                ys:ArrayLike,
                ax:Optional[BehavizAxes] = None,
                spec:Optional[PlotSpec] = None,
                **overrides
                ) -> BehavizAxes | BehavizFigure:
    
    x = np.asarray(x).ravel()
    ys = np.asarray(ys)
    
    assert x.shape[0] == ys.shape[1], f"Shape of {spec.x.label}({x.shape[0]}) is not equal to shape of {spec.y.label}({ys.shape[1]})."
    
    jitter = overrides.pop("jitter",0)
    jittered_array = np.tile(x,(ys.shape[0],1)) + np.random.randn(ys.shape[0],ys.shape[1]) * jitter

    # plot the lines
    for yi,xi in zip(ys,jittered_array):
        _, ax = plot_line(xi,yi,ax=ax,spec=spec,**overrides)
    
    # plot the the dots
    dot_overrides = {k.strip("dot_"):v for k,v in overrides.items() if "dot_" in k}
    for i in range(len(x)):
        yi = ys[:,i]
        xi = jittered_array[:,i]
        _, ax = plot_scatter(xi,yi,ax=ax,spec=spec,**dot_overrides)
        
    return ax