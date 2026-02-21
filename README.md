# Project 2 - CSP - Tile Placement

Python 3 solver for the tile placement CSP using backtracking search, MRV/LCV heuristics, and AC-3-style domain propagation.

Author: Kamal Ahmadov, Rufat Guliyev, Murad Valiyev

## Requirements

- Python 3.10+
- `pytest` for tests

## Run

```bash
python3 main.py input/tilesproblem_1326658913086500.txt
```

Output format:

- `Solved` or `No solution found`
- If solved, one line per block:
  - `block_id 4 tile_shape rotation`

Example line:

```text
7 4 EL_SHAPE 2
```

The program is command-line only (no GUI), matching project instructions.

## Input Format Supported

The parser supports the required sections:

1. `# Landscape`
2. `# Tiles:` then one dictionary-like line, e.g. `{OUTER_BOUNDARY=6, EL_SHAPE=7, FULL_BLOCK=12}`
3. `# Targets:` then four lines `1:x` .. `4:x`

Notes:

- Landscape must be square, and `N % 4 == 0`.
- Optional `Solution Key` content after targets is ignored by the solver.

## CSP Model

- Variables: one variable `X_b` for each 4x4 block in row-major order.
- Domain values:
  - `(FULL_BLOCK, 0)`
  - `(OUTER_BOUNDARY, 0)`
  - `(EL_SHAPE, rot)` for `rot in {0,1,2,3}`
- Domain filtering by availability:
  - Any shape with inventory `0` is removed from all domains.

### Constraints

- Inventory constraint (global): each shape must be used exactly its available count.
- Visibility target constraint (global): final visible bush counts for colors 1..4 must equal the given targets.

There is one variable per 4x4 block in row-major order, so the solution prints in the same order.

## Search + Inference

- Backtracking search.
- Variable ordering: MRV (`min domain size`), deterministic tie-break by smaller block index.
- Value ordering: LCV approximation using a damage score:
  - how many values in other domains become immediately infeasible,
  - plus a small scarcity penalty for consuming a shape at a tight bound.
- AC-3-style propagation over variables:
  - queue initialized with all variables initially,
  - after assignment/domain reduction, re-enqueue other unassigned variables,
  - `revise(X_i)` removes values that fail global feasibility checks.

Tie-breaking rule:

- MRV ties are broken by lower block index for deterministic output.

## Pruning / Feasibility Checks

For tentative assignment `(b = v)`:

1. Inventory feasibility (no shape overuse).
2. Target overshoot check (`visible_so_far + contrib[b][v] <= target`).
3. Remaining per-color bounds using current domains of unassigned blocks:
   - `min_possible_total[color] <= target[color] <= max_possible_total[color]`
4. Remaining shape-count bounds:
   - required remaining count per shape must fit within lower/upper bounds implied by remaining domains.

Contributions are precomputed:

- `contrib[b][v] = (visible_1, visible_2, visible_3, visible_4)`
- computed from 4x4 masks for `FULL_BLOCK`, `OUTER_BOUNDARY`, and rotated `EL_SHAPE`.

This combination gives much stronger pruning than naive brute force because domains are cut using both visibility and inventory bounds at every step.

## Tests

Run:

```bash
pytest -q
```

Test suite covers:

- tile mask definitions and rotations,
- parser robustness for section headers and optional solution key,
- end-to-end solver validity on a provided sample instance (inventory + exact target checks),
- unsatisfiable-case behavior (`solve()` returns `None`),
- CLI output format checks for required line structure.
