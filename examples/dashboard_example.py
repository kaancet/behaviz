"""behaviz dashboard starter — a DataTable + 4 linked plots, no abstractions.

Run it:
    panel serve examples/dashboard_example.py --show     # live server
    python examples/dashboard_example.py                 # opens a browser tab

Everything shares ONE data source, so a box/lasso selection in any plot — or a
row click in the table — highlights the same rows everywhere. No callbacks.

Swap the data in STEP 1 and the plots in STEP 4 for your own; the wiring stays.
"""

import numpy as np
import behaviz as bv

# ---------------------------------------------------------------------------
# STEP 1 — your data, as a dict (or a pandas/polars DataFrame).
# One row per observation; columns are what you'll plot. Replace freely.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(0)
n = 300
data = {
    "x": rng.normal(size=n),
    "y": rng.normal(size=n),
    "z": rng.normal(size=n) * 2,
    "w": rng.uniform(0, 10, size=n),
}

# ---------------------------------------------------------------------------
# STEP 2 — wrap the data once. This builds ONE bokeh ColumnDataSource that
# every plot and the table will share. Sharing it is what links selection.
# ---------------------------------------------------------------------------
src = bv.linked(data)

# ---------------------------------------------------------------------------
# STEP 3 — linked brushing only exists on the interactive (bokeh) backend.
# ---------------------------------------------------------------------------
bv.set_renderer("bokeh")

# ---------------------------------------------------------------------------
# STEP 4 — the plots. bv.linked_plot(src, "<kind>", x_col, y_col, ...) draws an
# x/y plot from the shared source so every plot brushes together. Styling kwargs
# (color, size, ...) work exactly as in the normal plot functions. Each returns
# (fig, ax); we keep the figure. Change kind/columns/styling to anything.
# ---------------------------------------------------------------------------
p1, _ = bv.linked_plot(src, "scatter", "x", "y", color="#3366cc", size=6)
p2, _ = bv.linked_plot(src, "scatter", "x", "z", color="#cc3366", size=6)
p3, _ = bv.linked_plot(src, "scatter", "y", "z", color="#33aa55", size=6)
p4, _ = bv.linked_plot(src, "line", "w", "y", color="#9933cc")

# ---------------------------------------------------------------------------
# STEP 5 — the DataTable viewer. It's a plain bokeh DataTable pointed at the
# SAME source (src.cds), so clicking a row selects that observation in the
# plots, and brushing the plots selects rows here. One column per data field.
# ---------------------------------------------------------------------------
from bokeh.models import DataTable, TableColumn

table = DataTable(
    source=src.cds,
    columns=[TableColumn(field=c, title=c) for c in src.columns],
    height=220,
    sizing_mode="stretch_width",
)

# ---------------------------------------------------------------------------
# STEP 6 — arrange everything. `bv.view(...)` wraps a figure so it composes:
#   `|`  puts things in a Row (side by side)
#   `/`  stacks things in a Column
# Here: the table on top, then a 2x2 grid of the four plots underneath.
# ---------------------------------------------------------------------------
plots = (bv.view(p1) | p2) / (bv.view(p3) | p4)   # 2x2 grid
layout = bv.view(table) / plots                   # table above the grid

# ---------------------------------------------------------------------------
# STEP 7 — expose it. `.servable()` lets `panel serve` find it; the __main__
# block lets a plain `python this_file.py` open it in a browser.
# ---------------------------------------------------------------------------
layout.servable()

if __name__ == "__main__":
    layout.show()
