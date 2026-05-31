from behaviz.backends.seaborn.backend import (
    SeabornRenderer,
)

from behaviz.core.renderer_registry import (
    register_renderer,
)

register_renderer(
    "seaborn",
    SeabornRenderer,
)
