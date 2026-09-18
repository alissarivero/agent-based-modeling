from sim.config import AgentType, LandscapeClass, MissionSpec, SchedulerKind, SocialCondition
from sim.export import session_to_records
from sim.scheduler import run_session


def _spec(small_config, seed: int = 42) -> MissionSpec:
    return MissionSpec(
        landscape_class=LandscapeClass.smooth,
        triplet_id=0,
        condition=SocialCondition.diff_attract,
        agent_a=AgentType.searcher,
        agent_b=AgentType.maximizer,
        scheduler=SchedulerKind.repeat_five,
        seed=seed,
        config=small_config,
    )


def test_same_seed_replays_identically(small_config) -> None:
    a = run_session(_spec(small_config), record_frames=True)
    b = run_session(_spec(small_config), record_frames=True)
    assert [ep.agents[0].path for ep in a.episodes] == [ep.agents[0].path for ep in b.episodes]
    assert [ep.agents[0].reward for ep in a.episodes] == [ep.agents[0].reward for ep in b.episodes]
    assert [frame["t"] for frame in a.frames] == [frame["t"] for frame in b.frames]
    assert a.frames[-1]["session_done"] is True


def test_different_seed_can_diverge(small_config) -> None:
    spec_a = _spec(small_config, seed=1)
    spec_b = _spec(small_config, seed=99)
    spec_a.agent_b = AgentType.random
    spec_b.agent_b = AgentType.random
    a = run_session(spec_a)
    b = run_session(spec_b)
    assert session_to_records(a)
    assert [ep.agents[1].path for ep in a.episodes] != [ep.agents[1].path for ep in b.episodes]
