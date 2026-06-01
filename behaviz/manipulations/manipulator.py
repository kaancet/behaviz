from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from dataclasses import dataclass, field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .jitter import _JitterStrategy
    from .smoother import _SmootherStrategy
    from .normaliser import _NormaliserStrategy
    from .binner import _BinnerStrategy

from .jitter import UniformJitter, NormalJitter, BeeswarmJitter
from .smoother import BoxcarSmooth, GaussianSmooth
from .normaliser import MinMaxNormaliser, BaselineNormaliser, ZScoreNormaliser
from .binner import MeanBinner, MedianBinner, SumBinner, CountBinner


_JITTER_STRATEGIES: dict[str, "_JitterStrategy"] = {
    "uniform": UniformJitter(),
    "normal": NormalJitter(),
    "beeswarm": BeeswarmJitter(),
}

_SMOOTHER_STRATEGIES: dict[str, "_SmootherStrategy"] = {
    "boxcar": BoxcarSmooth(),
    "gaussian": GaussianSmooth(),
}

_NORMALISER_STRATEGIES: dict[str, "_NormaliserStrategy"] = {
    "minmax": MinMaxNormaliser(),
    "baseline": BaselineNormaliser(),
    "zscore": ZScoreNormaliser(),
}

_BINNER_STRATEGIES: dict[str, "_BinnerStrategy"] = {
    "mean": MeanBinner(),
    "median": MedianBinner(),
    "sum": SumBinner(),
    "count": CountBinner(),
}

# TODO: Do a better registry system for strategies
_STRATEGIES = {
    "jitter": _JITTER_STRATEGIES,
    "smoother": _SMOOTHER_STRATEGIES,
    "normaliser": _NORMALISER_STRATEGIES,
    "binner": _BINNER_STRATEGIES,
}


@dataclass(frozen=True)
class ManipulationResult:
    """
    Immutable container for a manipulated coordinate pair.

    x_original and y_original are stored so the caller can always
    retrieve the untouched data from the same object.
    """

    x: np.ndarray
    y: np.ndarray
    x_original: np.ndarray
    y_original: np.ndarray
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        # Make every stored array read-only — cannot be mutated in-place
        object.__setattr__(self, "x", _freeze(self.x))
        object.__setattr__(self, "y", _freeze(self.y))
        object.__setattr__(self, "x_original", _freeze(self.x_original))
        object.__setattr__(self, "y_original", _freeze(self.y_original))


def _freeze(arr: np.ndarray) -> np.ndarray:
    """Return a read-only copy — prevents in-place mutation by the caller."""
    out = np.array(arr, copy=True)
    out.flags.writeable = False
    return out


