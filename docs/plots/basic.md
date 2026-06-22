# Basic plots

The everyday XY plots. All accept arrays or `data=` column names, an optional `spec=`, and
arbitrary backend [overrides](../overriding.md). All support
[`hue=` / `group=`](../grouping.md).

## Line — `plot_line`

```python
bv.plot_line(x, y)
bv.plot_line("t", "signal", data=df, color="firebrick", linewidth=2)
```

**Channels:** `x` (vector), `y` (vector, same length as `x`).

## Scatter — `plot_scatter`

```python
bv.plot_scatter(x, y, color="k", alpha=0.5)
```

**Channels:** `x` (vector), `y` (vector, same length as `x`).

## Step — `plot_step`

Staircase line. `where` controls where the step happens (`"pre"`, `"post"`, `"mid"`).

```python
bv.plot_step(x, y, where="post")
```

**Channels:** `x` (vector), `y` (vector, same length as `x`).

## Bar — `plot_bar`

```python
bv.plot_bar(x, y, width=0.6)
```

**Signature:** `plot_bar(x, y, width=0.2, bottom=None, ...)`.
**Channels:** `x` (vector), `y` (heights, same length as `x`).

- `bottom=` stacks bars on a baseline (used internally by stacked dodging).
- With `hue=`/`group=`, bars are placed **side by side** (`dodge="centered"`, default) or
  **stacked** (`dodge="stacked"`). See [Grouping](../grouping.md).

## Error bars — `plot_errorbar`

```python
bv.plot_errorbar(x, y, err)

# asymmetric errors: err shape (2, N) → [lower, upper]
bv.plot_errorbar(x, y, np.vstack([lower, upper]))
```

**Signature:** `plot_errorbar(x, y, err, ...)`.
**Channels:** `x` (vector), `y` (vector, same length as `x`), `err` (matches `y`; or `(2, N)`
for asymmetric).

Override the cap/line styling with `capsize=`, `elinewidth=`, `ecolor=`, `capthick=` — these
route correctly on every backend.

## Fill between — `plot_fill_between`

A shaded band between two curves (or a curve and a constant).

```python
bv.plot_fill_between(x, lower, upper, alpha=0.3)
bv.plot_fill_between(x, y, 0)            # band down to zero
```

**Channels:** `x` (vector), `y1` (vector), `y2` (vector or scalar, default `0`).

With multiple categories, bands are **overlaid** (not dodged) — overlapping is the intended
look.
