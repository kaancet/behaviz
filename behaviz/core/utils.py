import numbers
import numpy as np

from collections.abc import Sequence


def validate_and_fix_inputs(*ins):
    """ """

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
        else:
            raise TypeError(f"Ony numeric sequences are allowed, got: {_in}")
    if len(out) == 1:
        return out[0]
    else:
        return tuple(out)
