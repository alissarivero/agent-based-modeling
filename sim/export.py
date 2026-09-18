from __future__ import annotations

from pathlib import Path

import pandas as pd

from sim.models import SessionResult


def session_to_records(session: SessionResult) -> list[dict]:
    rows = []
    for episode in session.episodes:
        shared = {
            "run_id": session.run_id,
            "seed": session.seed,
            "landscape_class": session.landscape_class.value,
            "triplet_id": episode.triplet_id,
            "condition": session.condition.value,
            "scheduler": session.scheduler.value,
            "agent_a": session.agent_a.value,
            "agent_b": session.agent_b.value if session.agent_b else "",
            "episode": episode.episode,
            "steps": episode.steps,
            "total_reward_available": episode.total_reward_available,
            "remaining_reward": episode.remaining_reward,
            "high_value_total": episode.high_value_total,
            "high_value_cleared_map": episode.high_value_cleared,
            "mean_pairwise_distance": episode.mean_pairwise_distance,
            "constraint_violations": episode.constraint_violations,
            "learning_gain": session.learning_gain,
        }
        for agent in episode.agents:
            rows.append(
                {
                    **shared,
                    "agent_type": agent.agent_type.value,
                    "role": agent.role,
                    "reward": agent.reward,
                    "cells_visited": agent.cells_visited,
                    "high_value_cleared": agent.high_value_cleared,
                    "high_value_fraction": agent.high_value_fraction,
                    "cells_seen": agent.cells_seen,
                }
            )
    return rows


def sessions_to_frame(sessions: list[SessionResult]) -> pd.DataFrame:
    records: list[dict] = []
    for session in sessions:
        records.extend(session_to_records(session))
    if not records:
        return pd.DataFrame()
    return pd.DataFrame.from_records(records)


def write_csv(sessions: list[SessionResult], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sessions_to_frame(sessions).to_csv(path, index=False)
    return path
