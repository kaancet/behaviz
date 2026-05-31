from behaviz.backends.bokeh.backend import (
    BokehRenderer,
)

from behaviz.core.renderer_registry import (
    register_renderer,
)

register_renderer(
    "bokeh",
    BokehRenderer,
)
