from __future__ import annotations

"""CLI entry point for Project 2 - CSP Tile Placement.

Author: Kamal Ahmadov, Rufat Guliyev, Murad Valiyev
"""

import argparse

from tileplacement.csp import TilePlacementCSP
from tileplacement.parser import parse_problem


def main() -> int:
    """Parse input, run CSP solver, print required output format."""
    parser = argparse.ArgumentParser(
        description="Project 2 CSP Tile Placement solver")
    parser.add_argument("input_file", help="Path to problem input file")
    args = parser.parse_args()

    problem = parse_problem(args.input_file)
    csp = TilePlacementCSP(problem)
    solution = csp.solve()

    if solution is None:
        print("No solution found")
        return 1

    print("Solved")
    for block_id in range(csp.num_blocks):
        tile_shape, rotation = solution[block_id]
        print(f"{block_id} 4 {tile_shape} {rotation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
