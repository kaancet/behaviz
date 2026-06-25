# ColorbarSpec

Describes the colorbar attached to `plot_image` and `plot_hexbin`. You rarely build one by
hand — the `colorbar=` argument coerces shortcuts for you:

```python
import behaviz as bv

bv.plot_image(matrix, cmap="magma", colorbar=True)        # default bar
bv.plot_image(matrix, cmap="magma", colorbar="Correlation")  # str → labelled bar
bv.plot_image(matrix, cmap="magma",
              colorbar=bv.ColorbarSpec(label="r", location="bottom", fontsize=14))  # full control
```

`colorbar=` accepts `True` (default bar), a `str` (its label), or a `ColorbarSpec`.

## Fields

| Field | Default | Meaning |
|---|---|---|
| `label` | `""` | colorbar label |
| `location` | `"right"` | `right` / `left` / `top` / `bottom` |
| `ticks` | `None` | explicit tick positions |
| `tick_fmt` | `None` | printf format, e.g. `"%.1f"` |
| `fraction` | `0.046` | bar size as a fraction of the axes (matches axes height by default) |
| `pad` | `None` | gap between axes and bar (`None` → sensible default) |
| `fontsize` | `12` | label + tick-label font size |

## Examples

### Labelled bar on the bottom

```python
bv.plot_image(
    matrix, cmap="viridis",
    colorbar=bv.ColorbarSpec(label="counts", location="bottom", tick_fmt="%d"),
)
```

<!-- image placeholder: examples/specs/colorbar_bottom.png -->

### Explicit ticks

```python
bv.ColorbarSpec(label="z-score", ticks=[-2, -1, 0, 1, 2], fontsize=11)
```

!!! note "matplotlib / seaborn"
    Colorbars are a matplotlib construct; behaviz renders them on the matplotlib and
    seaborn backends. The bokeh backend draws the image itself but does not yet attach a
    behaviz colorbar.
