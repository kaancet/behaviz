import copy
import inspect
import functools
import matplotlib.axes
import matplotlib.pyplot as plt
from collections.abc import Sequence, Mapping
from matplotlib.artist import ArtistInspector
from dataclasses import is_dataclass, replace


def _flatten_artists(obj):
    """
    Recursively yield matplotlib artists from arbitrary containers.

    Handles:
        - single artists
        - lists/tuples
        - dicts
        - nested combinations
    """

    if isinstance(obj, Mapping):
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


def override_plots(methods_to_override=None):
    """
    Overrides matplotlib Axes methods by creating versions prefixed with "_".

    Example:
        ax._scatter(..., mpl_kwargs={...})

    The wrapper:
        1. separates valid function kwargs
        2. applies remaining valid artist kwargs post-hoc
    """
    
    if methods_to_override is None:
        methods_to_override = [
            "plot",
            "scatter",
            "bar",
            "step",
            "errorbar",
            "fill_between",
            "violinplot",
            "boxplot",
            "hist",
        ]

    original_methods = {}
    for meth in methods_to_override:

        original_method = getattr(matplotlib.axes.Axes, meth)

        original_methods[meth] = original_method

        def create_custom_method(name, method):

            @functools.wraps(method)
            def custom_method(self, *args, **kwargs):

                mpl_kwargs = copy.deepcopy(kwargs.pop("mpl_kwargs", {}))
                # seperate kwargs
                call_kwargs = get_valid_call_kwargs(plot_type=name, kwargs=mpl_kwargs)
                
                artist_kwargs = get_valid_artist_kwargs(plot_type=name,kwargs=mpl_kwargs)
                # explicit kwargs override mpl_kwargs
                final_call_kwargs = {**call_kwargs,**kwargs}

                # create plot
                result = method(self,*args,**final_call_kwargs)

                # artist post process
                apply_artist_kwargs(result,artist_kwargs)

                return result

            return custom_method

        custom = create_custom_method(
            meth,
            original_method,
        )

        setattr(
            matplotlib.axes.Axes,
            f"_{meth}",
            custom,
        )            


# def get_valid_mpl_kwargs(plot_type: str, mpl_kwargs: dict) -> dict:
#     """Returns the subset of values that are valid for the given plot type

#     Args:
#         plot_type: Type of the plotting function (e.g. "plot", "scatter")
#         mpl_kwargs: dictionary with all the matplotlib keeyword arguments

#     Returns:
#         dict: Valid kwargs for given plot type
#     """
#     def get_root(obj):
#         if isinstance(obj, Sequence):
#             # sometimes matplotlib returns a tuple/list of objects; just get the first
#             return obj[0]
#         elif isinstance(obj, Mapping):
#             _key, _val = next(iter(obj.items()))
#             return _val
#         return obj

#     dummy_f, dummy_ax = plt.subplots(1, 1)
#     func = getattr(
#         matplotlib.axes.Axes, plot_type
#     )  # Get the function dynamically (e.g., plt.plot, plt.scatter, etc.)

#     dummy_ax.remove()
#     dummy_f.clear()
#     plt.close(dummy_f)

#     sig = inspect.signature(func)

#     valid_kwds = ArtistInspector(
#         get_root(func(dummy_ax, [0], [0]))
#     ).get_setters() + list(sig.parameters.keys())
#     # Filter mpl_kwargs to only include valid parameters
#     return {k: v for k, v in mpl_kwargs.items() if k in valid_kwds}


# def override_plots(methods_to_override: list[str] | None = None) -> None:
#     """Overrides matplotlib.axes plots with "_" prepended to the name,
#     Currently the overriding function checks and filters the valid kwargs for the overriden plot

#     Args:
#         methods_to_override (list[str] | None, optional): List of matplotlib plots to override. Defaults to None.
#     """
#     if methods_to_override is None:
#         methods_to_override = [
#             "plot",
#             "errorbar",
#             "scatter",
#             "bar",
#             "step",
#             "violinplot",
#             "fill_between",
#         ]

#     original_methods = {}
#     for meth in methods_to_override:
#         original_methods[meth] = getattr(matplotlib.axes.Axes, meth)

#         def create_custom_method(name, method):
#             @functools.wraps(original_methods[meth])
#             def custom_method(self, *args, **kwargs):
#                 valid_kwargs = get_valid_mpl_kwargs(
#                     plot_type=name, mpl_kwargs=kwargs.get("mpl_kwargs", {})
#                 )
#                 good_kwargs = copy.deepcopy({**kwargs, **valid_kwargs})
#                 good_kwargs.pop("mpl_kwargs", {})

#                 return method(self, *args, **good_kwargs)

#             return custom_method

#         cust_meth = create_custom_method(meth, original_methods[meth])
#         setattr(matplotlib.axes.Axes, f"_{meth}", cust_meth)


# def override_walk(obj, replace_dict:dict):
#     """Recursive walk through an objects fields to override values

#     Args:
#         obj (_type_): Object to be walked on
#         replace_dict (dict): Dictionary with a single key value pair of the name and new value of the to be changed attribute

#     Returns:
#         _type_: _description_
#     """

#     _key, _val = next(iter(replace_dict.items()))
#     # Primitive types: stop recursion
#     if isinstance(obj, (str, int, float, bool, type(None))):
#         return obj

#     # Dictionaries
#     if isinstance(obj, Mapping):
#         for k, v in obj.items():
#             if k == _key:
#                 obj[k] = _val
#                 return obj
#             else:
#                 override_walk(v,replace_dict)
#         return obj

#     # Dataclasses
#     if is_dataclass(obj):
#         for field_name in obj.__dataclass_fields__:
#             if field_name == _key:
#                 return replace(obj, **{_key:_val})
#             else:
#                 override_walk(getattr(obj, field_name),replace_dict)
#         return obj

#     # Generic custom classes
#     if hasattr(obj, "__dict__"):
#         for k, v in vars(obj).items():
#             if k == _key:
#                 setattr(obj,_key,_val)
#                 return obj
#             else:
#                 override_walk(v,replace_dict)
#         return obj