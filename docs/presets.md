# Presets

A preset is a saved `PlotSpec` look you load by name. They are the bread and butter of behaviz to create visually consistent plots accross analysis pipelines and backends. Presets reside as JSON files at `~/.behaviz/presets` (need to run behaviz init after installation to create this directory).

An example:

```json
{
  "behaviz_preset_version": 1,
  "title": "Lab figure",
  "x": {
    "label": "Contrast",
    "unit": "%",
    "fontsize": 13,
    "scale": "linear",
    "lim": null,
    "ticks": null,
    "tick_fmt": null,
    "invert": false,
    "spines": [
      "bottom",
      "top",
      "left",
      "right"
    ],
    "grid": true,
    "grid_minor": false
  },
  "y": {
    "label": "Hit rate",
    "unit": "%",
    "fontsize": 13,
    "scale": "linear",
    "lim": null,
    "ticks": null,
    "tick_fmt": null,
    "invert": false,
    "spines": [
      "bottom",
      "top",
      "left",
      "right"
    ],
    "grid": true,
    "grid_minor": false
  },
  "figure": {
    "figsize": [
      10,
      4
    ],
    "dpi": 120,
    "tight": true,
    "style": "default"
  },
  "show_legend": false,
  "legend_pos": "best",
  "annotations": []
}

```

## Built-ins

```python
spec = bv.load_preset("paper")
```

Available built-ins: `default`, `paper`, `poster`, `notebook`, `dark`, `presentation`,
`presentation_dark`, `print`.

!!! note
    `PlotSpec.preset(name)` (the classmethod) and `bv.load_preset(name)` overlap but are not
    identical — the classmethod also accepts `"custom"` with a `style_dict=`.

## Save / list / delete your own

```python
spec = bv.PlotSpec().with_title("Lab style")  # ...craft a look
bv.save_preset(spec, "lab")                    # → ~/.behaviz/presets/lab.json
bv.list_presets()                              # {'lab': 'user', 'paper': 'builtin', ...}
bv.delete_preset("lab")
```

## Share between machines

```python
bv.export_preset("lab", "/path/to/lab.json")   # machine A
bv.import_preset("/path/to/lab.json")          # machine B → installs into local library
```

## Command-line setup

```bash
behaviz init        # create ~/.behaviz home (presets/, examples/)
behaviz list        # list presets
```

_TODO: per-backend behaviour of dark presets; the `~/.behaviz` layout; full CLI from README
§"Saving and loading presets"._
