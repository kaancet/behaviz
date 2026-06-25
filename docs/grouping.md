# Grouping: `hue` & `group`

Turn one plot call into per-category series automatically. Gated on `data=`; `group`/`hue`
are column names.

## Semantics

| Argument | Effect |
| --- | --- |
| `hue=col` | one **distinctly coloured** series per category, **with a legend** |
| `group=col` | one **separate primitive** per category, **same style**, **no legend** (spaghetti) |
| both | one primitive per (group × hue), coloured/labelled by hue |

```python
import numpy as np
import pandas as pl
import behaviz as bv

rng = np.random.default_rng(7)
subjects = [f's{i}' for i in range(6)]
conds = ['control', 'drug A', 'drug B']
t = np.linspace(0, 1, 40)
rows = []
for ci, cond in enumerate(conds):
    for s in subjects:
        base = 0.6 * ci + 0.15 * rng.standard_normal()
        y = np.sin(t * 6) + base + 0.06 * rng.standard_normal(t.size)
        rows += [dict(t=ti, signal=yi, condition=cond, subject=s) for ti, yi in zip(t, y)]
df = pd.DataFrame(rows)

bv.plot_scatter('t', 'signal', data=df, hue='condition')
```

![hue_scatter](/res/hue1.png)

Combined ```hue``` + ```group``` makes sure the dataframe column values are properly colored and seperated.

```python
bv.plot_line('t', 'signal', data=df, group='subject', hue='condition')
```

![hue_scatter](/res/hue_group.png)

## Order & palette

```python
bv.plot_line('t', 'signal', data=df, 
             hue="condition",
             group="subject",
             hue_order=["control", "drug A", "drug B"],
             palette={"control": "#333e3e", "drug A": "#e41a1c", "drug B":"#339811"})
```

![palette](/res/palette.png)

`palette` accepts `None` (auto), a list, or a `{category: color}` dict.

## Overlay vs dodge

- **Overlay** (line/scatter/step/fill_between): series drawn at their original x.
- **Dodge** (bar/errorbar): categories placed side by side.

```python
import matplotlib.pyplot as plt 

bars = pd.DataFrame({
    'cond_idx':  [0, 1, 2, 0, 1, 2],
    'condition': ['control', 'drug A', 'drug B'] * 2,
    'session':   ['pre'] * 3 + ['post'] * 3,
    'score':     [3.1, 5.2, 2.4, 4.0, 1.8, 6.1],
    'sem':       [0.3, 0.4, 0.2, 0.35, 0.25, 0.5],
})

f,ax = plt.subplots(1,2,figsize=(12,6)) # only works with matplotlib backend

bv.plot_bar('cond_idx', 'score', data=bars, 
            ax=ax[0], 
            hue='session', 
            dodge="centered",
            dodge_width=0.4)
bv.plot_bar('cond_idx', 'score', data=bars, 
            ax=ax[1], 
            hue='session', 
            dodge='stacked')
```

![dodge](/res/dodge.png)

## Prefixing legend labels

With `hue=`, legend entries are the category values. Pass `label=` to prepend a prefix
(space-joined):

```python
bv.plot_line("t", "signal", data=df, hue="cond", label="Condition ")
# legend: "Condition ctrl", "Condition drug"
```

## Custom dodge strategies

`dodge=` resolves a strategy from a registry (`"centered"`, `"stacked", "none"`). Register your own —
see [Overriding](overriding.md).

_TODO: expand with full examples and the group-only "why is everything connected" gotcha
(each subject must be sorted/monotonic in x)._
