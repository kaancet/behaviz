from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from behaviz.core.renderer import Renderer

_CURRENT_RENDERER: Renderer | None = None


def set_renderer_instance(
    renderer: "Renderer",
):
    global _CURRENT_RENDERER

    _CURRENT_RENDERER = renderer


def get_renderer() -> "Renderer":
    if _CURRENT_RENDERER is None:
        raise RuntimeError("No renderer configured.")

    return _CURRENT_RENDERER
