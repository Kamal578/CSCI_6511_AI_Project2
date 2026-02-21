from collections import Counter
from pathlib import Path

from tileplacement.csp import TilePlacementCSP
from tileplacement.parser import parse_problem
from tileplacement.tiles import mask_for


def _compute_visible_counts(problem, solution):
    n = len(problem.landscape)
    bps = n // 4
    visible = [0, 0, 0, 0]

    for b, value in solution.items():
        br = b // bps
        bc = b % bps
        r0 = br * 4
        c0 = bc * 4

        mask = mask_for(value)
        for r in range(4):
            for c in range(4):
                if not mask[r][c]:
                    color = problem.landscape[r0 + r][c0 + c]
                    if 1 <= color <= 4:
                        visible[color - 1] += 1

    return tuple(visible)


def test_solver_finds_valid_solution_for_sample_instance():
    problem = parse_problem("input/tilesproblem_1326658913086500.txt")
    csp = TilePlacementCSP(problem)
    solution = csp.solve()

    assert solution is not None
    assert len(solution) == csp.num_blocks

    shape_counts = Counter(shape for shape, _ in solution.values())
    assert shape_counts["FULL_BLOCK"] == problem.tiles["FULL_BLOCK"]
    assert shape_counts["OUTER_BOUNDARY"] == problem.tiles["OUTER_BOUNDARY"]
    assert shape_counts["EL_SHAPE"] == problem.tiles["EL_SHAPE"]

    visible = _compute_visible_counts(problem, solution)
    assert visible == (
        problem.targets[1],
        problem.targets[2],
        problem.targets[3],
        problem.targets[4],
    )


def test_solver_returns_none_for_unsatisfiable_instance(tmp_path: Path):
    path = tmp_path / "unsat.txt"
    path.write_text(
        "\n".join(
            [
                "# Landscape",
                "1 1 1 1",
                "1 1 1 1",
                "1 1 1 1",
                "1 1 1 1",
                "",
                "# Tiles:",
                "{FULL_BLOCK=1, OUTER_BOUNDARY=0, EL_SHAPE=0}",
                "",
                "# Targets:",
                "1:1",
                "2:0",
                "3:0",
                "4:0",
            ]
        ),
        encoding="utf-8",
    )

    problem = parse_problem(str(path))
    csp = TilePlacementCSP(problem)
    assert csp.solve() is None
