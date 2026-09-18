from __future__ import annotations

import uuid

import numpy as np

from sim.agents import Agent, decide
from sim.config import MissionSpec, SchedulerKind
from sim.constraints import chebyshev, constraint_satisfied, spawn_positions
from sim.environment import GridWorld
from sim.landscapes import load_landscape
from sim.metrics import episode_result, learning_gain
from sim.models import Frame, FrameAgent, SessionResult


def _make_agents(spec: MissionSpec, positions: list[tuple[int, int]]) -> list[Agent]:
    types = [spec.agent_a] if spec.n_agents == 1 else [spec.agent_a, spec.agent_b]
    return [
        Agent(i, agent_type, positions[i][0], positions[i][1], spec.config)
        for i, agent_type in enumerate(types)
    ]


def _partner_of(agents: list[Agent], index: int) -> tuple[int, int] | None:
    if len(agents) < 2:
        return None
    other = agents[1 - index]
    return other.x, other.y


def _constraint_ok(spec: MissionSpec, agents: list[Agent]) -> bool:
    if len(agents) < 2:
        return True
    return constraint_satisfied(
        agents[0].x,
        agents[0].y,
        agents[1].x,
        agents[1].y,
        spec.condition,
        spec.config.attract_r,
        spec.config.avoid_r,
    )


def _frame(
    spec: MissionSpec,
    episode: int,
    triplet_id: int,
    t: int,
    world: GridWorld,
    agents: list[Agent],
    residual: bool,
    episode_done: bool,
    session_done: bool,
) -> dict:
    dirty = [{"x": x, "y": y, "v": v} for x, y, v in world.take_dirty()]
    frame = Frame(
        t=t,
        episode=episode,
        triplet_id=triplet_id,
        landscape_class=spec.landscape_class,
        residual=world.residual.tolist() if residual else None,
        dirty=dirty,
        agents=[FrameAgent(**agent.snapshot()) for agent in agents],
        constraint_ok=_constraint_ok(spec, agents),
        episode_done=episode_done,
        session_done=session_done,
    )
    return frame.model_dump(mode="json")


def episode_triplet_ids(spec: MissionSpec) -> list[int]:
    if spec.scheduler == SchedulerKind.repeat_five:
        return [spec.triplet_id] * spec.config.n_repeat_episodes
    return list(range(spec.config.n_triplets))


def run_episode(
    spec: MissionSpec,
    world: GridWorld,
    agents: list[Agent],
    rng: np.random.Generator,
    episode: int,
    triplet_id: int,
    persist_memory: bool,
    record_frames: bool,
    include_original: bool,
    include_paths: bool = True,
) -> tuple[object, list[dict]]:
    positions = spawn_positions(spec.config.grid, spec.condition, spec.config.avoid_r)
    for agent, (x, y) in zip(agents, positions):
        agent.reset_for_episode(x, y, persist_memory)
    world.reset()

    frames: list[dict] = []
    distances: list[float] = []
    violations = 0

    for agent in agents:
        agent.sense(world)
        agent.collect(world)
        agent.sense(world)

    if record_frames:
        frames.append(
            _frame(spec, episode, triplet_id, 0, world, agents, residual=True, episode_done=False, session_done=False)
        )

    if len(agents) == 2:
        distances.append(float(chebyshev(agents[0].x, agents[0].y, agents[1].x, agents[1].y)))
        if not _constraint_ok(spec, agents):
            violations += 1

    for t in range(1, spec.config.steps + 1):
        order = rng.permutation(len(agents))
        for index in order:
            agent = agents[int(index)]
            agent.sense(world)
            nx, ny = decide(agent, _partner_of(agents, int(index)), spec.condition, rng)
            agent.x, agent.y = nx, ny
            agent.path.append((nx, ny))
            agent.collect(world)
            agent.sense(world)
        if len(agents) == 2:
            distances.append(float(chebyshev(agents[0].x, agents[0].y, agents[1].x, agents[1].y)))
            if not _constraint_ok(spec, agents):
                violations += 1
        if record_frames:
            frames.append(
                _frame(
                    spec,
                    episode,
                    triplet_id,
                    t,
                    world,
                    agents,
                    residual=False,
                    episode_done=t == spec.config.steps,
                    session_done=False,
                )
            )

    result = episode_result(
        spec,
        episode,
        triplet_id,
        world,
        agents,
        distances,
        violations,
        include_original=include_original,
        include_paths=include_paths,
    )
    return result, frames


def run_session(
    spec: MissionSpec,
    record_frames: bool = False,
    include_original: bool = False,
    include_paths: bool = True,
) -> SessionResult:
    rng = np.random.default_rng(spec.seed)
    triplet_ids = episode_triplet_ids(spec)
    positions = spawn_positions(spec.config.grid, spec.condition, spec.config.avoid_r)
    agents = _make_agents(spec, positions)
    episodes = []
    frames: list[dict] = []

    for episode, triplet_id in enumerate(triplet_ids):
        grid = load_landscape(triplet_id, spec.landscape_class, spec.config)
        world = GridWorld(grid)
        # Episode 0 is a blank slate. Later episodes keep last-grid memory;
        # agents are never told that the map changed or that patches refilled.
        ep, ep_frames = run_episode(
            spec,
            world,
            agents,
            rng,
            episode,
            triplet_id,
            persist_memory=episode > 0,
            record_frames=record_frames,
            include_original=include_original,
            include_paths=include_paths,
        )
        episodes.append(ep)
        if record_frames:
            if episode == len(triplet_ids) - 1 and ep_frames:
                ep_frames[-1]["session_done"] = True
            frames.extend(ep_frames)

    focal_rewards = [ep.agents[0].reward for ep in episodes]
    return SessionResult(
        run_id=str(uuid.uuid4()),
        seed=spec.seed,
        condition=spec.condition,
        scheduler=spec.scheduler,
        landscape_class=spec.landscape_class,
        triplet_id=spec.triplet_id,
        agent_a=spec.agent_a,
        agent_b=spec.agent_b,
        n_episodes=len(episodes),
        learning_gain=learning_gain(focal_rewards),
        episodes=episodes,
        frames=frames,
    )


def iter_session_frames(spec: MissionSpec):
    result = run_session(spec, record_frames=True)
    yield from result.frames
