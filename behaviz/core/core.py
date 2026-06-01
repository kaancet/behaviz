import numpy as np
from typing import Optional, Literal

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes, BehavizFigure
from .plot_setup import plot_function

from ..spec import PlotSpec, AxisSpec, ScaleType, FigureSpec
from .utils import validate_and_fix_inputs

DEFAULT_SPEC = PlotSpec(
    figure=FigureSpec(figsize=(7, 7), dpi=300, style="seaborn-v0_8-paper"),
    x=AxisSpec(label="X", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Y", scale=ScaleType.LINEAR),
    show_legend=True,
)


@plot_function(default_spec=DEFAULT_SPEC)
def plot_line(
    x: np.ndarray,
    y: np.ndarray,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        err (np.ndarray): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[BehavizAxes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        BehavizAxes | BehavizFigure: Plotted axes object if not standalone, otherwie will return the figure object
    """

    x, y = validate_and_fix_inputs(x, y)
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    r = get_renderer()
    r.line(ax, x, y, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC)
def plot_scatter(
    x: np.ndarray,
    y: np.ndarray,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        err (np.ndarray): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[BehavizAxes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        BehavizAxes | BehavizFigure: Plotted axes object if not standalone, otherwie will return the figure object
    """

    x, y = validate_and_fix_inputs(x, y)
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    r = get_renderer()
    r.scatter(ax, x, y, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC)
def plot_errorbar(
    x: np.ndarray,
    y: np.ndarray,
    err: np.ndarray,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        err (np.ndarray): The errorbar sizes
            shape(N,): Symmetric +/-values for each data point.
            shape(2, N): Separate - and + values for each bar. First row contains the lower errors, the second row contains the upper errors.
        ax (Optional[BehavizAxes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        BehavizAxes | BehavizFigure: Plotted axes object if not standalone, otherwie will return the figure object
    """

    x, y, err = validate_and_fix_inputs(x, y, err)
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

    r = get_renderer()
    r.errorbar(ax, x, y, err, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC)
def plot_violin(
    x: np.ndarray,
    ys: list[np.ndarray],
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """_summary_

    Args:
        x (np.ndarray): _description_
        ys (np.ndarray): _description_
        ax (Optional[BehavizAxes], optional): _description_. Defaults to None.
        spec (Optional[PlotSpec], optional): _description_. Defaults to None.

    Returns:
        BehavizAxes | BehavizFigure: _description_
    """

    x, y = validate_and_fix_inputs(x, ys)
    x = x.ravel()

    assert len(x) == len(ys), f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({len(ys)})."
    # make sure the data is in proper format -> a list

    r = get_renderer()
    vp = r.violin(ax, ys, x, **overrides)
    return ax, vp


@plot_function(default_spec=DEFAULT_SPEC)
def plot_step(
    x: np.ndarray,
    y: np.ndarray,
    where: Optional[Literal["pre", "post", "mid"]] = "pre",
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        where (Optional[Literal['pre','post','mid']], optional): where the steps should be placed. Defaults to "pre".
        ax (Optional[BehavizAxes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        BehavizAxes | BehavizFigure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    x, y = validate_and_fix_inputs(x, y)
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    r = get_renderer()
    r.step(ax, x, y, where, **overrides)
    return ax


@plot_function(default_spec=DEFAULT_SPEC)
def plot_bar(
    x: np.ndarray,
    y: np.ndarray,
    bottom: Optional[np.ndarray] = None,
    width: Optional[float | np.ndarray] = 0.2,
    ax: Optional[BehavizAxes] = None,
    spec: Optional[PlotSpec] = None,
    **overrides,
) -> tuple[BehavizFigure, BehavizAxes]:
    """_summary_

    Args:
        x (np.ndarray): x-axis values
        y (np.ndarray): y-axis values
        where (Optional[Literal['pre','post','mid']], optional): where the steps should be placed. Defaults to "pre".
        ax (Optional[BehavizAxes], optional): The axes object to plot on. Defaults to None, in which new figure and axes are created.
        spec (Optional[PlotSpec], optional): Plot specifications. Defaults to None, in which Psychometric plot defaults will be used.

    Returns:
        BehavizAxes | BehavizFigure: Plotted axes object if not standalone, otherwie will return the figure object
    """
    x, y, y_bottom = validate_and_fix_inputs(x, y, bottom)
    x = x.ravel()
    y = y.ravel()

    assert x.shape == y.shape, f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({y.shape})."

    if y_bottom is not None:
        y_bottom.ravel()
        assert y.shape == bottom.shape, (
            f"Shape of {spec.x.label}({x.shape}) is not equal to shape of {spec.y.label}({bottom.shape})."
        )

    r = get_renderer()
    print(overrides)
    r.bar(ax, x, y, width=width, bottom=bottom, **overrides)

    return ax
