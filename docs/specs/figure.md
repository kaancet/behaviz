# FigureSpec

!!! note "Stub — to be expanded"

`spec.figure` is a `FigureSpec`.

| Field | Default | Meaning |
|---|---|---|
| `figsize` | `(12, 8)` | figure size in inches |
| `dpi` | `120` | dots per inch |
| `tight` | `True` | call `tight_layout()` automatically |
| `style` | `"default"` | any `plt.style` name, a preset, or a custom rcParams dict |

!!! warning
    `style` raw rcParams apply fully on matplotlib/seaborn; bokeh honours background and
    text colour only.

_TODO: example; how `style` interacts with presets._
