from __future__ import annotations

from typing import Any, Sequence


def split_styles(
    overrides: dict[str, Any],
    components: Sequence[str],
    defaults: dict[str, dict] | None = None,
) -> dict[str, dict]:
    """Distribute a composite plot's ``**overrides`` across its sub-components.

    Precedence, lowest to highest (later wins):

    1. ``defaults[component]`` — the composite function's own defaults.
    2. **shared** overrides — un-prefixed kwargs the caller passed; applied to
       *every* component (e.g. ``color="red"`` recolours the whole composite).
    3. **component** overrides — kwargs prefixed ``"<component>_"``; applied to
       that one component only (e.g. ``dot_color="black"``).

    Because each component's kwargs are merged into a single dict, the caller can
    override a default without ever triggering a "multiple values" error.

    Parameters
    ----------
    overrides
        The ``**overrides`` captured by the composite plot function.
    components
        Sub-component names, used as the override prefixes, e.g. ``("bar", "dot")``.
    defaults
        Optional ``{component: {kwarg: value}}`` of composite-supplied defaults.

    Returns
    -------
    dict[str, dict]
        ``{component: kwargs}`` — splat each into the matching sub-plot call.

    Examples
    --------
    >>> def plot_lollipop(x, y, ax=None, spec=None, **overrides):
    ...     style = split_styles(
    ...         overrides,
    ...         components=("bar", "dot"),
    ...         defaults={"bar": {"color": "navy"}, "dot": {"color": "navy"}},
    ...     )
    ...     _, ax = plot_bar(x, y, ax=ax, spec=spec, **style["bar"])
    ...     _, ax = plot_scatter(x, y, ax=ax, spec=spec, **style["dot"])
    ...     return ax

    ``plot_lollipop(x, y)`` → both navy; ``plot_lollipop(x, y, color="red")`` →
    both red; ``plot_lollipop(x, y, dot_color="black")`` → navy bar, black dot.
    """
    defaults = defaults or {}
    shared: dict[str, Any] = {}
    specific: dict[str, dict] = {c: {} for c in components}

    for key, value in overrides.items():
        for component in components:
            prefix = f"{component}_"
            if key.startswith(prefix):
                specific[component][key[len(prefix) :]] = value
                break
        else:
            # No component prefix matched → it's a shared override.
            shared[key] = value

    return {c: {**defaults.get(c, {}), **shared, **specific[c]} for c in components}
