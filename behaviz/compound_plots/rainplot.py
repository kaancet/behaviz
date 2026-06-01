import numpy as np
from typing import Optional
from numpy.typing import ArrayLike

from behaviz.core import BehavizAxes, BehavizFigure, plot_function, plot_violin, plot_scatter
from behaviz.spec import PlotSpec, AxisSpec, ScaleType, FigureSpec


RAINPLOT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(10,10), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="Contrast", unit="%", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Hit rate", unit="%", scale=ScaleType.LINEAR),
    title="Rain plot"
)


@plot_function(default_spec=RAINPLOT_SPEC)
def plot_rain(x:ArrayLike,
              ys:list[ArrayLike],
              ax: Optional[BehavizAxes] = None,
              bin_width: int = 25, #ms
              with_cloud: bool = False,
              spec: Optional[PlotSpec] = None,
              **overrides,
) -> BehavizAxes | BehavizFigure:
    """_summary_

    Args:
        x (ArrayLike): _description_
        ys (list[ArrayLike]): _description_
        ax (Optional[plt.Axes], optional): _description_. Defaults to None.
        bin_width (int, optional): _description_. Defaults to 25.
        spec (Optional[PlotSpec], optional): _description_. Defaults to None.

    Returns:
        plt.Axes | plt.Figure: _description_
    """
    _xspace = x[1] - x[0]    
    if with_cloud:
        x_wm = overrides.pop("width_margin",_xspace/5) #arbitrary
        width = overrides.pop("width",(_xspace - 2*x_wm) / 2)
        
        cloud_overrides = {k.removeprefix("cloud_"):v for k,v in overrides.items() if "cloud_" in k}
        _, ax, vp = plot_violin(x - x_wm,ys,ax=ax,spec=spec, **cloud_overrides)
        
        # Keep only left half of violins
        for body in vp["bodies"]:
            path = body.get_paths()[0]
            vertices = path.vertices

            center = np.mean(vertices[:, 0])

            # Clip right side to center
            vertices[:, 0] = np.minimum(vertices[:, 0], center)
            
    else:
        x_wm = overrides.pop("width_margin",0)
        width = overrides.pop("width",_xspace/2 - x_wm)
        
    # plot the the dots
    dot_overrides = {k.removeprefix("dot_"):v for k,v in overrides.items() if "dot_" in k}
    for xi,yi in zip(x,ys):    
        x_dots = make_dot_swarm(yi,
                                center=xi + x_wm,
                                bin_width=bin_width,
                                width=width,
                                right_sided=with_cloud)
        
        
        _,ax = plot_scatter(x_dots,yi,ax=ax,spec=spec,**dot_overrides)
    return ax
        
def make_dot_swarm(
    y_points: ArrayLike,
    center: float = 0,
    bin_width: float = 50,
    width: float = 0.5,
    right_sided:bool=False,
) -> np.ndarray:
    """Turns the data points into a cloud by dispersing them horizontally depending on their distribution.
    The more points in a bin, the wider the dispersion.
    Returns x-coordinates of the dispersed points.

    Args:
        y_points (ArrayLike): values that will be dispersed in a cloud
        center (float, optional): Center value that the cloud will be located at. Defaults to 0.
        bin_width (float, optional): width of bins. Defaults to 50.
        width (float, optional): maximum total width of the swarm. Defaults to 0.5.

    Returns:
        np.ndarray: new dispersed x_points corresponding to y_points
    """
    if not isinstance(y_points, np.ndarray):
        y_points = np.array(y_points)

    if len(y_points) > 1:
        bin_edges = np.arange(
            np.nanmin(y_points), np.nanmax(y_points) + bin_width, bin_width
        )
        counts, bin_edges = np.histogram(y_points, bins=bin_edges)

        if not len(counts):
            counts = np.array([0])

        max_count = np.nanmax(counts) // 2
        dx = max_count and width / max_count or 0

        idx_in_bin = []
        for k, (ymin, ymax) in enumerate(zip(bin_edges[:-1], bin_edges[1:])):
            if k == len(bin_edges) - 2:
                i = np.nonzero((y_points >= ymin) & (y_points <= ymax))[0]
            else:
                i = np.nonzero((y_points >= ymin) & (y_points < ymax))[0]
            idx_in_bin.append(i)

        x_coords = np.zeros(len(y_points))

        for i in idx_in_bin:
            if len(i) > 1:
                n = len(i)
                j = n % 2  # 1 if odd (one point stays at center), 0 if even

                # Interleave from the center outward rather than edge inward.
                # For n=6: sorted order is [0,1,2,3,4,5]
                #   left half  → [2,1,0]  (indices counting inward from left)
                #   right half → [3,4,5]  (indices counting inward from right)
                # Zip them together so rank 0 = innermost pair, rank 1 = next, etc.

                left_half  = i[:n // 2][::-1]   # reverse → innermost first
                right_half = i[n // 2 + j:]     # innermost first

                for rank, (l, r) in enumerate(zip(left_half, right_half)):
                    offset = (rank + (j == 0) * 0.5) * dx  # even: 0.5,1.5,… | odd: 0,1,…
                    x_coords[l] = offset if right_sided else -offset  
                    x_coords[r] = offset

        return x_coords + center

    else:
        return np.array([0]) + center