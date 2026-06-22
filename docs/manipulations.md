# Manipulators

!!! note "Stub — to be expanded"

Visual data manipulators are explicit, shape-aware transforms you apply to data before
plotting. They live in `behaviz.manipulations` and share a `VisualManipulator` contract.

## Families

| Family | Classes |
|---|---|
| **Jitter** | `UniformJitter`, `NormalJitter`, `BeeswarmJitter` |
| **Smoothing** | `BoxcarSmooth`, `GaussianSmooth` |
| **Normalising** | `BaselineNormaliser`, `MinMaxNormaliser`, `ZScoreNormaliser` |
| **Binning** | `CountBinner`, `MeanBinner`, `MedianBinner`, `SumBinner` |
| **Dodging** | (used internally by [grouping](grouping.md)) |

```python
from behaviz.manipulations import GaussianSmooth, ZScoreNormaliser
y2 = GaussianSmooth(sigma=2).apply(y)
```

_TODO: the shared contract/shape guarantee; chaining; one worked example per family; pull
from README §"Visual data manipulators"._
