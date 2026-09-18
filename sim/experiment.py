from __future__ import annotations

from collections.abc import Callable

from sim.config import (
    AgentType,
    BatchSpec,
    MissionSpec,
    SocialCondition,
)
from sim.export import sessions_to_frame
from sim.models import SessionResult
from sim.scheduler import run_session

DIFF_CONDITIONS = {SocialCondition.diff_attract, SocialCondition.diff_avoid}
SAME_CONDITIONS = {SocialCondition.same_attract, SocialCondition.same_avoid}


def pairings_for(condition: SocialCondition, types: list[AgentType]) -> list[tuple[AgentType, AgentType | None]]:
    unique = list(dict.fromkeys(types))
    if condition == SocialCondition.solo:
        return [(t, None) for t in unique]
    if condition in SAME_CONDITIONS:
        return [(t, t) for t in unique]
    pairs = []
    for i, a in enumerate(unique):
        for b in unique[i + 1 :]:
            pairs.append((a, b))
    return pairs


def expand_batch(spec: BatchSpec) -> list[MissionSpec]:
    missions: list[MissionSpec] = []
    for seed_i in range(spec.n_seeds):
        seed = spec.base_seed + seed_i
        for landscape_class in spec.landscape_classes:
            for condition in spec.conditions:
                for scheduler in spec.schedulers:
                    for agent_a, agent_b in pairings_for(condition, spec.agent_types):
                        if scheduler.value == "each_grid":
                            missions.append(
                                MissionSpec(
                                    landscape_class=landscape_class,
                                    triplet_id=spec.triplet_ids[0] if spec.triplet_ids else 0,
                                    condition=condition,
                                    agent_a=agent_a,
                                    agent_b=agent_b,
                                    scheduler=scheduler,
                                    seed=seed,
                                    config=spec.config,
                                )
                            )
                        else:
                            for triplet_id in spec.triplet_ids:
                                missions.append(
                                    MissionSpec(
                                        landscape_class=landscape_class,
                                        triplet_id=triplet_id,
                                        condition=condition,
                                        agent_a=agent_a,
                                        agent_b=agent_b,
                                        scheduler=scheduler,
                                        seed=seed,
                                        config=spec.config,
                                    )
                                )
    return missions


def run_batch(
    spec: BatchSpec,
    record_frames: bool = False,
    progress: Callable[[int, int, SessionResult], None] | None = None,
) -> list[SessionResult]:
    missions = expand_batch(spec)
    results: list[SessionResult] = []
    total = len(missions)
    for i, mission in enumerate(missions, start=1):
        result = run_session(
            mission,
            record_frames=record_frames,
            include_paths=record_frames,
        )
        results.append(result)
        if progress:
            progress(i, total, result)
    return results


def run_batch_frame(spec: BatchSpec):
    return sessions_to_frame(run_batch(spec))
