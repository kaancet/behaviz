### CONTINUE : MULTI LEVEL SANKEY
import numpy as np
from bokeh.models import Label, HoverTool, ColumnDataSource, CustomJS, Div, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.layouts import column


def create_alluvial(
    flows_data,
    time_points,
    categories,
    colors=None,
    title="Alluvial Diagram",
    width=1500,
    height=800,
    node_width=0.12,
    gap=2,
    flow_alpha=0.5,
    interactive=True,
):
    """
    Create an interactive Alluvial (multi-level Sankey) diagram.

    Parameters:
    -----------
    flows_data : list of list of tuples
        Each inner list represents flows between consecutive time points.
        Each tuple: (from_category, to_category, value)
        Example: [[("A", "B", 10), ("A", "C", 5)], [("B", "C", 8), ...]]
    time_points : list of str
        Labels for each time point
    categories : list of str
        All unique categories across time points
    colors : dict, optional
        Color mapping for categories {category: hex_color}
    title : str
        Plot title
    width : int
        Plot width in pixels
    height : int
        Plot height in pixels
    node_width : float
        Width of nodes
    gap : float
        Gap between nodes as percentage of total height (0-100)
    flow_alpha : float
        Transparency of flows
    interactive : bool
        Enable hover interactions

    Returns:
    --------
    bokeh.layouts.Layout or bokeh.plotting.figure
        Alluvial diagram
    """

    # Auto-generate colors if not provided
    if colors is None:
        default_palette = [
            "#306998",
            "#D62728",
            "#FFD43B",
            "#7F7F7F",
            "#2ECC71",
            "#3498DB",
            "#E67E22",
            "#9B59B6",
            "#1ABC9C",
            "#F39C12",
        ]
        colors = {cat: default_palette[i % len(default_palette)] for i, cat in enumerate(categories)}

    # Calculate node heights at each time point (in flow units)
    node_heights = []
    for t_idx in range(len(time_points)):
        heights = {}
        if t_idx == 0:
            # First time point: sum outgoing flows
            for cat in categories:
                heights[cat] = sum(f[2] for f in flows_data[0] if f[0] == cat)
        elif t_idx == len(time_points) - 1:
            # Last time point: sum incoming flows
            for cat in categories:
                heights[cat] = sum(f[2] for f in flows_data[-1] if f[1] == cat)
        else:
            # Middle time points: sum incoming flows from previous
            for cat in categories:
                heights[cat] = sum(f[2] for f in flows_data[t_idx - 1] if f[1] == cat)
        node_heights.append(heights)

    # Find max total flow at any time point
    max_total_flow = 0
    for t_idx in range(len(time_points)):
        total = sum(node_heights[t_idx].get(cat, 0) for cat in categories)
        max_total_flow = max(max_total_flow, total)

    # Count active categories at each time point for gap calculation
    num_active_categories = []
    for t_idx in range(len(time_points)):
        count = sum(1 for cat in categories if node_heights[t_idx].get(cat, 0) > 0)
        num_active_categories.append(count)

    max_active = max(num_active_categories)

    # Target y-range is 70% of figure height
    target_y_range = height * 0.7

    # Calculate gap size in scaled units
    # gap parameter is percentage, convert to actual units
    gap_size = target_y_range * (gap / 100.0)
    total_gap = gap_size * (max_active - 1) if max_active > 1 else 0

    # Available space for nodes
    available_for_nodes = target_y_range - total_gap

    # Scale factor converts flow units to display units
    scale_factor = available_for_nodes / max_total_flow if max_total_flow > 0 else 1

    # Calculate x positions evenly spaced
    x_positions = list(range(len(time_points)))

    # Calculate node positions in scaled coordinates
    node_positions = []
    max_y = 0
    for t_idx in range(len(time_points)):
        positions = {}
        y_cursor = 0
        for cat in categories:
            height_flow = node_heights[t_idx].get(cat, 0)
            height_scaled = height_flow * scale_factor
            positions[cat] = {
                "y_start": y_cursor,
                "y_end": y_cursor + height_scaled,
                "value": height_flow,  # Store original value
            }
            if height_scaled > 0:
                y_cursor += height_scaled + gap_size
            else:
                y_cursor += 0
        node_positions.append(positions)
        max_y = max(max_y, y_cursor)

    # Create figure with proper ranges
    x_margin = 1
    y_margin = max_y * 0.15

    p = figure(
        width=width,
        height=height,
        title=title,
        x_range=(-x_margin, len(time_points) - 1 + x_margin),
        y_range=(-y_margin, max_y + y_margin),
        tools="",
        toolbar_location=None,
    )

    # Style
    p.title.text_font_size = "20pt"
    p.title.align = "center"
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.outline_line_color = None
    p.background_fill_color = "#FAFAFA"

    # Store ribbon data for interactivity
    ribbon_renderers = []
    ribbon_sources = []

    # Draw flows between consecutive time points
    n_points = 100
    t_param = np.linspace(0, 1, n_points)

    for t_idx, flows in enumerate(flows_data):
        x_start = x_positions[t_idx] + node_width / 2
        x_end = x_positions[t_idx + 1] - node_width / 2

        # Track current position for stacking
        source_cursors = {cat: node_positions[t_idx][cat]["y_start"] for cat in categories}
        target_cursors = {cat: node_positions[t_idx + 1][cat]["y_start"] for cat in categories}

        for from_cat, to_cat, value in flows:
            if value == 0:
                continue

            # Scale the value for visual display
            scaled_value = value * scale_factor

            # Source coordinates
            y_src_bottom = source_cursors[from_cat]
            y_src_top = y_src_bottom + scaled_value
            source_cursors[from_cat] = y_src_top

            # Target coordinates
            y_tgt_bottom = target_cursors[to_cat]
            y_tgt_top = y_tgt_bottom + scaled_value
            target_cursors[to_cat] = y_tgt_top

            # Bezier control points
            cx0 = x_start + (x_end - x_start) / 3
            cx1 = x_start + 2 * (x_end - x_start) / 3

            # Top edge bezier
            x_top = (
                (1 - t_param) ** 3 * x_start
                + 3 * (1 - t_param) ** 2 * t_param * cx0
                + 3 * (1 - t_param) * t_param**2 * cx1
                + t_param**3 * x_end
            )
            y_top = (
                (1 - t_param) ** 3 * y_src_top
                + 3 * (1 - t_param) ** 2 * t_param * y_src_top
                + 3 * (1 - t_param) * t_param**2 * y_tgt_top
                + t_param**3 * y_tgt_top
            )

            # Bottom edge bezier
            x_bottom = (
                (1 - t_param) ** 3 * x_start
                + 3 * (1 - t_param) ** 2 * t_param * cx0
                + 3 * (1 - t_param) * t_param**2 * cx1
                + t_param**3 * x_end
            )
            y_bottom = (
                (1 - t_param) ** 3 * y_src_bottom
                + 3 * (1 - t_param) ** 2 * t_param * y_src_bottom
                + 3 * (1 - t_param) * t_param**2 * y_tgt_bottom
                + t_param**3 * y_tgt_bottom
            )

            # Create closed polygon
            xs = list(x_top) + list(x_bottom[::-1])
            ys = list(y_top) + list(y_bottom[::-1])

            # Create data source (store ORIGINAL value for display)
            source_data = ColumnDataSource(
                data={
                    "x": [xs],
                    "y": [ys],
                    "from": [from_cat],
                    "to": [to_cat],
                    "value": [value],  # Original unscaled value
                    "time_from": [time_points[t_idx]],
                    "time_to": [time_points[t_idx + 1]],
                    "alpha": [flow_alpha],
                }
            )

            ribbon = p.patches(
                "x",
                "y",
                source=source_data,
                fill_color=colors[from_cat],
                fill_alpha="alpha",
                line_color=colors[from_cat],
                line_alpha="alpha",
                line_width=0.5,
            )

            ribbon_renderers.append(ribbon)
            ribbon_sources.append(source_data)

    # Draw nodes and collect for legend
    legend_renderers = {}
    node_renderers = []
    node_sources = []

    for t_idx in range(len(time_points)):
        x = x_positions[t_idx]
        for cat in categories:
            y_start = node_positions[t_idx][cat]["y_start"]
            y_end = node_positions[t_idx][cat]["y_end"]
            value_original = node_positions[t_idx][cat]["value"]

            if y_end > y_start:
                node_source = ColumnDataSource(
                    data={
                        "left": [x - node_width / 2],
                        "right": [x + node_width / 2],
                        "bottom": [y_start],
                        "top": [y_end],
                        "category": [cat],
                        "time_idx": [t_idx],
                        "value": [value_original],  # Store original value
                    }
                )

                renderer = p.quad(
                    left="left",
                    right="right",
                    bottom="bottom",
                    top="top",
                    source=node_source,
                    fill_color=colors[cat],
                    fill_alpha=0.9,
                    line_color="white",
                    line_width=2,
                    hover_fill_alpha=1.0,
                )

                node_renderers.append(renderer)
                node_sources.append(node_source)

                # Collect for legend (one per category)
                if cat not in legend_renderers:
                    legend_renderers[cat] = renderer

                # Add labels on first and last time points (with original values)
                if t_idx == 0:
                    label = Label(
                        x=x - node_width / 2 - 0.03,
                        y=(y_start + y_end) / 2,
                        text=f"{cat} ({int(value_original)})",
                        text_font_size="11pt",
                        text_baseline="middle",
                        text_align="right",
                        text_color="#333333",
                    )
                    p.add_layout(label)
                elif t_idx == len(time_points) - 1:
                    label = Label(
                        x=x + node_width / 2 + 0.03,
                        y=(y_start + y_end) / 2,
                        text=f"{cat} ({int(value_original)})",
                        text_font_size="11pt",
                        text_baseline="middle",
                        text_color="#333333",
                    )
                    p.add_layout(label)

    # Add time point labels
    for t_idx, t in enumerate(time_points):
        label = Label(
            x=x_positions[t_idx],
            y=-y_margin * 0.5,
            text=t,
            text_font_size="14pt",
            text_align="center",
            text_baseline="top",
            text_color="#333333",
            text_font_style="bold",
        )
        p.add_layout(label)

    # Create legend on the right
    legend_items = [
        LegendItem(label=cat, renderers=[legend_renderers[cat]]) for cat in categories if cat in legend_renderers
    ]
    legend = Legend(
        items=legend_items,
        location="center",
        label_text_font_size="11pt",
        glyph_width=20,
        glyph_height=20,
        spacing=8,
        padding=12,
        background_fill_alpha=0.9,
        background_fill_color="white",
        border_line_color="#cccccc",
    )
    p.add_layout(legend, "right")

    if not interactive:
        return p

    # Add interactivity
    info_div = Div(
        text="""
        <div style="padding:12px;border:2px solid #333;border-radius:6px;
                    background:#FFF8DC;font-family:Arial;font-size:13px;color:#333;">
            <b>Hover over flows or nodes</b>
        </div>
        """,
        width=280,
        margin=(10, 10, 10, 10),
    )

    # Ribbon hover
    ribbon_hover = HoverTool(
        renderers=ribbon_renderers,
        tooltips=None,
        callback=CustomJS(
            args=dict(ribbons=ribbon_sources, div=info_div),
            code="""
            const i = cb_data.index.indices[0];
            if (i == null) return;
            const r = cb_data.renderer.data_source;
            
            for (let k = 0; k < ribbons.length; k++) {
                ribbons[k].data.alpha = [0.05];
                ribbons[k].change.emit();
            }
            
            r.data.alpha = [0.85];
            r.change.emit();
            
            div.text = `
            <div style="padding:12px;border:2px solid #333;border-radius:6px;background:#FFF8DC;color:#333;">
                <b>Flow: ${r.data.time_from[0]} → ${r.data.time_to[0]}</b><br><br>
                <b>From:</b> ${r.data.from[0]}<br>
                <b>To:</b> ${r.data.to[0]}<br>
                <b>Value:</b> ${r.data.value[0]}
            </div>`;
            """,
        ),
    )
    p.add_tools(ribbon_hover)

    # Node hover
    node_hover = HoverTool(
        renderers=node_renderers,
        tooltips=None,
        callback=CustomJS(
            args=dict(ribbons=ribbon_sources, div=info_div, time_points=time_points),
            code="""
            const i = cb_data.index.indices[0];
            if (i == null) return;
            const node = cb_data.renderer.data_source.data;
            const cat = node.category[i];
            const t_idx = node.time_idx[i];
            
            let highlighted = 0;
            for (let k = 0; k < ribbons.length; k++) {
                const r = ribbons[k].data;
                if (r.from[0] === cat || r.to[0] === cat) {
                    ribbons[k].data.alpha = [0.75];
                    highlighted++;
                } else {
                    ribbons[k].data.alpha = [0.05];
                }
                ribbons[k].change.emit();
            }
            
            div.text = `
            <div style="padding:12px;border:2px solid #333;border-radius:6px;background:#FFF8DC;color:#333;">
                <b>${cat}</b> at <b>${time_points[t_idx]}</b><br><br>
                <b>Value:</b> ${node.value[i]}<br>
                <b>Connected flows:</b> ${highlighted}
            </div>`;
            """,
        ),
    )
    p.add_tools(node_hover)

    # Reset on mouse leave
    p.js_on_event(
        "mouseleave",
        CustomJS(
            args=dict(ribbons=ribbon_sources, div=info_div, base_alpha=flow_alpha),
            code="""
        for (let k = 0; k < ribbons.length; k++) {
            ribbons[k].data.alpha = [base_alpha];
            ribbons[k].change.emit();
        }
        div.text = `<div style="padding:12px;border:2px solid #333;border-radius:6px;
                     background:#FFF8DC;color:#333;"><b>Hover over flows or nodes</b></div>`;
        """,
        ),
    )

    return column(p, info_div)
