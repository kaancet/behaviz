# Multi-panel layout

`bv.grid` builds a figure with several panels — on any backend. Everything on
this page works identically on matplotlib, seaborn and bokeh unless the text
says otherwise.

|  | `bv.canvas` | `bv.grid` |
| --- | --- | --- |
| Panels | one | many |
| `ax=` on plot calls | optional (auto-targets the canvas) | **required** |
| Yields | the axes | `axs[row, col]` array, or `axs["A"]` dict with `mosaic=` |

See [Saving & display](saving.md) for `bv.canvas`.

## A regular grid

`nrows`/`ncols` yields a 2-D array indexed `axs[row, col]`.

```python
import numpy as np
import behaviz as bv

x = np.linspace(1, 10, 60)

with bv.grid(2, 2) as axs:
    bv.plot_line(x, x**2, ax=axs[0, 0])
    bv.plot_scatter(x, np.sqrt(x), ax=axs[0, 1])
    bv.plot_line(x, np.sin(x), ax=axs[1, 0])
    bv.plot_scatter(x, np.cos(x), ax=axs[1, 1])
```

!!! warning "`ax=` is required inside a grid"
    A grid has no single default target, so plot calls must say which panel they
    draw into. Omitting `ax=` creates a separate figure instead.

## Spanning panels with a mosaic

A mosaic is ASCII art: one character per cell, one line per row. Repeating a
character makes that panel **span** those cells. With `mosaic=` you get a dict
keyed by panel name instead of an array.

```python
with bv.grid(mosaic="AAB\nCCB", suptitle="mosaic: AAB / CCB",
             wspace=0.35, hspace=0.4) as axs:
    bv.plot_line(x, x**2, ax=axs["A"])
    bv.plot_line(x, np.sin(x), ax=axs["B"])
    bv.plot_scatter(x, np.sqrt(x), ax=axs["C"])
```

![Mosaic layout](res/grid_mosaic.png)

`A` spans the top two columns, `C` the bottom two, and `B` spans both rows on
the right.

A triple-quoted string reads more like the layout it describes:

```python
layout = """
AAA
BCC
BCC
"""

with bv.grid(mosaic=layout) as axs:
    bv.plot_line(x, np.sin(x), ax=axs["A"])       # full-width banner
    bv.plot_scatter(x, np.cos(x), ax=axs["B"])    # tall left panel
    bv.plot_line(x, x**2, ax=axs["C"])            # large 2x2 block
```

Mosaics also accept a list of equal-length sequences, which is handy for names
longer than one character:

```python
bv.grid(mosaic=[["psth", "psth"], ["raster", "tuning"]])
```

### Empty cells

`.` leaves a cell blank — useful for staircase or triangular layouts.

```python
with bv.grid(mosaic="AB\n.C") as axs:
    ...
```

### Rules

Each panel name must occupy a **solid rectangle**, and every row must be the
same width. Both are validated when the block is entered, before any figure is
built:

```python
with bv.grid(mosaic="ABA\nCCC") as axs:    # ValueError: panel 'A' is not a solid rectangle
    ...
with bv.grid(mosaic="AAB\nCC") as axs:     # ValueError: rows must all be the same width
    ...
with bv.grid(nrows=2, mosaic="AB") as axs: # ValueError: pass either nrows/ncols or mosaic
    ...
```

!!! note
    `bv.grid` is a context manager, so these errors surface on `with` entry —
    not when the call is constructed.

## Sizing, spacing and sharing

```python
with bv.grid(2, 2,
             width_ratios=[2, 1], height_ratios=[1, 2],
             wspace=0.3, hspace=0.35,
             sharex=True,
             suptitle="width_ratios=[2,1], height_ratios=[1,2]") as axs:
    ...
```

![Ratios](res/grid_ratios.png)

| Argument | Meaning |
| --- | --- |
| `nrows`, `ncols` | shape of a regular grid (mutually exclusive with `mosaic`) |
| `mosaic` | ASCII layout; yields a `{name: ax}` dict |
| `width_ratios` | relative column widths — one entry per column |
| `height_ratios` | relative row heights — one entry per row |
| `wspace`, `hspace` | gaps between panels |
| `sharex`, `sharey` | link the panel axes |
| `suptitle` | figure-level title |
| `spec` | figure spec (size, dpi, style) for the figure as a whole |
| `layout` | `"tight"` or `"constrained"` — matplotlib/seaborn only |
| `save`, `show` | write and/or display the figure when the block exits |

Ratio lengths are validated against the grid shape, so a wrong count fails
immediately rather than producing a silently skewed figure.

## Per-panel specs

The grid-level `spec` configures the figure. Each panel takes its own `spec=`
on the plot call — no extra machinery.

```python
left  = bv.PlotSpec(title="Linear", x=bv.AxisSpec(label="x"))
right = bv.PlotSpec(title="Log x",  x=bv.AxisSpec(label="x", scale="log"))

with bv.grid(1, 2, spec=bv.PlotSpec(figure=bv.FigureSpec(figsize=(10, 4)))) as axs:
    bv.plot_line(x, x**2, ax=axs[0, 0], spec=left)
    bv.plot_line(x, x**2, ax=axs[0, 1], spec=right)
```

## Backends

The same grid code runs everywhere — only `bv.set_renderer` changes. Spanning,
ratios, spacing and sharing work on all three backends.

```python
for backend in ["matplotlib", "seaborn", "bokeh"]:
    bv.set_renderer(backend)
    ext = "html" if backend == "bokeh" else "png"
    with bv.grid(mosaic="AAB\nCCB", save=f"grid_{backend}.{ext}") as axs:
        bv.plot_line(x, x**2, ax=axs["A"])
```

### Displaying a bokeh grid

The panels you get from `bv.grid` are the individual figures, **not** the layout
that holds them, so `show(axs)` raises `Invalid object to show`. Use `show=True`
and behaviz shows the real layout (calling `output_notebook()` for you in a
notebook):

```python
bv.set_renderer("bokeh")
with bv.grid(mosaic="AAB\nCCB", show=True) as axs:
    bv.plot_line(x, x**2, ax=axs["A"])

bv.set_renderer("matplotlib")   # the renderer is global — set it back
```

`save=` and `show=True` combine safely — saving does not consume the figure.

### Matplotlib-only features

Three features have no bokeh equivalent. Rather than degrade silently, bokeh
raises `NotImplementedError` naming the feature and the alternative.

=== "Layout engine"

    ```python
    with bv.grid(1, 2, layout="constrained") as axs:
        ...
    ```

=== "Inset axes"

    ```python
    # bounds are (x, y, width, height) in parent-axes fractions
    with bv.grid(1, 1) as axs:
        bv.plot_line(x, x**2, ax=axs[0, 0])
        ins = bv.inset(axs[0, 0], (0.6, 0.15, 0.35, 0.3))
        bv.plot_line(x, np.sin(x), ax=ins)
    ```

=== "Shared colorbar"

    ```python
    with bv.grid(1, 2) as axs:
        for c in range(2):
            fig, ax = bv.plot_image(img, ax=axs[0, c])
        bv.shared_colorbar(fig, axs, mappable=ax.images[-1])
    ```

`layout=None` (the default) never raises, so plain bokeh grids are unaffected.

!!! note "Interaction with `FigureSpec.tight`"
    When you set `layout=` or pass explicit ratios/spacing, you own the layout —
    behaviz skips its automatic `tight_layout()` so it cannot override your
    values.

## Example notebook

`examples/canvas_and_grid_example.ipynb` runs every pattern on this page across
all three backends.
