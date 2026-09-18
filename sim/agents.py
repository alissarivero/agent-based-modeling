from __future__ import annotations

import numpy as np

from sim.config import AgentType, SimConfig
from sim.constraints import chebyshev, legal_moves
from sim.environment import GridWorld


class Agent:
    def __init__(self, agent_id: int, agent_type: AgentType, x: int, y: int, config: SimConfig):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.x = x
        self.y = y
        self.config = config
        n = config.grid
        self.seen = np.zeros((n, n), dtype=bool)
        self.belief = np.zeros((n, n), dtype=np.float64)
        self.known_residual = np.zeros((n, n), dtype=np.float64)
        self.visited = np.zeros((n, n), dtype=bool)
        self.score = 0.0
        self.high_cleared = 0
        self.path: list[tuple[int, int]] = [(x, y)]

    def reset_for_episode(self, x: int, y: int, persist_memory: bool) -> None:
        self.x = x
        self.y = y
        self.score = 0.0
        self.high_cleared = 0
        self.visited[:] = False
        self.path = [(x, y)]
        if persist_memory:
            # Same prior either way: the last grid they remember. They are not
            # told that resources refilled or that the map was swapped.
            self.known_residual = self.belief.copy()
        else:
            self.seen[:] = False
            self.belief[:] = 0.0
            self.known_residual[:] = 0.0

    def sense(self, world: GridWorld) -> None:
        x0, x1, y0, y1 = world.vision_window(self.x, self.y, self.config.vision)
        view = world.residual[y0:y1, x0:x1]
        was_seen = self.seen[y0:y1, x0:x1].copy()
        self.seen[y0:y1, x0:x1] = True
        positive = view > 0
        belief = self.belief[y0:y1, x0:x1]
        belief[positive] = view[positive]
        belief[~was_seen & ~positive] = 0.0
        self.known_residual[y0:y1, x0:x1] = view

    def collect(self, world: GridWorld) -> float:
        value = world.collect(self.x, self.y)
        if not self.visited[self.y, self.x] and world.original[self.y, self.x] >= self.config.tau:
            self.high_cleared += 1
        self.visited[self.y, self.x] = True
        self.score += value
        return value

    def cells_seen(self) -> int:
        return int(self.seen.sum())

    def cells_visited(self) -> int:
        return int(self.visited.sum())

    def snapshot(self) -> dict:
        return {
            "id": self.agent_id,
            "type": self.agent_type.value,
            "x": self.x,
            "y": self.y,
            "score": round(self.score, 6),
            "seen": self.cells_seen(),
            "visited": self.cells_visited(),
        }


def _tie_break(rng: np.random.Generator, items: list, scores: list[float], maximize: bool) -> object:
    if not items:
        raise ValueError("no items to choose")
    best = max(scores) if maximize else min(scores)
    tied = [item for item, score in zip(items, scores) if score == best]
    if len(tied) == 1:
        return tied[0]
    return tied[int(rng.integers(0, len(tied)))]


def nearest_high_target(agent: Agent, rng: np.random.Generator) -> tuple[int, int] | None:
    mask = (
        agent.seen
        & (agent.known_residual >= agent.config.tau)
        & ~agent.visited
    )
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    dist = np.maximum(np.abs(ys - agent.y), np.abs(xs - agent.x))
    best = float(dist.min())
    tied = np.flatnonzero(dist == best)
    j = int(tied[int(rng.integers(0, len(tied)))])
    return int(xs[j]), int(ys[j])


def best_value_target(agent: Agent, rng: np.random.Generator) -> tuple[int, int] | None:
    mask = agent.seen & (agent.known_residual > 1e-12) & ~agent.visited
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    vals = agent.known_residual[ys, xs]
    dist = np.maximum(np.maximum(np.abs(ys - agent.y), np.abs(xs - agent.x)), 1)
    score = vals / dist
    best = float(score.max())
    tied = np.flatnonzero(score == best)
    j = int(tied[int(rng.integers(0, len(tied)))])
    return int(xs[j]), int(ys[j])


def unknown_in_vision(agent: Agent, x: int, y: int) -> int:
    r = agent.config.vision
    n = agent.config.grid
    x0, x1 = max(0, x - r), min(n, x + r + 1)
    y0, y1 = max(0, y - r), min(n, y + r + 1)
    return int(np.count_nonzero(~agent.seen[y0:y1, x0:x1]))


def move_toward(
    legal: list[tuple[int, int]],
    target: tuple[int, int],
    rng: np.random.Generator,
) -> tuple[int, int]:
    scores = [chebyshev(x, y, target[0], target[1]) for x, y in legal]
    return _tie_break(rng, legal, scores, maximize=False)  # type: ignore[return-value]


def explore_frontier(agent: Agent, legal: list[tuple[int, int]], rng: np.random.Generator) -> tuple[int, int]:
    scores = [float(unknown_in_vision(agent, x, y)) for x, y in legal]
    return _tie_break(rng, legal, scores, maximize=True)  # type: ignore[return-value]


def choose_move(
    agent: Agent,
    legal: list[tuple[int, int]],
    rng: np.random.Generator,
) -> tuple[int, int]:
    if not legal:
        return agent.x, agent.y
    if agent.agent_type == AgentType.random:
        return legal[int(rng.integers(0, len(legal)))]
    if agent.agent_type == AgentType.searcher:
        target = nearest_high_target(agent, rng)
    else:
        target = best_value_target(agent, rng)
    if target is not None:
        return move_toward(legal, target, rng)
    return explore_frontier(agent, legal, rng)


def decide(
    agent: Agent,
    partner: tuple[int, int] | None,
    condition,
    rng: np.random.Generator,
) -> tuple[int, int]:
    cfg = agent.config
    legal = legal_moves(
        agent.x,
        agent.y,
        partner,
        condition,
        cfg.grid,
        cfg.attract_r,
        cfg.avoid_r,
        include_stay=False,
    )
    if not legal:
        stay = legal_moves(
            agent.x,
            agent.y,
            partner,
            condition,
            cfg.grid,
            cfg.attract_r,
            cfg.avoid_r,
            include_stay=True,
        )
        return stay[0] if stay else (agent.x, agent.y)
    return choose_move(agent, legal, rng)
