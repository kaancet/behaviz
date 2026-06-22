# Presets

!!! note "Stub — to be expanded"

A preset is a saved `PlotSpec` look you load by name.

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
