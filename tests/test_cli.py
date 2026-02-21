import subprocess
import sys


def test_cli_prints_required_format_for_sample_problem():
    proc = subprocess.run(
        [sys.executable, "main.py", "input/tilesproblem_1326658913086500.txt"],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    assert lines
    assert lines[0] == "Solved"

    # 20x20 landscape => (20/4)^2 = 25 block lines.
    assert len(lines[1:]) == 25

    for idx, line in enumerate(lines[1:]):
        parts = line.split()
        assert len(parts) == 4
        assert int(parts[0]) == idx
        assert parts[1] == "4"
        assert parts[2] in {"FULL_BLOCK", "OUTER_BOUNDARY", "EL_SHAPE"}
        rot = int(parts[3])
        if parts[2] in {"FULL_BLOCK", "OUTER_BOUNDARY"}:
            assert rot == 0
        else:
            assert rot in {0, 1, 2, 3}
