import matplotlib
matplotlib.use("Agg")   # must happen before any other mpl import

import numpy as np
import pytest
import matplotlib.pyplot as plt


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def xy():
    """Simple 1-D x/y arrays for line / scatter / errorbar tests."""
    x = np.linspace(0, 10, 50)
    y = np.sin(x)
    return x, y


@pytest.fixture
def xy_err(xy):
    """Same as xy but with a symmetric error array."""
    x, y = xy
    err = np.full_like(y, 0.1)
    return x, y, err


@pytest.fixture
def xy_err_2row(xy):
    """Asymmetric errors: shape (2, N)."""
    x, y = xy
    err = np.vstack([np.full_like(y, 0.05), np.full_like(y, 0.15)])
    return x, y, err


@pytest.fixture
def group_data():
    """x positions + list-of-arrays for violin / rain plots."""
    rng = np.random.default_rng(42)
    x = np.array([1.0, 2.0, 3.0])
    ys = [rng.normal(loc=xi, scale=0.5, size=30) for xi in x]
    return x, ys


@pytest.fixture
def existing_ax():
    """A pre-existing Axes the caller can pass in (non-standalone mode)."""
    fig, ax = plt.subplots()
    return fig, ax