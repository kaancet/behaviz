from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlotType:
    name: str
    backend_methods: dict[str, str]

    # Arguments passed to the native matplotlib Axes method when building the
    # artist-kwargs table (post-hoc styling introspection). Defaults to a
    # simple two-point (x, y) call which works for most plot types.
    # Override for types with non-standard signatures (e.g. violinplot needs
    # a list-of-arrays, not two flat arrays).
    mpl_dummy_args: tuple = field(default=([0, 1], [0, 1]))


LINE = PlotType(
    name="line",
    backend_methods={
        "matplotlib": "plot",
        "seaborn": "lineplot",
        "bokeh": "line",
    },
)

SCATTER = PlotType(
    name="scatter",
    backend_methods={
        "matplotlib": "scatter",
        "seaborn": "scatterplot",
        "bokeh": "scatter",
    },
)

BAR = PlotType(
    name="bar",
    backend_methods={
        "matplotlib": "bar",
        "seaborn": "barplot",
        "bokeh": "vbar",
    },
    mpl_dummy_args=([0, 1], [1, 2]),
)

HBAR = PlotType(
    name="hbar",
    backend_methods={
        "matplotlib": "barh",
        "seaborn": "barplot",
        "bokeh": "hbar",
    },
    mpl_dummy_args=([0, 1], [1, 2]),
)

VIOLIN = PlotType(
    name="violin",
    backend_methods={
        "matplotlib": "violinplot",
        "seaborn": "violinplot",
        "bokeh": "patch",
    },
    mpl_dummy_args=([[0, 1], [1, 2]],),
)

ERRORBAR = PlotType(
    name="errorbar",
    backend_methods={
        "matplotlib": "errorbar",
        "seaborn": "errorbar",
        "bokeh": "segment",
    },
)

STEP = PlotType(
    name="step",
    backend_methods={
        "matplotlib": "step",
        "seaborn": "step",
        "bokeh": "step",
    },
)

TEXT = PlotType(
    name="text",
    backend_methods={
        "matplotlib": "text",
        "seaborn": "text",
        "bokeh": "text",
    },
    mpl_dummy_args=(0, 0, ""),
)

VERTICAL = PlotType(
    name="vertical",
    backend_methods={
        "matplotlib": "axvline",
        "seaborn": "axvline",
        "bokeh": "vspan",
    },
)

HORIZONTAL = PlotType(
    name="horizontal",
    backend_methods={
        "matplotlib": "axhline",
        "seaborn": "axhline",
        "bokeh": "hspan",
    },
)

IMAGE = PlotType(
    name="image",
    backend_methods={
        "matplotlib": "imshow",
        "seaborn": "imshow",
        "bokeh": "image",
    },
    mpl_dummy_args=([[0, 1], [1, 2]],),
)

FILL_BETWEEN = PlotType(
    name="fill_between",
    backend_methods={
        "matplotlib": "fill_between",
        "seaborn": "fill_between",
        "bokeh": "varea",
    },
    mpl_dummy_args=([0, 1], [0, 1], [1, 2]),  # x, y1, y2
)

PIE = PlotType(
    name="pie",
    backend_methods={
        "matplotlib": "pie",
        "seaborn": "pie",
        "bokeh": "wedge",
    },
    mpl_dummy_args=([1, 2, 3],),
)

HEXBIN = PlotType(
    name="hexbin",
    backend_methods={
        "matplotlib": "hexbin",
        "seaborn": "hexbin",
        "bokeh": "hex_tile",
    },
    mpl_dummy_args=([0, 1, 2, 3], [0, 1, 2, 3]),
)

SANKEY = PlotType(
    name="sankey",
    backend_methods={
        "matplotlib": "sankey",
        "seaborn": "sankey",
        "bokeh": "sankey",
    },
)

ALLUVIAL = PlotType(
    name="alluvial",
    backend_methods={
        "matplotlib": "alluvial",
        "seaborn": "alluvial",
        "bokeh": "alluvial",
    },
)


ALL_PLOTS = {
    p.name: p
    for p in [
        LINE,
        SCATTER,
        BAR,
        HBAR,
        VIOLIN,
        ERRORBAR,
        STEP,
        TEXT,
        VERTICAL,
        HORIZONTAL,
        IMAGE,
        FILL_BETWEEN,
        PIE,
        HEXBIN,
        SANKEY,
        ALLUVIAL,
    ]
}


def get_plot(plot_name: str, backend: str) -> str:
    return ALL_PLOTS[plot_name].backend_methods[backend]
