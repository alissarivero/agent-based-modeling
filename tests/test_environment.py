import numpy as np

from sim.config import AgentType, LandscapeClass, MissionSpec, SchedulerKind, SocialCondition
from sim.environment import GridWorld
from sim.scheduler import run_session


def test_collect_depletes_and_conserves() -> None:
    original = np.array([[0.5, 0.2], [0.1, 0.8]])
    world = GridWorld(original)
    assert world.collect(0, 0) == 0.5
    assert world.residual[0, 0] == 0.0
    assert world.collect(0, 0) == 0.0
    assert world.collect(1, 1) == 0.8
    np.testing.assert_allclose(world.residual.sum() + 1.3, original.sum())


def test_session_conserves_reward(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.smooth,
        triplet_id=0,
        condition=SocialCondition.solo,
        agent_a=AgentType.searcher,
        scheduler=SchedulerKind.repeat_five,
        seed=11,
        config=small_config,
    )
    session = run_session(spec)
    for episode in session.episodes:
        collected = sum(agent.reward for agent in episode.agents)
        np.testing.assert_allclose(
            collected + episode.remaining_reward,
            episode.total_reward_available,
            atol=1e-9,
        )
