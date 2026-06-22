# Architecture

!!! note "Stub — for contributors"

behaviz is layered so each piece stays small and testable.

- **`spec/`** — plain dataclasses (`PlotSpec`, `AxisSpec`, `FigureSpec`, `ColorbarSpec`)
  describing *what* a plot looks like, independent of any backend.
- **`core/`** — the public plot functions. Simple `(x, y)` plots are generated from one
  template in `core_factory.py`; richer ones are hand-written. A `plot_function` decorator
  handles figure creation, `data=` resolution, channel validation, grouping, and spec
  application uniformly.
- **`backends/`** — one `Renderer` per backend translating canonical calls to native
  matplotlib / seaborn / bokeh, plus an `Overrider` (kwarg routing) and an opt-in
  `HoverEngine`.
- **The registry** — validates at import that every plot type is implemented across all
  backends, so gaps fail loudly during development.

_TODO: diagram; how to add a new plot type; how to add a backend; pull from README §"How it
works"._
