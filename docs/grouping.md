# Grouping: `group` & `hue`

!!! note "Stub — to be expanded"

Turn one plot call into per-category series automatically. Gated on `data=`; `group`/`hue`
are column names.

## Semantics

| Argument | Effect |
|---|---|
| `hue=col` | one **distinctly coloured** series per category, **with a legend** |
| `group=col` | one **separate primitive** per category, **same style**, **no legend** (spaghetti) |
| both | one primitive per (group × hue), coloured/labelled by hue |

```python
bv.plot_line("t", "signal", data=df, hue="condition")          # colored + legend
bv.plot_line("t", "signal", data=df, group="subject")          # one line per subject
bv.plot_line("t", "signal", data=df, hue="condition", group="subject")
```

## Overlay vs dodge

- **Overlay** (line/scatter/step/fill_between): series drawn at their original x.
- **Dodge** (bar/errorbar): categories placed side by side.

```python
bv.plot_bar("cond", "mean", data=df, hue="drug")               # side-by-side
bv.plot_bar("cond", "mean", data=df, hue="drug", dodge="stacked")
bv.plot_bar("cond", "mean", data=df, hue="drug", dodge_width=0.5)  # tighter/wider spacing
```

## Order & palette

```python
bv.plot_line(..., hue="cond", hue_order=["ctrl", "drug"], palette={"ctrl": "#888", "drug": "#e41a1c"})
```

`palette` accepts `None` (auto), a list, or a `{category: color}` dict.

## Prefixing legend labels

With `hue=`, legend entries are the category values. Pass `label=` to prepend a prefix
(space-joined):

```python
bv.plot_line("t", "signal", data=df, hue="cond", label="Condition ")
# legend: "Condition ctrl", "Condition drug"
```

## Custom dodge strategies

`dodge=` resolves a strategy from a registry (`"centered"`, `"stacked"`). Register your own —
see [Overriding](overriding.md).

_TODO: expand with full examples and the group-only "why is everything connected" gotcha
(each subject must be sorted/monotonic in x)._
