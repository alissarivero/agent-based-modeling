from __future__ import annotations

from pydantic import BaseModel, Field

from sim.config import AgentType, LandscapeClass, SchedulerKind, SocialCondition


class AgentEpisodeMetrics(BaseModel):
    agent_id: int
    agent_type: AgentType
    role: str
    reward: float
    cells_visited: int
    high_value_cleared: int
    high_value_fraction: float
    cells_seen: int
    path: list[tuple[int, int]] = Field(default_factory=list)


class EpisodeResult(BaseModel):
    episode: int
    triplet_id: int
    landscape_class: LandscapeClass
    steps: int
    total_reward_available: float
    remaining_reward: float
    high_value_total: int
    high_value_cleared: int
    mean_pairwise_distance: float | None
    constraint_violations: int
    agents: list[AgentEpisodeMetrics]
    original: list[list[float]] | None = None


class SessionResult(BaseModel):
    run_id: str
    seed: int
    condition: SocialCondition
    scheduler: SchedulerKind
    landscape_class: LandscapeClass
    triplet_id: int
    agent_a: AgentType
    agent_b: AgentType | None
    n_episodes: int
    learning_gain: float | None
    episodes: list[EpisodeResult]
    frames: list[dict] = Field(default_factory=list)


class FrameAgent(BaseModel):
    id: int
    type: AgentType
    x: int
    y: int
    score: float
    seen: int
    visited: int


class Frame(BaseModel):
    t: int
    episode: int
    triplet_id: int
    landscape_class: LandscapeClass
    residual: list[list[float]] | None = None
    dirty: list[dict]
    agents: list[FrameAgent]
    constraint_ok: bool
    episode_done: bool
    session_done: bool
