"""Tile value domain and 4x4 coverage masks.

Author: Kamal Ahmadov, Rufat Guliyev, Murad Valiyev
"""

from typing import List, Tuple

TileValue = Tuple[str, int]  # (tile_shape, rotation)


def mask_full() -> List[List[bool]]:
    """FULL_BLOCK: cover all cells in the 4x4 patch."""
    return [[True] * 4 for _ in range(4)]


def mask_outer_boundary() -> List[List[bool]]:
    """OUTER_BOUNDARY: cover the perimeter, leave the inner 2x2 visible."""
    m = [[False] * 4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            if r in (0, 3) or c in (0, 3):
                m[r][c] = True
    return m


def mask_el(rot: int) -> List[List[bool]]:
    """EL_SHAPE mask by rotation.

    Rotation convention:
    0 -> top row + left column
    1 -> top row + right column
    2 -> bottom row + right column
    3 -> bottom row + left column
    """
    m = [[False] * 4 for _ in range(4)]
    if rot == 0:
        for c in range(4):
            m[0][c] = True
        for r in range(4):
            m[r][0] = True
    elif rot == 1:
        for c in range(4):
            m[0][c] = True
        for r in range(4):
            m[r][3] = True
    elif rot == 2:
        for c in range(4):
            m[3][c] = True
        for r in range(4):
            m[r][3] = True
    elif rot == 3:
        for c in range(4):
            m[3][c] = True
        for r in range(4):
            m[r][0] = True
    else:
        raise ValueError("rot must be 0..3")
    return m


def all_values() -> List[TileValue]:
    """Return complete domain before inventory-based filtering."""
    vals = [("FULL_BLOCK", 0), ("OUTER_BOUNDARY", 0)]
    vals += [("EL_SHAPE", r) for r in range(4)]
    return vals


def mask_for(value: TileValue) -> List[List[bool]]:
    """Return 4x4 coverage mask for one domain value."""
    t, r = value
    if t == "FULL_BLOCK":
        return mask_full()
    if t == "OUTER_BOUNDARY":
        return mask_outer_boundary()
    if t == "EL_SHAPE":
        return mask_el(r)
    raise ValueError(f"Unknown tile type {t}")
