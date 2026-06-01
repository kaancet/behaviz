from behaviz.backends.matplotlib.backend import (
    MatplotlibRenderer,
)

from behaviz.backends.renderer_registry import (
    register_renderer,
)

register_renderer(
    "matplotlib",
    MatplotlibRenderer,
)
