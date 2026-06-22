# Plotting overview

Every plot is a top-level function `bv.plot_<type>(...)` that returns `(fig, ax)`. They all
share the same conventions:

- **Inputs** are numpy arrays, or **column names** when you pass `data=` (see
  [Data input](../data.md)).
- **Styling** comes from an optional `spec=` ([the spec system](../specs/index.md)).
- **Any extra keyword** is an [override](../overriding.md) routed to the backend
  (`color=`, `linewidth=`, `alpha=`, `label=`, …).
- **`hue=` / `group=`** split one call into per-category series ([Grouping](../grouping.md)).

## The full set

| Function | Draws | Page |
|---|---|---|
| `plot_line` | connected line | [Basic](basic.md) |
| `plot_scatter` | markers | [Basic](basic.md) |
| `plot_step` | step / staircase | [Basic](basic.md) |
| `plot_bar` | bars (grouped/stacked) | [Basic](basic.md) |
| `plot_errorbar` | points with error bars | [Basic](basic.md) |
| `plot_fill_between` | shaded band | [Basic](basic.md) |
| `plot_violin` | violin distributions | [Distributions](distribution.md) |
| `plot_hexbin` | 2D density hexbins | [Distributions](distribution.md) |
| `plot_pie` | pie chart | [Distributions](distribution.md) |
| `plot_image` | heatmap / image + colorbar | [2D & images](twod.md) |
| `plot_vertical` | vertical reference lines | [Annotations](annotation.md) |
| `plot_horizontal` | horizontal reference lines | [Annotations](annotation.md) |
| `plot_pval` | significance bracket | [Annotations](annotation.md) |

Higher-level composed figures (raincloud, lollipop, …) live in
[Composite plots](../composite.md).

## Channels: what each plot expects

behaviz validates inputs declaratively. Each plot declares **channels** — named, typed
inputs (e.g. `x` is a vector, `ys` is a list of vectors, `err` must match `y`'s length).
Pass the wrong shape and you get a clear `BehavizDataError` naming the channel and the fix,
not a backend traceback. The required channels for each plot are listed on its page.
