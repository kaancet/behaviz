# Saving & display

!!! note "Stub — to be expanded"

## `bv.save`

Dispatches on the active backend and the file extension.

```python
fig, ax = bv.plot_line(x, y)
bv.save(fig, "out.png")        # mpl/seaborn: png/svg/pdf/...; bokeh: html/png/svg
```

Failures raise `BehavizSaveError` (a `ValueError`) with the format and what's missing (e.g.
a browser driver for bokeh png/svg).

## `bv.canvas` context manager

Group several draws onto one axes; optionally save and/or show on exit.

```python
with bv.canvas(spec=spec, save="out.png", show=False) as ax:
    bv.plot_line("t", "signal", data=df)
    bv.plot_scatter("t", "signal", data=df)
```

Reuse a pre-made axes:

```python
import matplotlib.pyplot as plt
f, axs = plt.subplots(1, 2)
with bv.canvas(ax=axs[0]) as ax:
    bv.plot_line(x, y)
```

_TODO: format matrix per backend; show() semantics; canvas spec precedence._
