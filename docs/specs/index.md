# The spec system

A **`PlotSpec`** is a plain dataclass describing *what* a plot should look like, independent
of any backend. You pass it as `spec=` and every backend honors the same fields.

```python
spec = bv.PlotSpec(title="My plot")
bv.plot_line(x, y, spec=spec)
```

## Anatomy

```python
PlotSpec(
    title       = "",                 # figure title
    x           = AxisSpec(),         # x-axis: label, scale, lim, ticks, grid, spines...
    y           = AxisSpec(),         # y-axis: same fields
    figure      = FigureSpec(),       # figsize, dpi, tight, style
    show_legend = False,
    legend_pos  = LegendPosition.BEST,
    annotations = [],                 # text annotations
    post_hook   = None,               # callable(ax, spec) for raw backend access
)
```

- [`AxisSpec`](axis.md) — per-axis: `label`, `unit`, `fontsize`, `scale`, `lim`, `ticks`,
  `tick_fmt`, `invert`, `spines`, `spine_width`, `grid`, `grid_minor`, `grid_alpha`,
  `grid_color`.
- [`FigureSpec`](figure.md) — `figsize`, `dpi`, `tight`, `style`.
- [`ColorbarSpec`](colorbar.md) — colorbar for `plot_image`.

## Chainable mutators

Building a spec field-by-field is verbose; the `with_*` methods return a modified copy:

```python
spec = (
    bv.PlotSpec()
    .with_title("Decay")
    .with_xlabel("Time")
    .with_ylabel("Amplitude")
    .with_xlim(0, 10)
    .with_yticks([0, 0.5, 1.0], tick_fmt="%.1f")
    .with_scale("log", axis="y")
    .with_fontsize(14, axis="both")
    .with_size((10, 6))
    .with_annotation(5, 0.5, "midpoint")
    .with_hook(my_styling_fn)
)
```

Available mutators: `with_title`, `with_xlabel`, `with_ylabel`, `with_xlim`, `with_ylim`,
`with_xticks`, `with_yticks`, `with_fontsize`, `with_scale`, `with_size`,
`with_annotation`, `with_hook`.

## Enums

```python
from behaviz import ScaleType, LegendPosition

ScaleType:       linear | log | symlog | logit
LegendPosition:  best | upper right | upper left | lower right | lower left | outside
```

## Cross-backend parity

Every **discrete** `AxisSpec`/`FigureSpec` field — scale, lim, ticks, invert, grid
colour/alpha, spines, spine width, fonts, background/text colour — takes effect on **all
three backends**.

!!! warning "The one exception"
    The `FigureSpec.style` field's raw matplotlib **rcParams** (line widths, marker sizes,
    fonts) apply fully on matplotlib/seaborn. bokeh has no rcParams model, so it honours
    **background and text colour only** from a style.

## Presets

Don't build a spec from scratch every time — load a [preset](../presets.md):

```python
spec = bv.load_preset("paper")          # or "poster", "notebook", "dark", "print"...
```
