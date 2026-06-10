from __future__ import annotations


def validate_registry() -> None:
    """Run all completeness checks. Raises RuntimeError if anything is missing."""
    errors: list[str] = []

    errors.extend(_check_renderer_abc())
    errors.extend(_check_concrete_backends())
    errors.extend(_check_overriders())

    if errors:
        msg = "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(f"behaviz registry is incomplete — fix these before importing:\n{msg}")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def _check_renderer_abc() -> list[str]:
    """Every ALL_PLOTS name must exist as a method on the Renderer ABC."""
    from behaviz.core.plot_registry import ALL_PLOTS
    from behaviz.backends.renderer import Renderer

    errors = []
    for name in ALL_PLOTS:
        if not hasattr(Renderer, name):
            errors.append(
                f"Renderer ABC is missing abstract method '{name}' "
                f"(registered in ALL_PLOTS but not declared on Renderer)"
            )
    return errors


def _check_concrete_backends() -> list[str]:
    """Every concrete Renderer subclass must implement all ALL_PLOTS methods."""
    from behaviz.core.plot_registry import ALL_PLOTS
    from behaviz.backends.renderer import Renderer

    errors = []
    for backend_cls in _all_concrete_subclasses(Renderer):
        for name in ALL_PLOTS:
            if not callable(getattr(backend_cls, name, None)):
                errors.append(f"{backend_cls.__name__} is missing method '{name}' (registered in ALL_PLOTS)")
    return errors


def _check_overriders() -> list[str]:
    """Every concrete Overrider subclass's VALID_CALL_KWARGS must cover all ALL_PLOTS names."""
    from behaviz.core.plot_registry import ALL_PLOTS
    from behaviz.backends.override import Overrider

    errors = []
    for overrider_cls in _all_concrete_subclasses(Overrider):
        covered = set(overrider_cls.VALID_CALL_KWARGS.keys())
        for name in ALL_PLOTS:
            if name not in covered:
                errors.append(f"{overrider_cls.__name__}.VALID_CALL_KWARGS is missing entry for plot type '{name}'")
    return errors


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _all_concrete_subclasses(base: type) -> list[type]:
    """Recursively collect all non-abstract subclasses of *base*."""
    import inspect

    result = []
    for cls in base.__subclasses__():
        if not inspect.isabstract(cls):
            result.append(cls)
        result.extend(_all_concrete_subclasses(cls))
    return result
