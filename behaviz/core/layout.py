"""Backend-agnostic multi-panel layout.

A layout is described as a list of :class:`Placement` — one per panel, giving
its name, top-left cell and span. Both a plain ``nrows x ncols`` grid and a
mosaic string reduce to the same list, so every backend has one code path:
place each panel at ``(row, col)`` spanning ``(rowspan, colspan)``.

Nothing here imports a plotting backend.
"""

from __future__ import annotations

from dataclasses import dataclass

# Cell character meaning "leave this cell empty" in a mosaic.
EMPTY = "."


@dataclass(frozen=True)
class Placement:
    """One panel: its name and the block of grid cells it occupies."""

    name: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1


def plain_grid(nrows: int, ncols: int) -> list[Placement]:
    """Placements for a regular ``nrows x ncols`` grid, one panel per cell.

    Panels are named ``"r{row}c{col}"`` — callers that want positional access
    reshape by ``(row, col)`` rather than using the names.
    """
    if nrows < 1 or ncols < 1:
        raise ValueError(f"Grid must have at least 1 row and 1 column, got {nrows}x{ncols}.")
    return [Placement(f"r{r}c{c}", r, c) for r in range(nrows) for c in range(ncols)]


def _mosaic_rows(mosaic) -> list[list[str]]:
    """Normalise a mosaic to a rectangular list of rows of cell names."""
    if isinstance(mosaic, str):
        rows = [list(line.strip()) for line in mosaic.strip().splitlines()]
    else:
        rows = [list(r) for r in mosaic]
    if not rows or not rows[0]:
        raise ValueError("Mosaic is empty.")
    widths = {len(r) for r in rows}
    if len(widths) != 1:
        raise ValueError(f"Mosaic rows must all be the same width, got widths {sorted(widths)}.")
    return rows


def parse_mosaic(mosaic) -> tuple[list[Placement], int, int]:
    """Parse a mosaic into ``(placements, nrows, ncols)``.

    ``mosaic`` is either a string (one line per row, one character per cell) or
    a list of equal-length sequences. A ``"."`` cell is left empty.

    Each name must occupy a solid rectangle; L-shaped or split regions raise.

    Example
    -------
    >>> placements, nrows, ncols = parse_mosaic("AAB\\nCCB")
    >>> nrows, ncols
    (2, 3)
    """
    rows = _mosaic_rows(mosaic)
    nrows, ncols = len(rows), len(rows[0])

    placements: list[Placement] = []
    for name in dict.fromkeys(ch for row in rows for ch in row if ch != EMPTY):
        cells = [(r, c) for r in range(nrows) for c in range(ncols) if rows[r][c] == name]
        r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
        r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
        rowspan, colspan = r1 - r0 + 1, c1 - c0 + 1
        if len(cells) != rowspan * colspan:
            raise ValueError(
                f"Mosaic panel {name!r} is not a solid rectangle "
                f"(occupies {len(cells)} cells in a {rowspan}x{colspan} block)."
            )
        placements.append(Placement(name, r0, c0, rowspan, colspan))

    if not placements:
        raise ValueError("Mosaic has no panels (every cell is empty).")
    return placements, nrows, ncols


def resolve(nrows=None, ncols=None, mosaic=None) -> tuple[list[Placement], int, int]:
    """Resolve either a plain grid or a mosaic to ``(placements, nrows, ncols)``."""
    if mosaic is not None:
        if nrows is not None or ncols is not None:
            raise ValueError("Pass either nrows/ncols or mosaic, not both.")
        return parse_mosaic(mosaic)
    nrows = 1 if nrows is None else nrows
    ncols = 1 if ncols is None else ncols
    return plain_grid(nrows, ncols), nrows, ncols


def check_ratios(width_ratios, height_ratios, nrows: int, ncols: int) -> None:
    """Validate ratio lengths against the grid shape."""
    if width_ratios is not None and len(width_ratios) != ncols:
        raise ValueError(f"width_ratios must have {ncols} entries (one per column), got {len(width_ratios)}.")
    if height_ratios is not None and len(height_ratios) != nrows:
        raise ValueError(f"height_ratios must have {nrows} entries (one per row), got {len(height_ratios)}.")
