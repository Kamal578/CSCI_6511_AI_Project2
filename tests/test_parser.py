from pathlib import Path

from tileplacement.parser import parse_problem


def test_parse_problem_ignores_tiles_problem_header_and_solution_key():
    p = parse_problem("input/tilesproblem_1326658913086500.txt")
    assert len(p.landscape) == 20
    assert len(p.landscape[0]) == 20
    assert p.tiles == {"FULL_BLOCK": 12, "OUTER_BOUNDARY": 6, "EL_SHAPE": 7}
    assert set(p.targets.keys()) == {1, 2, 3, 4}


def test_parse_problem_with_minimal_4x4_case(tmp_path: Path):
    path = tmp_path / "mini.txt"
    path.write_text(
        "\n".join(
            [
                "# Tiles Problem, generated at: x",
                "# Landscape",
                "1 2 3 4",
                "4 3 2 1",
                "1 1 2 2",
                "3 3 4 4",
                "",
                "# Tiles: ",
                "{ FULL_BLOCK = 1, OUTER_BOUNDARY=0, EL_SHAPE=0 }",
                "",
                "# Targets: ",
                "1:0",
                "2:0",
                "3:0",
                "4:0",
                "",
                "# Tiles Problem Solution Key, generated at: y",
                "# Tiles:",
                "0 4 FULL_BLOCK",
            ]
        ),
        encoding="utf-8",
    )

    p = parse_problem(str(path))
    assert len(p.landscape) == 4
    assert p.tiles["FULL_BLOCK"] == 1
    assert p.tiles["OUTER_BOUNDARY"] == 0
    assert p.tiles["EL_SHAPE"] == 0
    assert p.targets == {1: 0, 2: 0, 3: 0, 4: 0}
