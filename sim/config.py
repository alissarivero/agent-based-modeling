from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class AgentType(str, Enum):
    searcher = "searcher"
    maximizer = "maximizer"
    random = "random"


class LandscapeClass(str, Enum):
    smooth = "smooth"
    rough = "rough"
    random = "random"


class SocialCondition(str, Enum):
    solo = "solo"
    same_attract = "same_attract"
    diff_attract = "diff_attract"
    same_avoid = "same_avoid"
    diff_avoid = "diff_avoid"


class SchedulerKind(str, Enum):
    repeat_five = "repeat_five"
    each_grid = "each_grid"


class SimConfig(BaseModel):
    grid: int = 110
    steps: int = 200
    vision: int = 7
    tau: float = 0.7
    attract_r: int = 2
    avoid_r: int = 5
    n_triplets: int = 5
    n_repeat_episodes: int = 5
    density_means: tuple[float, float, float, float, float] = (
        0.25,
        0.35,
        0.45,
        0.55,
        0.65,
    )
    beta_concentration: float = 4.0
    grf_smooth_sigma: float = 18.0
    grf_rough_sigma: float = 5.0
    landscape_seed: int = 20260918
    data_dir: Path = Path("data/landscapes")

    @property
    def center(self) -> int:
        return (self.grid - 1) // 2


DEFAULT_CONFIG = SimConfig()


class MissionSpec(BaseModel):
    landscape_class: LandscapeClass
    triplet_id: int = Field(ge=0, le=4)
    condition: SocialCondition
    agent_a: AgentType
    agent_b: AgentType | None = None
    scheduler: SchedulerKind = SchedulerKind.repeat_five
    seed: int = 1
    config: SimConfig = Field(default_factory=SimConfig)

    @model_validator(mode="after")
    def validate_pairing(self) -> MissionSpec:
        if self.condition == SocialCondition.solo:
            self.agent_b = None
            return self
        if self.agent_b is None:
            raise ValueError("Paired conditions require agent_b")
        same = self.agent_a == self.agent_b
        if self.condition in (
            SocialCondition.same_attract,
            SocialCondition.same_avoid,
        ) and not same:
            raise ValueError("Same-type conditions require matching agent types")
        if self.condition in (
            SocialCondition.diff_attract,
            SocialCondition.diff_avoid,
        ) and same:
            raise ValueError("Different-type conditions require distinct agent types")
        return self

    @property
    def n_agents(self) -> int:
        return 1 if self.condition == SocialCondition.solo else 2


class BatchSpec(BaseModel):
    landscape_classes: list[LandscapeClass] = Field(
        default_factory=lambda: list(LandscapeClass)
    )
    conditions: list[SocialCondition] = Field(
        default_factory=lambda: list(SocialCondition)
    )
    agent_types: list[AgentType] = Field(default_factory=lambda: list(AgentType))
    schedulers: list[SchedulerKind] = Field(
        default_factory=lambda: list(SchedulerKind)
    )
    triplet_ids: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    n_seeds: int = 1
    base_seed: int = 1000
    config: SimConfig = Field(default_factory=SimConfig)
