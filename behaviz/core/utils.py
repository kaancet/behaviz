import numbers
import numpy as np


def validate_and_fix_inputs(*ins):
    """
    Validate and normalize one or more numeric inputs into NumPy arrays.

    Accepts scalars, lists, tuples, and NumPy arrays (or None), and converts
    them into a consistent NumPy-based format. Mixed types within a single
    input are not supported.

    Parameters
    ----------
    *ins : int, float, list, tuple, np.ndarray, or None
        One or more inputs to validate and convert. Each input may be:
        - A scalar number → converted to a 1D np.ndarray of length 1.
        - A flat list or tuple of numbers → converted to a 1D np.ndarray.
        - A list or tuple of lists/tuples/arrays → converted to a list of np.ndarrays.
        - An np.ndarray → passed through unchanged.
        - None → passed through unchanged.

    Returns
    -------
    np.ndarray, list of np.ndarray, None, or tuple thereof
        - If a single input is provided, returns the converted value directly.
        - If multiple inputs are provided, returns a tuple of converted values.

    Raises
    ------
    ValueError
        If a list or tuple contains a mix of scalars and sequences.
    TypeError
        If an input is not a scalar, numeric sequence, list, tuple, np.ndarray, or None.

    Examples
    --------
    >>> validate_and_fix_inputs(42)
    array([42])

    >>> validate_and_fix_inputs([1, 2, 3])
    array([1, 2, 3])

    >>> validate_and_fix_inputs([[1, 2], [3, 4]])
    [array([1, 2]), array([3, 4])]

    >>> validate_and_fix_inputs([1, 2, 3], [4, 5, 6])
    (array([1, 2, 3]), array([4, 5, 6]))

    >>> validate_and_fix_inputs([1, 2, 3], None)
    (array([1, 2, 3]), None)
    """

    out = []
    for _in in ins:
        if isinstance(_in, (list, tuple)):
            if all(isinstance(x, numbers.Number) for x in _in):
                # list of numbers -> np.array(numbers)
                out.append(np.asarray(_in))
            elif all(isinstance(x, (list, tuple, np.ndarray)) for x in _in):
                # list of lists -> list of np.arrays
                out.append([np.asarray(i) for i in _in])
            else:
                raise ValueError("mixed types are not allowed yet")
        elif isinstance(_in, np.ndarray):
            out.append(_in)
        elif isinstance(_in, numbers.Number):
            out.append(_in)
        elif _in is None:
            out.append(_in)
        else:
            raise TypeError(f"Ony numeric sequences are allowed, got: {_in}")
    if len(out) == 1:
        return out[0]
    else:
        return tuple(out)
