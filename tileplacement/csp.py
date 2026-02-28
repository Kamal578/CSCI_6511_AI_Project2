from __future__ import annotations

"""CSP solver for the Tile Placement project.

Author: Kamal Ahmadov, Rufat Guliyev, Murad Valiyev
"""

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .parser import Problem
from .tiles import TileValue, all_values, mask_for

Vec4 = Tuple[int, int, int, int]
SHAPES = ("FULL_BLOCK", "OUTER_BOUNDARY", "EL_SHAPE")


def addv(a: Vec4, b: Vec4) -> Vec4:
    """Return element-wise sum of 4D vectors."""
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3])


@dataclass
class State:
    """Mutable search state used by backtracking + propagation."""

    assignment: Dict[int, TileValue]
    domains: Dict[int, List[TileValue]]
    used_tiles: Dict[str, int]
    visible_so_far: Vec4


class TilePlacementCSP:
    """Solve tile placement with global constraints and AC-3-style pruning."""

    def __init__(self, problem: Problem):
        """Build static CSP structures and precompute per-block contributions."""
        self.problem = problem
        self.n = len(problem.landscape)
        self.blocks_per_side = self.n // 4
        self.num_blocks = self.blocks_per_side * self.blocks_per_side
        self.target: Vec4 = (
            problem.targets[1],
            problem.targets[2],
            problem.targets[3],
            problem.targets[4],
        )

        if sum(problem.tiles.get(s, 0) for s in SHAPES) != self.num_blocks:
            raise ValueError(
                "Tile inventory must exactly match number of 4x4 blocks: "
                f"{sum(problem.tiles.get(s, 0) for s in SHAPES)} != {self.num_blocks}"
            )

        allowed_values = [v for v in all_values() if problem.tiles.get(v[0], 0) > 0]
        self.initial_domains: Dict[int, List[TileValue]] = {
            b: allowed_values[:] for b in range(self.num_blocks)
        }

        self.contrib: List[Dict[TileValue, Vec4]] = [dict() for _ in range(self.num_blocks)]
        self._precompute_contribs()

        # Precompute per-block min/max contribution bounds over all values — used
        # for fast feasibility checks without scanning domains at runtime.
        self._block_min: List[Vec4] = []
        self._block_max: List[Vec4] = []
        for b in range(self.num_blocks):
            contribs = list(self.contrib[b].values())
            self._block_min.append(tuple(min(c[i] for c in contribs) for i in range(4)))  # type: ignore
            self._block_max.append(tuple(max(c[i] for c in contribs) for i in range(4)))  # type: ignore

    def _block_origin(self, b: int) -> Tuple[int, int]:
        """Return top-left landscape coordinates for block id b."""
        br = b // self.blocks_per_side
        bc = b % self.blocks_per_side
        return br * 4, bc * 4

    def _precompute_contribs(self) -> None:
        """Precompute visible color contribution vector for each (block, value)."""
        for b in range(self.num_blocks):
            r0, c0 = self._block_origin(b)
            colors = [[self.problem.landscape[r0 + r][c0 + c] for c in range(4)] for r in range(4)]
            for value in self.initial_domains[b]:
                mask = mask_for(value)
                counts = [0, 0, 0, 0]
                for r in range(4):
                    for c in range(4):
                        if not mask[r][c]:
                            color = colors[r][c]
                            if 1 <= color <= 4:
                                counts[color - 1] += 1
                self.contrib[b][value] = (counts[0], counts[1], counts[2], counts[3])

    # ---------- Heuristics ----------

    def _select_unassigned_var_mrv(self, st: State) -> int:
        unassigned = [b for b in range(self.num_blocks) if b not in st.assignment]
        return min(unassigned, key=lambda b: (len(st.domains[b]), b))

    def _order_values_lcv(self, st: State, b: int) -> List[TileValue]:
        """
        Lightweight LCV: score each value by how much it pushes visible totals
        toward the target (prefer values that leave more slack), without the
        expensive full-domain scan of the original implementation.
        """
        scored: List[Tuple[int, TileValue]] = []
        remaining_unassigned = self.num_blocks - len(st.assignment) - 1  # after assigning b

        for v in st.domains[b]:
            if st.used_tiles[v[0]] + 1 > self.problem.tiles[v[0]]:
                continue

            new_vis = addv(st.visible_so_far, self.contrib[b][v])
            if any(new_vis[i] > self.target[i] for i in range(4)):
                continue

            # Cheap slack score: sum of remaining headroom across all colors.
            # Larger slack = less constraining = try first (lower score = better).
            slack = sum(self.target[i] - new_vis[i] for i in range(4))
            scored.append((-slack, v))  # negate so min = most slack

        scored.sort(key=lambda item: (item[0], item[1][0], item[1][1]))
        return [v for _, v in scored]

    # ---------- Feasibility ----------

    def _value_feasible(self, st: State, b: int, v: TileValue) -> bool:
        if b in st.assignment:
            return st.assignment[b] == v

        if st.used_tiles[v[0]] + 1 > self.problem.tiles[v[0]]:
            return False

        new_visible = addv(st.visible_so_far, self.contrib[b][v])
        if any(new_visible[i] > self.target[i] for i in range(4)):
            return False

        remaining_blocks = [rb for rb in range(self.num_blocks) if rb not in st.assignment and rb != b]

        required_left = {
            s: self.problem.tiles[s] - st.used_tiles[s] - (1 if s == v[0] else 0)
            for s in SHAPES
        }
        if not self._shape_bounds_feasible(st, remaining_blocks, required_left):
            return False

        # Use domain-based min/max for assigned remaining; fall back to precomputed
        # global bounds — avoids re-scanning domains when they haven't changed.
        min_add = [0, 0, 0, 0]
        max_add = [0, 0, 0, 0]

        for rb in remaining_blocks:
            vals = st.domains[rb]
            if not vals:
                return False
            if len(vals) == len(self.initial_domains[rb]):
                # Domain untouched — use precomputed bounds (fast path)
                for i in range(4):
                    min_add[i] += self._block_min[rb][i]
                    max_add[i] += self._block_max[rb][i]
            else:
                poss = [self.contrib[rb][vv] for vv in vals]
                for i in range(4):
                    min_add[i] += min(p[i] for p in poss)
                    max_add[i] += max(p[i] for p in poss)

        for i in range(4):
            total_min = new_visible[i] + min_add[i]
            total_max = new_visible[i] + max_add[i]
            if self.target[i] < total_min or self.target[i] > total_max:
                return False

        return True

    def _shape_bounds_feasible(
        self,
        st: State,
        remaining_blocks: List[int],
        required_left: Dict[str, int],
    ) -> bool:
        """Check whether required remaining shape counts can fit remaining domains."""
        m = len(remaining_blocks)
        if any(req < 0 for req in required_left.values()):
            return False
        if sum(required_left.values()) != m:
            return False

        upper: Dict[str, int] = {s: 0 for s in SHAPES}
        for rb in remaining_blocks:
            shapes_here = {val[0] for val in st.domains[rb]}
            for s in SHAPES:
                if s in shapes_here:
                    upper[s] += 1

        lower: Dict[str, int] = {}
        for s in SHAPES:
            lower[s] = max(0, m - sum(upper[o] for o in SHAPES if o != s))

        for s in SHAPES:
            if required_left[s] < lower[s] or required_left[s] > upper[s]:
                return False
        return True

    # ---------- Propagation ----------

    def _ac3_propagate(self, st: State, initial_queue: List[int]) -> bool:
        """
        AC-3 with one important optimisation: once a domain shrinks to size 1
        we immediately check whether that forced assignment overshoots targets,
        and only re-enqueue neighbours when the domain actually shrank.
        """
        q = deque(initial_queue)
        in_queue = set(initial_queue)

        while q:
            b = q.popleft()
            in_queue.discard(b)

            if b in st.assignment:
                continue

            old_len = len(st.domains[b])
            new_domain = [v for v in st.domains[b] if self._value_feasible(st, b, v)]

            if not new_domain:
                return False

            if len(new_domain) < old_len:
                st.domains[b] = new_domain
                for nb in range(self.num_blocks):
                    if nb not in st.assignment and nb != b and nb not in in_queue:
                        q.append(nb)
                        in_queue.add(nb)

        return True

    # ---------- Tentative state ----------

    def _tentative_state(self, st: State, b: int, v: TileValue) -> Optional[State]:
        if b in st.assignment:
            return None
        if st.used_tiles[v[0]] + 1 > self.problem.tiles[v[0]]:
            return None

        new_visible = addv(st.visible_so_far, self.contrib[b][v])
        if any(new_visible[i] > self.target[i] for i in range(4)):
            return None

        new_assignment = dict(st.assignment)
        new_assignment[b] = v

        new_domains = {k: vals[:] for k, vals in st.domains.items()}
        new_domains[b] = [v]

        new_used = dict(st.used_tiles)
        new_used[v[0]] += 1

        return State(
            assignment=new_assignment,
            domains=new_domains,
            used_tiles=new_used,
            visible_so_far=new_visible,
        )

    # ---------- Search ----------

    def solve(self) -> Optional[Dict[int, TileValue]]:
        """Run initial propagation and then backtracking search."""
        st = State(
            assignment={},
            domains={b: vals[:] for b, vals in self.initial_domains.items()},
            used_tiles={s: 0 for s in SHAPES},
            visible_so_far=(0, 0, 0, 0),
        )

        if not self._ac3_propagate(st, list(range(self.num_blocks))):
            return None

        return self._backtrack(st)

    def _backtrack(self, st: State) -> Optional[Dict[int, TileValue]]:
        """Depth-first backtracking with MRV/LCV and propagation after assignment."""
        if len(st.assignment) == self.num_blocks:
            if st.visible_so_far == self.target and all(
                st.used_tiles[s] == self.problem.tiles[s] for s in SHAPES
            ):
                return dict(st.assignment)
            return None

        b = self._select_unassigned_var_mrv(st)
        values = self._order_values_lcv(st, b)

        for v in values:
            next_state = self._tentative_state(st, b, v)
            if next_state is None:
                continue

            queue = [rb for rb in range(self.num_blocks) if rb not in next_state.assignment]
            if not self._ac3_propagate(next_state, queue):
                continue

            result = self._backtrack(next_state)
            if result is not None:
                return result

        return None