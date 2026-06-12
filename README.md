# behaviz

A modular, multi-backend plotting library that gets you from **raw data to a clean, clear and reproducible figures - fast**.

![OS](https://img.shields.io/badge/OS-independent-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


## Why behaviz?

Scientific plotting libraries are powerful but can be verbose: you spend more time wrangling
keyword arguments, call signatures, and styling than looking at your data. behaviz is
built for researchers who want **publication-quality plots without becoming matplotlib
experts**.

It aims to solve two problems:

1. **Consistent, reproducible plots for similar data:**  describe a plot once with a
   `spec`, reuse it everywhere.
2. **High-level calls with low-level control:** simple functions like `plot_line` and
   `plot_scatter` that still let you reach any underlying plot property through keyword
   overrides.

The same code can render through **matplotlib**, **seaborn**, or **bokeh**, and you can switch
backends with a single line.

### Highlights

- **One simple call per plot:** `plot_line`, `plot_scatter`, `plot_bar`, `plot_step`, `plot_errorbar`, `plot_violin`, `plot_image`,`plot_fill_between`, `plot_pie`, `plot_hexbin`
- **Three interchangeable backends:** `set_renderer("matplotlib" | "seaborn" | "bokeh")`
- **Painless colorbars:** `plot_image(data, colorbar="label")` — auto-sized, no mappable juggling
- **Plot from anything:** NumPy arrays, **pandas** / **polars** DataFrames, or plain dicts
- **Opt-in hover-tooltips:** (`hover_annotate=True`)
- **Cross-backend styling:** canonical keywords (`color`, `linewidth`, `alpha`, …) that work on every backend
- **Reusable specs & presets:** chainable `.with_*()` helpers, plus `save_preset` / `load_preset` to a personal `~/.behaviz` library
- **Visual data manipulators:** jitter, smoothing, normalising, binning that add visual manipulations without changing the original data

<br>

## Installation

behaviz uses [uv](https://github.com/astral-sh/uv) for dependency management.

**Requirements:** Python ≥ 3.10. Core dependencies (`numpy`, `scipy`, `matplotlib`,
`seaborn`, `bokeh`) are installed automatically. `pandas` / `polars` are **optional** —
behaviz never imports them unless you pass one in.

```bash
# clone and install
git clone https://github.com/kaancet/behaviz.git
cd behaviz

# It's recommended to create a virtual environment
uv venv --python 3.10
source .venv/bin/activate # unix (for windows: .venv/bin/activate )

uv sync
```

Or add it to an existing project:

```bash
uv add git+https://github.com/kaancet/behaviz.git
# or with pip
pip install git+https://github.com/kaancet/behaviz.git
```

Once installed, initialize the `~/.behaviz` preset directory (not necessary but it's convenient for discoverability and manually dropping/editting preset files)

```bash
behaviz init
```

<br>

## Quickstart

```python
import numpy as np
import behaviz as bv

x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

# matplotlib is the default backend, nothing else to set up
fig, ax = bv.plot_line(x, y, color="#349888", linewidth=2, label="sin(x)")
```

![quickstart_example](/res/quickstart.png)

Every plot function returns a `(fig, ax)` tuple, so you can keep customizing with the
native backend objects if you ever need to.

<br>

## Core concepts

### The return contract

| Function | Returns |
|---|---|
| `plot_line`, `plot_scatter`, `plot_bar`, `plot_step`, `plot_errorbar`, `plot_image`,`plot_fill_between`, `plot_pie`, `plot_hexbin` | `(fig, ax)` |
| `plot_violin` | `(fig, ax, vp)`-`vp["bodies"]` holds the violin artists |

When you pass an existing `ax=`, the plot is drawn onto it and the **same** axes is
returned, so you can layer plots:

```python
fig, ax = bv.plot_line(x, np.sin(x), label="sin")
bv.plot_line(x, np.cos(x), ax=ax, label="cos", color="orange")   # same axes
```

![quickstart_example](/res/quickstart2.png)

### Switching backends

```python
bv.set_renderer("matplotlib")   # default
bv.set_renderer("seaborn")      # matplotlib + seaborn themes
bv.set_renderer("bokeh")        # interactive HTML (great for dashboards)
```

The **same plotting code** works on all three. Only the display step differs for bokeh,
which renders to HTML and needs an explicit `show()`:

```python
import behaviz as bv
from bokeh.plotting import show
from bokeh.io import output_notebook

bv.set_renderer("bokeh")
fig, ax = bv.plot_line(x, y)

output_notebook()   # in a Jupyter notebook
show(ax)            # for bokeh, `ax` *is* the figure
```

![quickstart_example](/res/quickstart3.png)

<br>

## The plot functions

```python
import numpy as np
import behaviz as bv

x = np.linspace(0, 10, 60)
y = np.sin(x)
```

### Line

```python
fig, ax = bv.plot_line(x, y, color="steelblue", linewidth=2, label="signal")
```

![quickstart_example](/res/line.png)

### Scatter

```python
fig, ax = bv.plot_scatter(x, y, color="crimson", markersize=40, alpha=0.7)
```

![quickstart_example](/res/scatter.png)

### Bar

```python
heights = np.abs(np.sin(x)) + 0.1
fig, ax = bv.plot_bar(x, heights, width=0.25, color="#349888", edgecolor="#000000")
```

![quickstart_example](/res/bar.png)

### Step

```python
fig, ax = bv.plot_step(x, y, where="post", color="black")
```

![quickstart_example](/res/step.png)

### Error bars

```python
err = np.full_like(y, 0.15)               # symmetric ±err
fig, ax = bv.plot_errorbar(x, y, err, color="navy", capsize=3)

# asymmetric: shape (2, N) → [lower, upper]
err_asym = np.vstack([np.full_like(y, 0.05), np.full_like(y, 0.20)])
fig, ax = bv.plot_errorbar(x, y, err_asym)
```

![quickstart_example](/res/errorbar.png)

### Violin

```python
rng = np.random.default_rng(0)
positions = np.array([1.0, 2.0, 3.0])
distributions = [rng.normal(loc=p, scale=0.5, size=200) for p in positions]

fig, ax, vp = bv.plot_violin(positions, distributions)
```

![quickstart_example](/res/violin.png)

`ys` may be a list of arrays **or** a 2-D array of shape `(n_positions, n_samples)`;
both produce one violin per position.

### Image

Display a 2-D array as a colour-mapped image (heatmap):

```python
data = np.random.default_rng(0).normal(size=(40, 60))
fig, ax = bv.plot_image(data, cmap="magma")
```

![quickstart_example](/res/image.png)

Place it in data coordinates with `extent`, and flip the vertical origin like matplotlib:

```python
fig, ax = bv.plot_image(data, extent=(0, 6, 0, 4), origin="lower", vmin=-2, vmax=2)
```

![quickstart_example](/res/image2.png)

`cmap` means the same thing on every backend — the matplotlib colormap is converted to a
Bokeh palette under the hood — so the image looks identical when you `set_renderer("bokeh")`.

#### Colorbar — no plumbing required

A matplotlib colorbar normally means capturing the mappable and wrestling with sizing.
Here it's one opt-in keyword, and the bar is auto-sized to match the image height:

```python
bv.plot_image(data, colorbar=True)                 # default bar
bv.plot_image(data, colorbar="Firing rate (Hz)")   # a string is the label
```

![quickstart_example](/res/image3.png)

For full control, pass a `ColorbarSpec` — the same call works on every backend:

```python
from behaviz import ColorbarSpec

bv.plot_image(
    data, cmap="viridis",
    colorbar=ColorbarSpec(label="Hz", location="bottom", ticks=[-2, 0, 2], tick_fmt="%.0f"),
)
```

![quickstart_example](/res/image4.png)

> `plot_image` currently handles 2-D scalar arrays; RGB(A) images are on the roadmap.

### Fill between

Shade the band between two curves

```python
x = np.linspace(0, 10, 100)
y = np.sin(x)
sem = 0.2 * np.ones_like(x)

fig, ax = bv.plot_fill_between(x, y - sem, y + sem, color="steelblue", alpha=0.3)
bv.plot_line(x, y, ax=ax, color="navy")          # overlay the mean line
```

![quickstart_example](/res/fillbetween.png)

`y2` defaults to `0` (fill down to the axis). Pass two curves for a ribbon.

### Pie

```python
fig, ax = bv.plot_pie([30, 25, 15, 30], labels=["A", "B", "C", "D"], autopct="%.0f%%")
```

![quickstart_example](/res/pie.png)

(`autopct` is matplotlib/seaborn only; on bokeh the slice labels are drawn inside the wedges.)

### Hexbin

A 2-D histogram of raw point data, binned into hexagons and coloured by count — with the same
opt-in `colorbar`:

```python
rng = np.random.default_rng(0)
px, py = rng.normal(size=4000), rng.normal(size=4000)
fig, ax = bv.plot_hexbin(px, py, gridsize=25, cmap="viridis", colorbar="count")
```

![quickstart_example](/res/hexbin.png)

<br>

## Plotting from DataFrames and dicts

You don't have to unpack your data into arrays. Pass a **pandas** or **polars**
DataFrame (or a plain `dict`) as `data=` and reference columns by name. behaviz stays
dependency-free (it never imports pandas or polars, it just reads the columns you ask
for)

```python
import numpy as np
import polars as pl   # or pandas, both work identically
import behaviz as bv

df = pl.DataFrame({"time": np.linspace(0, 1, 50),
                   "voltage": np.random.rand(50)})

# keyword column names
fig, ax = bv.plot_line(x="time", y="voltage", data=df)

# positional column names work too
fig, ax = bv.plot_scatter("time", "voltage", data=df)

# mix and match: a column name for x, a raw array for y
fig, ax = bv.plot_line(x="time", y=np.random.rand(50), data=df)
```

![quickstart_example](/res/dataframe.png)

The rule is the same one seaborn uses: **when `data` is given, a string means "column
name"; otherwise everything is treated as raw data.** Arrays without `data=` behave
exactly as before.

When a channel comes from a named column and you haven't set a label, behaviz uses the
column name automatically

> Supported data sources: anything that responds to `data["column"]` and yields an
> array: pandas DataFrame, polars DataFrame, or `dict[str, array]`. (Pass an *eager*
> polars frame; call `.collect()` on a `LazyFrame` first.)

<br>

## Hover Tooltips

Turn on interactive value tooltips with a single opt-in keyword. It's **off by default**
and works on every backend.

```python
# custom tooltip labels
fig, ax = bv.plot_line(x, y, hover_annotate=True, hover_labels=("Time (s)", "Voltage"))
```

![quickstart_example](/res/hover.png)

- **bokeh:** adds a native hover tool that snaps to data points (works out of the box).
- **matplotlib / seaborn:** adds a nearest-point annotation. Hover events only fire on
  an *interactive* matplotlib backend, e.g. `%matplotlib widget` in Jupyter or a Qt/Tk
  window. (Under the static Agg backend it's a harmless no-op.)

Hover is available for `plot_line`, `plot_scatter`, `plot_bar`, `plot_step`, and
`plot_errorbar`.

---

## Styling: one vocabulary, every backend

Any extra keyword you pass is forwarded to the active backend. Crucially, behaviz
understands a set of **canonical names** so the same code styles a plot identically
whether you're on matplotlib or bokeh:

```python
# identical call, three backends, same visual result
for backend in ("matplotlib", "seaborn", "bokeh"):
    bv.set_renderer(backend)
    bv.plot_line(x, y, color="purple", linewidth=3, alpha=0.6, label="trace")
```

Common canonical keywords: `color`, `alpha`, `linewidth`, `linestyle`, `marker`,
`markersize` / `size`, `label`. Backend-native names still pass straight through, so
power users lose nothing:

```python
bv.set_renderer("bokeh")
bv.plot_line(x, y, line_color="teal", line_width=4)   # native bokeh names also fine
```

On bokeh, a single `color` even fans out to both `line_color` and `fill_color` for you.

---

## The spec system

A `PlotSpec` captures everything about how a plot looks: axes, scales, ticks, legend,
figure size, annotations, so you can define it once and reuse it across many plots for
a consistent look.

```python
from behaviz import PlotSpec, AxisSpec, FigureSpec, ScaleType, LegendPosition

x = np.array([1,2,3,4,5,6])
y = np.array([10,15,35,60,88,100])/100
err = np.array([5,5,5,10,20,5])/100

spec = PlotSpec(
    title="Response curve",
    x=AxisSpec(label="Contrast", unit="%", scale=ScaleType.LINEAR),
    y=AxisSpec(label="Hit rate", unit="%", grid=True),
    figure=FigureSpec(figsize=(6, 6), dpi=300),
    show_legend=True,
    legend_pos=LegendPosition.UPPER_LEFT,
)

fig, ax = bv.plot_errorbar(x, y, err,spec=spec)
```

![quickstart_example](/res/spec.png)

### Presets

Skip the boilerplate with target-tuned presets:

```python
paper    = PlotSpec.preset("paper")      # small, thin lines, no grid
poster   = PlotSpec.preset("poster")     # large figure, big fonts
notebook = PlotSpec.preset("notebook")   # medium, grid on
dark     = PlotSpec.preset("dark")       # dark background
```

### Shortcuts and chaining

Only care about labels? Use `from_labels`:

```python
spec = PlotSpec.from_labels("Time", "Voltage", xunit="s", yunit="mV")
```

Every spec is immutable, the `.with_*()` helpers return a **new** spec, so they chain
cleanly and never mutate shared defaults:

```python
spec = PlotSpec.from_labels("Contrast", "Hit rate", xunit="%", yunit="%")

spec = (
    spec
    .with_title("Trial 1")
    .with_xlim(0, 10)
    .with_scale("y", "log")
    .with_fontsize(14)
    .with_annotation(6, 1.1, "peak", color="red")
)

fig, ax = bv.plot_errorbar(x, y, err,spec=spec)
```

![quickstart_example](/res/spec2.png)

Available helpers: `with_title`, `with_xlim`, `with_ylim`, `with_xticks`, `with_yticks`,
`with_fontsize`, `with_scale`, `with_size`, `with_annotation`, `with_hook`.

### AxisSpec options

`AxisSpec` controls a single axis: `label`, `unit`, `fontsize`, `scale`
(`linear`/`log`/`symlog`/`logit`), `lim`, `ticks`, `tick_fmt`, `invert`, `spines`,
`grid`, `grid_minor`. The displayed label is `"Label (unit)"` when a unit is set.

<br>

## Saving and loading presets

Build a spec once, save it, and reuse it across every project and session. Presets are
stored as JSON under `~/.behaviz/presets/`, so they travel with your machine, eliminating the need to
copy spec code between notebooks.

```python
import behaviz as bv

# craft a spec you like
my_style = (
    bv.PlotSpec.from_labels("Contrast", "Hit rate", xunit="%", yunit="%")
    .with_title("Lab figure")
    .with_size((10, 4))
    .with_fontsize(13)
)

# save it to ~/.behaviz/presets/lab.json
bv.save_preset("lab", my_style)

# ...later, anywhere...
spec = bv.load_preset("lab")          # returns a full PlotSpec
fig, ax = bv.plot_line(x, y, spec=spec)
```

![quickstart_example](/res/spec3.png)

behaviz ships with **built-in presets** that are always available: `default`, `paper`,
`poster`, `notebook`, `dark`:

```python
fig, ax = bv.plot_scatter(x, y, spec=bv.load_preset("paper"))

# start from a built-in, tweak it, save as your own
custom = bv.load_preset("paper").with_title("My paper figure")
bv.save_preset("my_paper", custom)
```

Manage your library:

```python
bv.list_presets()      # {'default': 'builtin', ..., 'lab': 'user'}
bv.delete_preset("lab")  # removes a user preset (built-ins can't be deleted)
bv.presets_dir()       # the storage directory (Path)
```

### Sharing presets between machines

Presets live in your home directory, but you can export one to a standalone file to email,
commit to a repo, or copy to another machine and import it on the other side:

```python
# on machine A: write the preset out to any path
bv.export_preset("lab", "shared/lab.json")

# on machine B: install it into the local ~/.behaviz library
bv.import_preset("shared/lab.json")          # now loadable as "lab"
bv.import_preset("shared/lab.json", name="lab_from_alice")   # or under a new name

spec = bv.load_preset("lab")
```

`export_preset` works for built-ins too (handy for starting points), and `import_preset`
validates the file is a real behaviz preset before installing it.

### Command-line setup

behaviz installs a small `behaviz` CLI for managing the preset library from the shell:

```bash
behaviz init     # scaffold ~/.behaviz: presets/, a README, and example presets
behaviz list     # list available presets (builtin / user)
behaviz where    # print the presets directory path
```

`behaviz init` is **optional**! Built-in presets load and shared presets import without
any setup. What `init` adds is discoverability: a `presets/` folder to drop JSON into, and
an `examples/` folder containing the built-ins as editable JSON starting points. Those
examples are *reference copies only* (not on the load path), so copying one into `presets/`
and editing it never shadows or freezes the real built-in. Use `behaviz init --no-examples`
to skip them.

> Storage honors `BEHAVIZ_HOME`, so `BEHAVIZ_HOME=/path/to/shared behaviz init` sets up a
> shared or version-controlled preset library.

**Good to know**

- A user preset with the same name as a built-in **shadows** it so you can customize
  `paper` without losing the original.
- The storage location is `~/.behaviz` by default, or whatever you point the
  `BEHAVIZ_HOME` environment variable at (handy for shared or version-controlled configs).  

<br>

## Visual data manipulators

Sometimes you need to *visually* tweak data like jittering overlapping points, smooth a noisy
trace, normalise to a baseline, etc., without altering the underlying values. The
`VisualManipulator` does exactly that and **guarantees your originals are never
mutated** (inputs are copied and results are returned read-only).

```python
import numpy as np
import behaviz as bv
from behaviz.manipulations import VisualManipulator

x = np.arange(0, 5 * np.pi, 0.1)
y = np.sin(x)

vm = VisualManipulator(seed=42)          # seed → reproducible jitter

# jitter
jittered = vm.jitter(x, y, kind="uniform", axis="y", strength=0.2)
bv.plot_scatter(jittered.x, jittered.y, label="jittered")

# smoothing, normalising, binning all share the same shape
smoothed   = vm.smooth(x, y, kind="gaussian", sigma=2.0)
normalised = vm.normalise(x, y, kind="zscore", axis="y")
binned     = vm.binning(x, y, bins=20, kind="mean", axis="x")
```

Each call returns a `ManipulationResult` exposing `.x`, `.y`, the untouched `.x_original`
/ `.y_original`, and a `.metadata` dict:

```python
print(jittered.metadata)   # {'kind': 'uniform', 'axis': 'y', 'strength': 0.2, ...}
```

![quickstart_example](/res/jittered.png)

Strategies available out of the box:

| Manipulation | `kind=` options |
| --- | --- |
| `jitter` | `uniform`, `normal`, `beeswarm` |
| `smooth` | `boxcar`, `gaussian` |
| `normalise` | `minmax`, `zscore`, `baseline` |
| `binning` | `mean`, `median`, `sum`, `count` |

Add your own with `VisualManipulator.register_strategy(...)`.

## composite plots

Higher-level, composed figures live in `behaviz.composite_plots` and are built from the
same primitives:

```python
from behaviz.composite_plots.rainplot import plot_rain
from behaviz.composite_plots.psychometric import plot_psychometric
from behaviz.composite_plots.distribution import plot_distribution
from behaviz.composite_plots.impact import plot_impact

fig, ax = plot_rain(positions, distributions, with_cloud=True)
```

These are evolving, so expect their API to firm up (or disappear) over time.

## How it works (architecture)

behaviz is intentionally layered so each piece stays small and testable:

- **`spec/`:** plain dataclasses (`PlotSpec`, `AxisSpec`, `FigureSpec`) describing *what*
  a plot should look like, independent of any backend.
- **`core/`:** the public plot functions. The simple `(x, y)` ones (`plot_line`,
  `plot_scatter`, `plot_step`) are generated from a single template in `core_factory.py`;
  richer ones are hand-written. A decorator (`plot_function`) handles figure creation,
  `data=` resolution, and spec application uniformly.
- **`backends/`:** one `Renderer` per backend translating canonical calls into native
  matplotlib / seaborn / bokeh, plus an `Overrider` that routes keyword arguments and an
  opt-in `HoverEngine`.
- **A registry:** validates at import that every plot type is fully implemented across all
  backends so that the gaps fail loudly during development, not at call time.

This is what lets the *same* call render on three backends and lets you reach any
low-level property through a single high-level function.

## Roadmap

- Unified `bv.save()` / `bv.show()` across backends
- `group=` / `hue=` for automatic per-category series, colors, and legends
- Bokeh-based dashboard layouts
- More composite plots and a documented gallery
- RGB(A) images (`plot_image` currently handles 2-D scalar arrays)
