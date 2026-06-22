# Data input

!!! note "Stub — to be expanded"

behaviz accepts numpy arrays directly, or **column names** resolved against a `data=`
source (a pandas/polars DataFrame or a dict).

## Resolution rules

```python
bv.plot_line("t", "signal", data=df)        # keyword column names
bv.plot_line("t", "signal", data=df)        # positional column names
bv.plot_line("t", raw_array, data=df)       # mix: column name + raw array
```

_TODO: full rules; dict source; positional vs keyword; mixing arrays and columns. Pull from
README §"Plotting from DataFrames and dicts"._

## Validation & errors

Inputs pass through a declarative **channel** layer that checks kind and length before any
backend sees them. Failures raise `BehavizDataError` with a message, the offending channel,
and a hint.

_TODO: example error output from README §"Input handling & errors"._

## See also

- [Grouping](grouping.md) — split by `hue=` / `group=`.
