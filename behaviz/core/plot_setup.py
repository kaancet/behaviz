import functools
from dataclasses import replace
from typing import Optional, Callable, Sequence

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes
from ..spec.plot_spec import PlotSpec
from .data_source import resolve


def plot_function(default_spec: PlotSpec, data_args: Sequence[str] = ()):
    """
    Decorator factory for behaviz plot functions.

    Parameters
    ----------
    default_spec : PlotSpec
        The module-level default spec to use when the caller does not supply one.
    data_args : Sequence[str]
        Names of the leading data channels for this function (e.g. ``("x", "y")``
        or ``("x", "y", "err")``). When declared, the decorator transparently
        accepts a ``data=`` keyword: any channel passed as a column-name string is
        resolved against ``data`` into a numpy array *before* the wrapped function
        runs — so the function body keeps seeing plain arrays and never changes.

    The wrapped function must accept `ax` and `spec` as keyword-only arguments
    and must return either:
      - ax                    (simple case)
      - (ax, extra_object)    (e.g. violinplot returns the vplot dict too)
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, ax: Optional[BehavizAxes] = None, spec: Optional[PlotSpec] = None, **kwargs):

            spec = spec or default_spec

            # `data` is a reserved keyword consumed here; it never reaches the
            # function body or the backend.
            data = kwargs.pop("data", None)
            if data_args:
                args, kwargs, spec = _resolve_data_args(data_args, args, kwargs, data, spec)

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


def _resolve_data_args(
    data_args: Sequence[str],
    args: tuple,
    kwargs: dict,
    data,
    spec: PlotSpec,
) -> tuple[tuple, dict, PlotSpec]:
    """Resolve declared data channels (positional or keyword) into arrays.

    Returns the (possibly) rewritten args/kwargs plus a spec that may have had
    its x/y axis labels auto-filled from the originating column names.
    """
    args = list(args)
    for i, name in enumerate(data_args):
        if i < len(args):
            raw = args[i]
            args[i] = resolve(raw, data)
        elif name in kwargs:
            raw = kwargs[name]
            kwargs[name] = resolve(raw, data)
        else:
            continue  # channel not supplied (optional)

        # Free clarity win: when a channel came from a named column and the
        # matching axis has no label yet, use the column name.
        if data is not None and isinstance(raw, str) and name in ("x", "y"):
            spec = _autolabel(spec, name, raw)

    return tuple(args), kwargs, spec


def _autolabel(spec: PlotSpec, axis_name: str, column: str) -> PlotSpec:
    """Fill an empty x/y axis label from a column name (immutably)."""
    axis = getattr(spec, axis_name)
    if not axis.label:
        return replace(spec, **{axis_name: replace(axis, label=column)})
    return spec
