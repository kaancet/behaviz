# Composite plots

!!! warning "Experimental — API may change"

Higher-level, composed figures built from the same primitives. They live under
`behaviz.composite_plots` and are imported by submodule (not re-exported at the top level).

Available modules: `boxplot`, `raincloudplot`, `lollipopplot`, `parallelplot`, `hist1dplot`,
plus shared `styling`.

```python
from behaviz.composite_plots import raincloudplot
# ...
```

_TODO: confirm each module's public entrypoint and signature, then document. Note: the
README composite examples currently reference older module names and need updating._
