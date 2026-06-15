"""Shared figure-saving helpers for the matplotlib-based backends.

``SeabornRenderer`` is not a subclass of ``MatplotlibRenderer``, so the common
``fig.savefig`` logic lives here as free functions both can call.
"""

from __future__ import annotations

import os

from behaviz.core.errors import BehavizSaveError

# Raster/vector formats matplotlib's Agg/PDF/SVG/PS writers handle.
MPL_FORMATS = frozenset({".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff", ".eps", ".ps"})


def extension(path) -> str:
    """Lower-cased file extension of ``path`` (including the dot)."""
    return os.path.splitext(os.fspath(path))[1].lower()


def save_matplotlib(fig, path, **kwargs) -> str:
    """Write a matplotlib ``Figure`` to ``path``, dispatching on its extension."""
    ext = extension(path)
    if ext in MPL_FORMATS:
        kwargs.setdefault("bbox_inches", "tight")
        fig.savefig(path, **kwargs)
        return os.fspath(path)

    if ext in (".html", ".htm"):
        raise BehavizSaveError(
            "The matplotlib/seaborn backend cannot write HTML. Use a raster or "
            "vector format (.png, .pdf, .svg), or switch to the bokeh backend "
            "for interactive HTML output."
        )

    raise BehavizSaveError(
        f"Unsupported file format '{ext or path}' for the matplotlib/seaborn backend. "
        f"Supported: {', '.join(sorted(MPL_FORMATS))}."
    )
