from behaviz.backends.seaborn.backend import (
    SeabornRenderer,
)

from behaviz.backends.renderer_registry import (
    register_renderer,
)

register_renderer(
    "seaborn",
    SeabornRenderer,
)
