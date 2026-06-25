# AxisSpec

`spec.x` and `spec.y` are each an `AxisSpec` — **independent**, so the two axes can
differ in scale, ticks, grid, spines, everything below.

```python
import behaviz as bv

spec = bv.PlotSpec(
    x=bv.AxisSpec(label="Time", unit="s", scale="linear"),
    y=bv.AxisSpec(label="Voltage", unit="mV", scale="log"),
)
bv.plot_line("t", "v", data=df, spec=spec)
```

!!! note "Cross-backend"
    Every field below takes effect on matplotlib, seaborn **and** bokeh, except the two
    marked *matplotlib only* (`spine_offset`, `spine_trim`) — bokeh has no spine model —
    and `tick_sides`, which on bokeh can only toggle the primary side (bottom/left).

## Fields

| Field | Default | Meaning |
|---|---|---|
| `label` | `""` | axis label |
| `unit` | `""` | appended automatically → `"Voltage (mV)"` |
| `fontsize` | `12` | label + tick-label font size |
| `scale` | `"linear"` | `linear` / `log` / `symlog` / `logit` |
| `lim` | `None` | `(min, max)` or `None` → auto |
| `ticks` | `None` | explicit tick positions (numbers, or strings → categorical labels) |
| `tick_fmt` | `None` | printf format, e.g. `"%.2f"` |
| `invert` | `False` | flip axis direction |
| `spines` | all four | which spines to draw |
| `spine_width` | `2` | spine line width |
| `spine_color` | `None` | spine colour (`None` → backend default) |
| `spine_offset` | `0` | push spine outward, px — *matplotlib only* |
| `spine_trim` | `False` | clip spine to the outer ticks — *matplotlib only* |
| `tick_dir` | `"out"` | tick direction: `out` / `in` / `inout` |
| `tick_length` | `None` | tick length (`None` → `3 × spine_width`) |
| `tick_width` | `None` | tick line width (`None` → `spine_width`) |
| `tick_color` | `None` | tick colour |
| `tick_sides` | `None` | sides that show tick marks (`["bottom"]`, `["left","right"]`, …) |
| `grid` | `True` | major grid on |
| `grid_minor` | `False` | minor grid on |
| `grid_color` | `"#c1c1c1"` | grid colour |
| `grid_alpha` | `0.5` | grid opacity |
| `grid_style` | `"-"` | major grid linestyle (`-`, `--`, `:`, `-.`) |
| `grid_width` | `0.8` | major grid line width |

## Examples

### Labels, units, font size

```python
bv.AxisSpec(label="Firing rate", unit="Hz", fontsize=16)
```

<!-- image placeholder: examples/specs/axis_labels.png -->

### Scales and limits

```python
spec = bv.PlotSpec(
    x=bv.AxisSpec(lim=(0, 10)),
    y=bv.AxisSpec(scale="log", lim=(1e-2, 1e2)),
)
```

### Categorical ticks

Pass strings to `ticks` — behaviz places them at integer positions automatically.

```python
bv.AxisSpec(ticks=["ctrl", "drug A", "drug B"])
```

### Ticks: direction, length, width, colour

```python
bv.AxisSpec(tick_dir="in", tick_length=8, tick_width=2, tick_color="#444")
```

<!-- image placeholder: examples/specs/axis_ticks.png -->

### Spines: subset, colour, despine offset/trim

```python
# only the left & bottom spines, pushed 8px outward and trimmed to the data
bv.AxisSpec(spines=["left", "bottom"], spine_color="#333",
            spine_offset=8, spine_trim=True)   # offset/trim: matplotlib/seaborn
```

<!-- image placeholder: examples/specs/axis_spines.png -->

### Grid styling

```python
bv.AxisSpec(grid=True, grid_style="--", grid_width=1.0,
            grid_color="#bbbbbb", grid_alpha=0.4, grid_minor=True)
```

### Same call, three backends

A single spec renders the same on every backend:

=== "matplotlib"

    <!-- image placeholder: examples/specs/axis_demo_mpl.png -->
    ![matplotlib output](../img/axis_demo_mpl.png)

=== "bokeh"

    <!-- embed a standalone bokeh HTML (carries its own BokehJS via CDN) -->
    <iframe src="../embeds/axis_demo_bokeh.html" width="100%" height="420" style="border:none"></iframe>

```python
spec = bv.PlotSpec(
    x=bv.AxisSpec(label="t", unit="s", tick_dir="in", grid_style=":"),
    y=bv.AxisSpec(label="signal", spines=["left", "bottom"]),
)
bv.set_renderer("matplotlib"); fig, ax = bv.plot_line("t", "v", data=df, spec=spec)
bv.save(fig, "docs/img/axis_demo_mpl.png")

bv.set_renderer("bokeh");      fig, ax = bv.plot_line("t", "v", data=df, spec=spec)
bv.save(fig, "docs/embeds/axis_demo_bokeh.html")
```