class VisualManipulator:
    """
    Object for visual data manipulation.

    All methods return a ManipulationResult.  The original data is
    never modified — this is enforced by:
      1. Copying all inputs immediately.
      2. Marking stored arrays as read-only via numpy flags.
      3. Returning a frozen dataclass.

    Seeding
    -------
    Pass seed= for reproducible jitter.  The seed is stored so that
    calling the same method twice on the same manipulator produces the
    same result (useful for aligning jittered x with jittered y).

    Usage
    -----
    >>> vm = VisualManipulator(seed=42)
    >>> result = vm.jitter(x, y, axis="x", strength=0.03)
    >>> plot_scatter(result.x, result.y)
    """

    def __init__(self, seed: int | None = None):
        self._seed = seed
        self._rng = np.random.default_rng(seed)

    def reset(self) -> "VisualManipulator":
        """Re-seed the RNG — useful to reproduce the exact same jitter."""
        self._rng = np.random.default_rng(self._seed)
        return self

    def jitter(
        self,
        x: ArrayLike,
        y: ArrayLike,
        strength: float = 0.05,  # uniform half-width  OR  normal sigma
        bin_width: float = 20,  # for beeswarm
        *,
        kind: str = "uniform",
        axis: str = "x",  # "x" | "y"
        **params,
    ) -> ManipulationResult:
        """
        Add noise to x or y without touching the originals.

        Parameters
        ----------
        kind : "uniform" | "normal" | "beeswarm"
            Distribution to draw jitter from.
        axis : "x" | "y"
            Which coordinate(s) to perturb.
        strength : float
            Uniform:  half-width of the uniform distribution.
            Normal:   sigma of the normal distribution.
            Beeswarm:
        """

        x_in, y_in = self._copy_pair(x, y)
        strategy = self._get_strategy("jitter", kind)

        x_out, y_out = strategy.apply(
            x_in, y_in, self._rng, axis=axis, strength=strength, sigma=strength, bin_width=bin_width, **params
        )

        return ManipulationResult(
            x_out, y_out, x, y, metadata={"kind": kind, "axis": axis, "strength": strength, "bin_width": bin_width}
        )

    def normalise(
        self,
        x: ArrayLike,
        y: ArrayLike,
        *,
        kind: str = "minmax",  # "minmax" | "zscore" | "baseline"
        axis: str = "y",  # "x" | "y"
        baseline_idx: slice | None = None,
        **params,
    ) -> ManipulationResult:
        """
        Normalise x or y without touching the originals.

        Parameters
        ----------
        kind : "minmax" | "zscore" | "baseline"
            Distribution to draw jitter from.
        axis : "x" | "y"
            Which coordinate(s) to perturb.
        baseline_idx : slice
            The indeces to be considered as baseline. USed only for "baseline" method
        """
        x_in, y_in = self._copy_pair(x, y)
        strategy = self._get_strategy("normaliser", kind)

        x_out, y_out = strategy.apply(x_in, y_in, axis=axis, baseline_idx=baseline_idx, **params)

        return ManipulationResult(
            x_out, y_out, x, y, metadata={"kind": kind, "axis": axis, "baseline_idx": baseline_idx}
        )

    def smooth(
        self,
        x: ArrayLike,
        y: ArrayLike,
        *,
        kind: str = "boxcar",  # "boxcar" | "gaussian"
        axis: str = "y",  # "x" | "y"
        window: int = 5,
        sigma: float = 1.0,
        **params,
    ) -> ManipulationResult:
        """
        Convolve x or y with a smoothing kernel, without touching the originals"""

        x_in, y_in = self._copy_pair(x, y)
        strategy = self._get_strategy("smoother", kind)

        x_out, y_out = strategy.apply(x_in, y_in, axis=axis, window=window, sigma=sigma, **params)

        return ManipulationResult(
            x_out, y_out, x, y, metadata={"kind": kind, "axis": axis, "window": window, "sigma": sigma}
        )

    def binning(
        self,
        x: ArrayLike,
        y: ArrayLike,
        bins: int | ArrayLike = 10,
        *,
        kind: str = "count",  # "mean" | "median" | "sum" | "count"
        axis: str = "y",  # "x" | "y"
        **params,
    ) -> ManipulationResult:
        """Bin x or y and aggregate the other within each bin, without touching the originals

        Args:
            x (ArrayLike): _description_
            y (ArrayLike): _description_
            kind (str, optional): _description_. Defaults to "boxcar".

        Raises:
            ValueError: _description_
            ValueError: _description_

        Returns:
            ManipulationResult: _description_
        """

        x_in, y_in = self._copy_pair(x, y)
        strategy = self._get_strategy("binner", kind)

        x_out, y_out = strategy.apply(x_in, y_in, bins=bins, axis=axis, **params)

        return ManipulationResult(x_out, y_out, x, y, metadata={"kind": kind, "axis": axis, "bins": bins})

    @staticmethod
    def _copy_arr(a: ArrayLike) -> np.ndarray:
        return np.array(a, copy=True, dtype=float)

    @staticmethod
    def _copy_pair(x: ArrayLike, y: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
        return VisualManipulator._copy_arr(x), VisualManipulator._copy_arr(y)

    @staticmethod
    def register_strategy(name: str, strategy_kind, strategy: _JitterStrategy) -> None:
        """
        Add a custom jitter strategy so it's available via kind=name.

        >>> class MyJitter(_JitterStrategy):
        ...     def apply(self, x, y, ...): ...
        >>> VisualManipulator.register_strategy("mine", MyJitter())
        >>> vm.jitter(x, y, kind="mine")
        """
        _STRATEGIES[strategy_kind][name] = strategy

    def _get_strategy(self, strategy_kind, name: str) -> _JitterStrategy:

        if strategy_kind not in _STRATEGIES:
            raise ValueError(f"{strategy_kind} is not a valid VisualManipulator strategy. Try {_STRATEGIES}")

        if name not in _STRATEGIES[strategy_kind]:
            raise ValueError(
                f"Unknown {strategy_kind} kind '{name}'. "
                f"Available: {list(_STRATEGIES[strategy_kind])}. "
                "Use VisualManipulator.register_strategy() to add custom ones."
            )
        return _STRATEGIES[strategy_kind][name]
