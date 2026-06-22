# Overriding

!!! note "Stub — to be expanded"

Beyond the spec, any extra keyword to a plot function is an **override** routed to the
active backend.

## Keyword passthrough

```python
bv.plot_line(x, y, color="firebrick", linewidth=2, alpha=0.7, label="trial 1")
```

behaviz maps canonical names to native ones per backend (`color` → mpl `color` /
bokeh `line_color`+`fill_color`; `label` → `legend_label`). Backend-specific kwargs you pass
that aren't canonical are forwarded as-is.

## The `post_hook`

For anything the spec doesn't model, attach a hook that receives `(ax, spec)` after drawing.
For bokeh, `ax` **is** the figure.

```python
def style_ticks(fig, spec):
    for axis in (fig.xaxis, fig.yaxis):
        axis.major_tick_out = 8           # tick length
        axis.major_tick_line_width = 2    # tick width

spec = bv.PlotSpec().with_hook(style_ticks)
bv.plot_line(x, y, spec=spec)
```

## Reaching raw backend properties

You can also grab the returned `(fig, ax)` and set native properties directly, or use the
[canvas](saving.md) context manager.

## Registering a custom dodge strategy

```python
from behaviz.manipulations.dodger import _DodgeStrategy, DodgePlacement, _DODGE_STRATEGIES
import numpy as np

class NoDodge(_DodgeStrategy):
    def place(self, level, n_levels, x, y, *, total_width, state):
        return DodgePlacement(x=np.asarray(x, dtype=float), width=total_width)

_DODGE_STRATEGIES["none"] = NoDodge()
bv.plot_errorbar("x", "y", data=df, hue="cond", dodge="none")
```

_TODO: full canonical→native kwarg table per backend._
