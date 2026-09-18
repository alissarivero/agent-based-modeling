from sim.config import AgentType, LandscapeClass, MissionSpec, SchedulerKind, SocialCondition
from sim.constraints import chebyshev, spawn_positions
from sim.scheduler import run_session


def test_avoid_spawns_at_least_radius(small_config) -> None:
    a, b = spawn_positions(small_config.grid, SocialCondition.same_avoid, small_config.avoid_r)
    assert chebyshev(a[0], a[1], b[0], b[1]) >= small_config.avoid_r


def test_attract_never_violates(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.rough,
        triplet_id=1,
        condition=SocialCondition.same_attract,
        agent_a=AgentType.maximizer,
        agent_b=AgentType.maximizer,
        scheduler=SchedulerKind.repeat_five,
        seed=3,
        config=small_config,
    )
    session = run_session(spec)
    assert all(ep.constraint_violations == 0 for ep in session.episodes)
    for episode in session.episodes:
        path_a = episode.agents[0].path
        path_b = episode.agents[1].path
        for (x0, y0), (x1, y1) in zip(path_a, path_b):
            assert chebyshev(x0, y0, x1, y1) <= small_config.attract_r


def test_avoid_never_violates(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.random,
        triplet_id=2,
        condition=SocialCondition.diff_avoid,
        agent_a=AgentType.searcher,
        agent_b=AgentType.random,
        scheduler=SchedulerKind.each_grid,
        seed=5,
        config=small_config,
    )
    session = run_session(spec)
    assert all(ep.constraint_violations == 0 for ep in session.episodes)
    for episode in session.episodes:
        for (x0, y0), (x1, y1) in zip(episode.agents[0].path, episode.agents[1].path):
            assert chebyshev(x0, y0, x1, y1) >= small_config.avoid_r
