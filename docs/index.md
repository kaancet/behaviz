![icon](res/favicon.png)
# behaviz

behaviz is a modular scientific plotting library that renders the *same* high-level call
on **matplotlib**, **seaborn**, or **bokeh** without changing your code. You describe
*what* a plot should look like with a declarative spec; behaviz translates it to whichever
backend is active.

```python
import behaviz as bv

fig, ax = bv.plot_line(x, y)        # matplotlib by default
bv.set_renderer("bokeh")
fig, ax = bv.plot_line(x, y)        # same call, interactive bokeh figure
```

## Why behaviz?

- **Backend-agnostic.** Write once, switch renderer with one line. Prototype in
  matplotlib, ship interactive bokeh, never rewrite plotting code.
- **A single styling vocabulary.** Scales, limits, ticks, grids, spines, fonts, legends —
  one `PlotSpec` describes them and every backend honors it.
- **Loud, helpful errors.** A declarative channel layer validates inputs and raises clear
  `BehavizDataError` messages instead of cryptic backend tracebacks.
- **Reach the metal when you need to.** Any native backend property is reachable through
  keyword overrides or a `post_hook`.

## Where to go next

| You want to… | Read |
| --- | --- |
| Install it | [Installation](install.md) |
| Make your first plot | [Quickstart](quickstart.md) |
| Understand the model | [Core concepts](concepts.md) |
| See every plot type | [Plotting overview](plots/index.md) |
| Plot from a DataFrame | [Data input](data.md) |
| One line per category | [Grouping](grouping.md) |
| Style a figure | [The spec system](specs/index.md) |
| Reuse a look | [Presets](presets.md) |
| Full API | [API reference](reference/core.md) |

---

behaviz is GPLv3. Source: [github.com/kaancet/behaviz](https://github.com/kaancet/behaviz).
