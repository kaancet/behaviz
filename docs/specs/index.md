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
    title          = "",                 # figure title
    title_fontsize = None,               # None → x.fontsize + 2
    text_color     = None,               # tints labels + title + tick labels
    x              = AxisSpec(),          # x-axis: label, scale, lim, ticks, grid, spines, ticks...
    y              = AxisSpec(),          # y-axis: same fields, independent
    figure         = FigureSpec(),        # figsize, dpi, tight, style, backgrounds, font
    show_legend    = False,
    legend_pos     = LegendPosition.BEST,
    legend_fontsize= None,               # None → backend default
    annotations    = [],                 # text annotations
    post_hook      = None,               # callable(ax, spec) for raw backend access
)
```

- `text_color` — one knob that tints every text element; the essential for dark themes.
- `title_fontsize` / `legend_fontsize` — override the derived sizes.

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

## Comparing backend outputs in these docs

Many examples below show the *same spec* on two backends using **content tabs** — a static
matplotlib image in one tab, a live bokeh figure in the other:

=== "matplotlib"

    ![matplotlib output](../img/example_mpl.png)

=== "bokeh"

    <iframe src="../embeds/example_bokeh.html" width="100%" height="420" style="border:none"></iframe>

Generate the two artefacts from one spec:

```python
import behaviz as bv

bv.set_renderer("matplotlib")
fig, ax = bv.plot_line("t", "v", data=df, spec=spec)
bv.save(fig, "docs/img/example_mpl.png")        # static image for tab 1

bv.set_renderer("bokeh")
fig, ax = bv.plot_line("t", "v", data=df, spec=spec)
bv.save(fig, "docs/embeds/example_bokeh.html")  # standalone HTML for the iframe
```

The bokeh `.html` is fully standalone (it pulls BokehJS from the CDN), so the `<iframe>`
needs no extra page setup. The markdown:

````markdown
=== "matplotlib"

    ![mpl](../img/example_mpl.png)

=== "bokeh"

    <iframe src="../embeds/example_bokeh.html" width="100%" height="420" style="border:none"></iframe>
````
