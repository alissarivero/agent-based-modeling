from __future__ import annotations

from sim.config import SocialCondition

NEIGHBOR_DELTAS = tuple(
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if not (dx == 0 and dy == 0)
)


def chebyshev(x0: int, y0: int, x1: int, y1: int) -> int:
    return max(abs(x0 - x1), abs(y0 - y1))


def spawn_positions(
    grid: int,
    condition: SocialCondition,
    avoid_r: int = 5,
) -> list[tuple[int, int]]:
    c = (grid - 1) // 2
    if condition == SocialCondition.solo:
        return [(c, c)]
    if condition in (SocialCondition.same_attract, SocialCondition.diff_attract):
        return [(c, c), (min(grid - 1, c + 1), min(grid - 1, c + 1))]
    left = max(0, c - avoid_r // 2)
    right = min(grid - 1, left + avoid_r)
    return [(left, c), (right, c)]


def constraint_satisfied(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    condition: SocialCondition,
    attract_r: int,
    avoid_r: int,
) -> bool:
    if condition == SocialCondition.solo:
        return True
    dist = chebyshev(x0, y0, x1, y1)
    if condition in (SocialCondition.same_attract, SocialCondition.diff_attract):
        return dist <= attract_r
    return dist >= avoid_r


def in_bounds(x: int, y: int, grid: int) -> bool:
    return 0 <= x < grid and 0 <= y < grid


def neighbors(x: int, y: int, grid: int) -> list[tuple[int, int]]:
    cells = []
    for dx, dy in NEIGHBOR_DELTAS:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny, grid):
            cells.append((nx, ny))
    return cells


def legal_moves(
    x: int,
    y: int,
    partner: tuple[int, int] | None,
    condition: SocialCondition,
    grid: int,
    attract_r: int,
    avoid_r: int,
    include_stay: bool = False,
) -> list[tuple[int, int]]:
    candidates = neighbors(x, y, grid)
    if include_stay:
        candidates.append((x, y))
    if partner is None or condition == SocialCondition.solo:
        return candidates
    px, py = partner
    return [
        cell
        for cell in candidates
        if constraint_satisfied(cell[0], cell[1], px, py, condition, attract_r, avoid_r)
    ]
