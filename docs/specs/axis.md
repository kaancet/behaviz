# AxisSpec

!!! note "Stub — field tables to be expanded"

`spec.x` and `spec.y` are each an `AxisSpec`.

| Field | Default | Meaning |
|---|---|---|
| `label` | `""` | axis label |
| `unit` | `""` | appended automatically: `"Voltage (mV)"` |
| `fontsize` | `12` | label + tick font size |
| `scale` | `linear` | `linear` / `log` / `symlog` / `logit` |
| `lim` | `None` | `(min, max)` or `None` → auto |
| `ticks` | `None` | explicit tick positions (numbers or string labels) |
| `tick_fmt` | `None` | format string, e.g. `"%.2f"` |
| `invert` | `False` | flip axis direction |
| `spines` | `["bottom","left"]` | which spines to draw |
| `spine_width` | `2` | spine line width |
| `grid` | `True` | major grid on |
| `grid_minor` | `False` | minor grid on |
| `grid_alpha` | `0.5` | grid line opacity |
| `grid_color` | `"#c1c1c1"` | grid line colour |

_TODO: example per field; note tick length/width is NOT a spec field — set via `post_hook`
(see [Overriding](../overriding.md))._
