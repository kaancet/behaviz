import copy
import inspect
import functools
import matplotlib.axes
import matplotlib.pyplot as plt
from collections.abc import Sequence, Mapping
from matplotlib.artist import ArtistInspector



def call_mpl(ax, method: str, *args, **kwargs):
    """Call ax.plot / ax.scatter / etc. with automatic kwarg routing."""
    from matplotlib.container import ErrorbarContainer
    func = getattr(ax, method)
    call_kwargs = get_valid_call_kwargs(method, kwargs)
    artist_kwargs = get_valid_artist_kwargs(method, kwargs)
    
    # anything the user passed explicitly that wasn't routed into the call
    # should still be applied post-hoc
    unrouted = {k: v for k, v in kwargs.items() if k not in call_kwargs}
    artist_kwargs = {**artist_kwargs, **unrouted}
    
    result = func(*args, **call_kwargs)
    if isinstance(result, ErrorbarContainer):
        apply_artist_kwargs_errorbar(result, artist_kwargs, call_kwargs)
    else:
        apply_artist_kwargs(result, artist_kwargs)
    return result


def _flatten_artists(obj):
    """
    Recursively yield matplotlib artists from arbitrary containers.

    Handles:
        - single artists
        - lists/tuples
        - dicts
        - nested combinations
    """
    from matplotlib.container import ErrorbarContainer, BarContainer, StemContainer
    
    if isinstance(obj, (ErrorbarContainer, BarContainer, StemContainer)):
        for child in obj.get_children():
            yield from _flatten_artists(child)
    
    elif isinstance(obj, Mapping):
        for v in obj.values():
            yield from _flatten_artists(v)

    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        for item in obj:
            yield from _flatten_artists(item)

    else:
        yield obj


def get_valid_call_kwargs(plot_type: str, kwargs: dict) -> dict:
    """
    Returns kwargs accepted directly by the plotting function itself.

    Example:
        scatter(..., s=10, c='r')

    but NOT:
        facecolor
        alpha
        etc. unless explicitly exposed by the function.
    """

    func = getattr(matplotlib.axes.Axes, plot_type)

    sig = inspect.signature(func)

    valid = set(sig.parameters.keys())

    return {k: v for k, v in kwargs.items() if k in valid}


def get_valid_artist_kwargs(plot_type: str, kwargs: dict) -> dict:
    """
    Returns kwargs valid on at least one returned artist.

    This allows post-hoc styling of returned artists for functions like:
        violinplot
        boxplot
        errorbar
        contourf
        etc.
    """
    
    dummy_f, dummy_ax = plt.subplots()

    try:
        func = getattr(matplotlib.axes.Axes, plot_type)
        dummy_args = {
            "plot": ([0, 1], [0, 1]),
            "scatter": ([0, 1], [0, 1]),
            "bar": ([0, 1], [1, 2]),
            "step": ([0, 1], [0, 1]),
            "errorbar": ([0, 1], [0, 1]),
            "fill_between": ([0, 1], [0, 1]),
            "violinplot": ([[0, 1], [1, 2]],),
            "boxplot": ([[0, 1], [1, 2]],),
            "hist": ([0, 1, 2],),
        }
        
        args = dummy_args.get(plot_type, ([0, 1], [0, 1]))
        result = func(dummy_ax, *args)
        valid_setters = set()

        for artist in _flatten_artists(result):
            try:
                setters = ArtistInspector(artist).get_setters()
                valid_setters.update(setters)
            except Exception:
                pass
        return {k: v for k, v in kwargs.items() if k in valid_setters}
    finally:
        plt.close(dummy_f)
        

def apply_artist_kwargs(obj, kwargs):
    """
    Recursively apply kwargs to matplotlib artists.

    Attempts:
        artist.set_<property>(value)

    Ignores unsupported setters gracefully.
    """

    for artist in _flatten_artists(obj):
        for k, v in kwargs.items():
            setter = f"set_{k}"
            if hasattr(artist, setter):
                try:
                    getattr(artist, setter)(v)
                except Exception:
                    # Ignore invalid setter calls
                    pass


def apply_artist_kwargs_errorbar(result, artist_kwargs, call_kwargs):
    """
    Special-case handler for errorbar's ErrorbarContainer.
    
    errorbar has call-time kwargs that target specific child artists:
      elinewidth -> LineCollection (error bars)
      capthick   -> caplines (Line2D)
      ecolor     -> both LineCollection and caplines
    
    Post-hoc artist kwargs (linewidth, markersize etc.) should only
    go to the data Line2D — not to children already configured by
    their dedicated call-time kwarg.
    """
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D

    # which child types are already owned by a call-time kwarg
    call_owned_types = set()
    if "elinewidth" in call_kwargs or "capthick" in call_kwargs:
        call_owned_types.add(LineCollection)

    for child in result.get_children():
        if isinstance(child, tuple(call_owned_types)):
            continue   # already configured, don't touch
        for k, v in artist_kwargs.items():
            setter = f"set_{k}"
            if hasattr(child, setter):
                try:
                    getattr(child, setter)(v)
                except Exception:
                    pass