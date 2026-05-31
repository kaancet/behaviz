from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from behaviz.core.renderer import Renderer

_REGISTRY: dict[str, "Renderer"] = {}


def register_renderer(
    name: str,
    renderer_cls: "Renderer",
) -> None:
    _REGISTRY[name] = renderer_cls


def get_renderer_class(
    name: str,
) -> "Renderer":
    try:
        return _REGISTRY[name]
    except KeyError:
        available = sorted(_REGISTRY)

        raise ValueError(f"Unknown renderer '{name}'. Available: {available}")


def make_renderer(
    name: str,
) -> "Renderer":
    renderer_cls = get_renderer_class(name)

    return renderer_cls()


def available_renderers() -> list[str]:
    return sorted(_REGISTRY)
