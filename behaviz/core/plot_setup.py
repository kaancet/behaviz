import functools
from typing import Optional, Callable

from .renderer_manager import get_renderer
from .renderer import BehavizAxes
from ..spec.plot_spec import PlotSpec


def plot_function(default_spec: PlotSpec):
    """
    Decorator factory for behaviz plot functions.

    Parameters
    ----------
    default_spec : PlotSpec
        The module-level default spec to use when the caller does not supply one.

    The wrapped function must accept `ax` and `spec` as keyword-only arguments
    and must return either:
      - ax                    (simple case)
      - (ax, extra_object)    (e.g. violinplot returns the vplot dict too)
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, ax: Optional[BehavizAxes] = None, spec: Optional[PlotSpec] = None, **kwargs):

            spec = spec or default_spec
            standalone = ax is None

            if standalone:
                fig, ax_ = get_renderer().make_figure(spec)
            else:
                fig = get_renderer().get_figure(ax)
                ax_ = ax

            result = fn(*args, ax=ax_, spec=spec, **kwargs)

            # Support (ax, extra) return values (e.g. violinplot)
            if isinstance(result, tuple):
                returned_ax, extra = result[0], result[1:]
                get_renderer().apply_axis_spec(returned_ax, spec)
                return (fig, returned_ax, *extra)
            else:
                returned_ax = result
                get_renderer().apply_axis_spec(returned_ax, spec)
                return fig, result

        return wrapper

    return decorator
