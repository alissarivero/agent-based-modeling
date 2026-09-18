from sim.config import AgentType, LandscapeClass, MissionSpec, SchedulerKind, SocialCondition
from sim.experiment import expand_batch
from sim.config import BatchSpec
from sim.scheduler import run_session


def test_repeat_five_uses_same_grid(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.rough,
        triplet_id=1,
        condition=SocialCondition.solo,
        agent_a=AgentType.searcher,
        scheduler=SchedulerKind.repeat_five,
        seed=9,
        config=small_config,
    )
    session = run_session(spec)
    assert session.n_episodes == 5
    assert [ep.triplet_id for ep in session.episodes] == [1] * 5
    assert session.learning_gain is not None


def test_each_grid_visits_all_triplets(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.smooth,
        triplet_id=0,
        condition=SocialCondition.solo,
        agent_a=AgentType.maximizer,
        scheduler=SchedulerKind.each_grid,
        seed=9,
        config=small_config,
    )
    session = run_session(spec)
    assert [ep.triplet_id for ep in session.episodes] == list(range(small_config.n_triplets))
    assert session.learning_gain is not None


def test_first_episode_starts_with_local_vision_only(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.smooth,
        triplet_id=0,
        condition=SocialCondition.solo,
        agent_a=AgentType.random,
        scheduler=SchedulerKind.repeat_five,
        seed=2,
        config=small_config,
    )
    session = run_session(spec)
    window = (2 * small_config.vision + 1) ** 2
    assert session.episodes[0].agents[0].cells_seen <= window + small_config.steps * (2 * small_config.vision + 1)
    assert session.episodes[0].agents[0].cells_seen < small_config.grid ** 2


def test_memory_persists_when_grid_changes(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.smooth,
        triplet_id=0,
        condition=SocialCondition.solo,
        agent_a=AgentType.searcher,
        scheduler=SchedulerKind.each_grid,
        seed=13,
        config=small_config,
    )
    session = run_session(spec)
    seen = [ep.agents[0].cells_seen for ep in session.episodes]
    assert seen[-1] >= seen[0]


def test_repeat_memory_grows_seen_cells(small_config) -> None:
    spec = MissionSpec(
        landscape_class=LandscapeClass.smooth,
        triplet_id=0,
        condition=SocialCondition.solo,
        agent_a=AgentType.searcher,
        scheduler=SchedulerKind.repeat_five,
        seed=13,
        config=small_config,
    )
    session = run_session(spec)
    seen = [ep.agents[0].cells_seen for ep in session.episodes]
    assert seen[-1] >= seen[0]


def test_expand_batch_covers_pairings(small_config) -> None:
    spec = BatchSpec(
        landscape_classes=[LandscapeClass.random],
        conditions=list(SocialCondition),
        agent_types=list(AgentType),
        schedulers=[SchedulerKind.each_grid],
        triplet_ids=[0],
        n_seeds=1,
        config=small_config,
    )
    missions = expand_batch(spec)
    # solo 3 + same attract 3 + same avoid 3 + diff attract 3 + diff avoid 3
    assert len(missions) == 15
