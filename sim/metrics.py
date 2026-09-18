from __future__ import annotations

import numpy as np

from sim.agents import Agent
from sim.config import MissionSpec
from sim.environment import GridWorld
from sim.models import AgentEpisodeMetrics, EpisodeResult


def agent_metrics(
    agent: Agent,
    role: str,
    high_value_total: int,
    include_path: bool = True,
) -> AgentEpisodeMetrics:
    fraction = agent.high_cleared / high_value_total if high_value_total else 0.0
    return AgentEpisodeMetrics(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        role=role,
        reward=round(agent.score, 6),
        cells_visited=agent.cells_visited(),
        high_value_cleared=agent.high_cleared,
        high_value_fraction=round(fraction, 6),
        cells_seen=agent.cells_seen(),
        path=list(agent.path) if include_path else [],
    )


def episode_result(
    spec: MissionSpec,
    episode: int,
    triplet_id: int,
    world: GridWorld,
    agents: list[Agent],
    distances: list[float],
    violations: int,
    include_original: bool = False,
    include_paths: bool = True,
) -> EpisodeResult:
    high_mask = world.high_value_mask(spec.config.tau)
    high_total = int(high_mask.sum())
    high_cleared = int(np.count_nonzero(high_mask & (world.residual == 0.0)))
    roles = ["focal", "partner"]
    return EpisodeResult(
        episode=episode,
        triplet_id=triplet_id,
        landscape_class=spec.landscape_class,
        steps=spec.config.steps,
        total_reward_available=round(float(world.original.sum()), 6),
        remaining_reward=round(float(world.residual.sum()), 6),
        high_value_total=high_total,
        high_value_cleared=high_cleared,
        mean_pairwise_distance=round(float(np.mean(distances)), 4) if distances else None,
        constraint_violations=violations,
        agents=[
            agent_metrics(agent, roles[i] if i < len(roles) else f"agent{i}", high_total, include_paths)
            for i, agent in enumerate(agents)
        ],
        original=world.original.tolist() if include_original else None,
    )


def learning_gain(rewards: list[float]) -> float | None:
    if len(rewards) < 2:
        return None
    return round(rewards[-1] - rewards[0], 6)
