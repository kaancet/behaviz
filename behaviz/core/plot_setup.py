import functools
from dataclasses import replace
from typing import Optional, Callable, Sequence

from ..backends.renderer_manager import get_renderer
from ..backends.renderer import BehavizAxes
from ..spec.plot_spec import PlotSpec
from .data_source import resolve
from .channels import Channel, coerce_channel, check_lengths
from .errors import data_error, describe

# Channel names that map onto an axis for label auto-filling.
_CHANNEL_AXIS = {"x": "x", "y": "y", "ys": "y", "y1": "y"}


def plot_function(default_spec: PlotSpec, channels: Sequence[Channel] = ()):
    """
    Decorator factory for behaviz plot functions.

    Parameters
    ----------
    default_spec : PlotSpec
        The module-level default spec to use when the caller does not supply one.
    channels : Sequence[Channel]
        Declarative contracts for the function's data-carrying parameters, in
        the same order as its leading positional parameters. For every declared
        channel the decorator:
          1. binds it to the matching positional arg or keyword,
          2. resolves a column-name string against the ``data=`` keyword
             (which is reserved and consumed here — it never reaches the body),
          3. coerces the value to the channel's kind (scalars to length-1
             arrays, trivial 2-D squeezed, 2-D-to-list-of-rows for "vectors"…),
          4. enforces ``same_length_as`` constraints with errors that name the
             offending parameter.
        The function body therefore always sees clean, normalised arrays.

    The wrapped function must accept `ax` and `spec` as keyword-only arguments
    and must return either:
      - ax                    (simple case)
      - (ax, extra_object)    (e.g. violinplot returns the vplot dict too)
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, ax: Optional[BehavizAxes] = None, spec: Optional[PlotSpec] = None, **kwargs):

            spec = spec or default_spec

            if channels:
                data = kwargs.pop("data", None)
                # wrapper.__name__ (not fn.__name__): factory-generated plots
                # overwrite the wrapper's name with their public name.
                args, kwargs, spec = _apply_channels(wrapper.__name__, channels, args, kwargs, data, spec)

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


def _apply_channels(
    func_name: str,
    channels: Sequence[Channel],
    args: tuple,
    kwargs: dict,
    data,
    spec: PlotSpec,
) -> tuple[tuple, dict, PlotSpec]:
    """Bind, resolve, coerce and cross-check the declared data channels.

    Returns the rewritten args/kwargs plus a spec that may have had its x/y
    axis labels auto-filled from originating column names.
    """
    args = list(args)
    bound: dict = {}

    for i, ch in enumerate(channels):
        if i < len(args):
            raw, slot = args[i], ("args", i)
        elif ch.name in kwargs:
            raw, slot = kwargs[ch.name], ("kwargs", ch.name)
        else:
            continue  # not supplied — the function signature's default applies

        if isinstance(raw, str):
            if data is None:
                raise data_error(
                    func_name,
                    f"`{ch.name}` is a string but no `data=` was given.",
                    details={ch.name: describe(raw)},
                    hint="pass data=<dataframe or dict of arrays> to plot by column name, "
                    "or pass the values themselves.",
                )
            value = resolve(raw, data)
            # Free clarity win: when a channel came from a named column and the
            # matching axis has no label yet, use the column name.
            if ch.name in _CHANNEL_AXIS:
                spec = _autolabel(spec, _CHANNEL_AXIS[ch.name], raw)
        else:
            value = raw

        coerced = coerce_channel(func_name, ch, value)
        bound[ch.name] = coerced
        if slot[0] == "args":
            args[slot[1]] = coerced
        else:
            kwargs[slot[1]] = coerced

    check_lengths(func_name, channels, bound)
    return tuple(args), kwargs, spec


def _autolabel(spec: PlotSpec, axis_name: str, column: str) -> PlotSpec:
    """Fill an empty x/y axis label from a column name (immutably)."""
    axis = getattr(spec, axis_name)
    if not axis.label:
        return replace(spec, **{axis_name: replace(axis, label=column)})
    return spec
