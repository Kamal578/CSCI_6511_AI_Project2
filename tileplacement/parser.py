from __future__ import annotations

"""Input parser for Tile Placement CSP problem files.

Author: Kamal Ahmadov, Rufat Guliyev, Murad Valiyev
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Problem:
    """Parsed input data needed by the solver."""

    landscape: List[List[int]]
    tiles: Dict[str, int]
    targets: Dict[int, int]


_TILE_RE = re.compile(r"([A-Z_]+)\s*=\s*(\d+)")
_TARGET_RE = re.compile(r"([1-4])\s*:\s*(\d+)")


def _parse_landscape_row(line: str) -> List[int]:
    """
    Parse one landscape line.

    Supports both common formats:
    1) "1 2 3 4" style integer tokens.
    2) generator's fixed-width 2-char cells (e.g. "2   1 ..."), where
       blank cell becomes 0.
    """
    stripped = line.strip()
    if not stripped:
        raise ValueError("Landscape row cannot be empty")

    raw = line.rstrip("\n")
    is_fixed_width = len(raw) % 2 == 0 and all(
        raw[i] == " " for i in range(1, len(raw), 2))
    if is_fixed_width:
        width = len(raw) // 2
        row = []
        for j in range(width):
            ch = raw[2 * j]
            row.append(int(ch) if ch.isdigit() else 0)
        return row

    tokens = stripped.split()
    if tokens and all(tok.isdigit() for tok in tokens):
        return [int(tok) for tok in tokens]

    raise ValueError(f"Unsupported landscape row format: {line!r}")


def _extract_section_index(lines: List[str], marker: str) -> int:
    """Return index of a required section header by logical marker name."""
    pattern_map = {
        "landscape": re.compile(r"^#\s*Landscape\s*$"),
        "tiles": re.compile(r"^#\s*Tiles\s*:\s*$"),
        "targets": re.compile(r"^#\s*Targets\s*:\s*$"),
    }
    key = marker.strip().lower()
    if key not in pattern_map:
        raise ValueError(f"Unknown section marker {marker!r}")

    pat = pattern_map[key]
    for i, line in enumerate(lines):
        if pat.match(line.strip()):
            return i
    raise ValueError(f"Missing required section: {marker}")


def parse_problem(path: str) -> Problem:
    """Parse one input file into a Problem object.

    Expected order of sections:
    1) # Landscape
    2) # Tiles:
    3) # Targets:
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    landscape_header = _extract_section_index(lines, "landscape")
    tiles_header = _extract_section_index(lines, "tiles")
    targets_header = _extract_section_index(lines, "targets")

    if not (landscape_header < tiles_header < targets_header):
        raise ValueError(
            "Input sections must appear in order: Landscape, Tiles, Targets")

    # Parse landscape rows between headers.
    landscape: List[List[int]] = []
    for line in lines[landscape_header + 1: tiles_header]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        landscape.append(_parse_landscape_row(line))

    if not landscape:
        raise ValueError("Landscape section is empty")

    n = len(landscape)
    if any(len(row) != len(landscape[0]) for row in landscape):
        raise ValueError("Landscape rows have inconsistent lengths")
    if len(landscape[0]) != n:
        raise ValueError(
            f"Landscape must be square (NxN), got {n}x{len(landscape[0])}")
    if n % 4 != 0:
        raise ValueError(f"Landscape size N must be divisible by 4, got N={n}")

    # Parse tiles dictionary from first non-empty non-comment line after # Tiles.
    tiles_line = None
    for line in lines[tiles_header + 1: targets_header]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        tiles_line = line
        break
    if tiles_line is None:
        raise ValueError("Missing tiles dictionary line")

    tiles: Dict[str, int] = {"FULL_BLOCK": 0,
                             "OUTER_BOUNDARY": 0, "EL_SHAPE": 0}
    for name, count in _TILE_RE.findall(tiles_line):
        if name in tiles:
            tiles[name] = int(count)

    if sum(tiles.values()) == 0:
        raise ValueError(
            f"Could not parse tile counts from line: {tiles_line}")

    # Parse targets lines after # Targets (ignore optional solution section).
    targets: Dict[int, int] = {}
    for line in lines[targets_header + 1:]:
        if line.strip().startswith("#"):
            if "Solution Key" in line:
                break
            continue
        if not line.strip():
            continue
        m = _TARGET_RE.fullmatch(line.strip())
        if m:
            targets[int(m.group(1))] = int(m.group(2))
            if len(targets) == 4:
                break

    if set(targets.keys()) != {1, 2, 3, 4}:
        raise ValueError(
            f"Targets for colors 1..4 are required, got {targets}")

    return Problem(landscape=landscape, tiles=tiles, targets=targets)
