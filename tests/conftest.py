from pathlib import Path

import pytest

from sim.config import SimConfig
from sim.landscapes import generate_library


@pytest.fixture
def small_config(tmp_path: Path) -> SimConfig:
    cfg = SimConfig(
        grid=16,
        steps=40,
        vision=4,
        tau=0.7,
        attract_r=2,
        avoid_r=5,
        n_triplets=3,
        n_repeat_episodes=5,
        density_means=(0.25, 0.45, 0.65, 0.55, 0.35),
        landscape_seed=7,
        data_dir=tmp_path / "landscapes",
    )
    generate_library(cfg, force=True)
    return cfg
