import { useEffect, useMemo, useRef, useState } from "react";
import { GridCanvas } from "../components/GridCanvas";
import type { Frame, FrameAgent, MissionSpec, SimConfig } from "../types";

interface Props {
  spec: MissionSpec;
  config: SimConfig;
  frames: Frame[];
  onFinished: () => void;
  onAbort: () => void;
}

const SPEEDS = [1, 2, 4, 8];

export function Play({ spec, config, frames, onFinished, onAbort }: Props) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(2);
  const residual = useRef(new Float32Array(config.grid * config.grid));
  const memory = useRef(new Float32Array(config.grid * config.grid).fill(-1));
  const belief = useRef(new Float32Array(config.grid * config.grid).fill(-1));
  const trails = useRef<Map<number, { x: number; y: number }[]>>(new Map());
  const [agentView, setAgentView] = useState(true);
  const [, bump] = useState(0);

  const frame = frames[index];

  useEffect(() => {
    residual.current = new Float32Array(config.grid * config.grid);
    memory.current = new Float32Array(config.grid * config.grid).fill(-1);
    belief.current = new Float32Array(config.grid * config.grid).fill(-1);
    trails.current = new Map();
    if (frames[0]?.residual) applyFull(frames[0].residual, residual.current);
    setIndex(0);
    setPlaying(true);
  }, [frames, config.grid]);

  useEffect(() => {
    if (!frame) return;
    if (frame.residual) applyFull(frame.residual, residual.current);
    if (frame.t === 0 && frame.episode > 0) {
      for (let i = 0; i < memory.current.length; i += 1) {
        if (belief.current[i] >= 0) memory.current[i] = belief.current[i];
      }
    }
    for (const cell of frame.dirty) {
      residual.current[cell.y * config.grid + cell.x] = cell.v;
    }
    for (const agent of frame.agents) {
      reveal(memory.current, belief.current, residual.current, config.grid, agent.x, agent.y, config.vision);
      const list = trails.current.get(agent.id) ?? [];
      const last = list[list.length - 1];
      if (!last || last.x !== agent.x || last.y !== agent.y) {
        const next = frame.t === 0 ? [{ x: agent.x, y: agent.y }] : [...list, { x: agent.x, y: agent.y }];
        trails.current.set(agent.id, next.slice(-80));
      }
    }
    bump((n) => n + 1);
  }, [frame, config.grid, config.vision]);

  useEffect(() => {
    if (!playing || !frames.length) return;
    const id = window.setInterval(() => {
      setIndex((i) => {
        if (i >= frames.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, Math.max(12, 80 / speed));
    return () => window.clearInterval(id);
  }, [playing, frames.length, speed]);

  const agents: FrameAgent[] = frame?.agents ?? [];
  const trailList = useMemo(
    () => Array.from(trails.current.entries()).map(([id, points]) => ({ id, points })),
    [index],
  );

  if (!frame) return <p className="error">No replay frames.</p>;

  return (
    <div className="play">
      <aside className="hud">
        <button type="button" className="text-btn" onClick={onAbort}>
          New mission
        </button>
        <div className="stat">
          <span>Episode</span>
          <strong>
            {frame.episode + 1} / 5
          </strong>
        </div>
        <div className="stat">
          <span>Step</span>
          <strong>
            {frame.t} / {config.steps}
          </strong>
        </div>
        <div className="stat">
          <span>Map</span>
          <strong>
            {frame.landscape_class} {frame.triplet_id + 1}
          </strong>
        </div>
        {agents.map((agent, i) => (
          <div key={agent.id} className={i === 0 ? "stat teal" : "stat orange"}>
            <span>{agent.type}</span>
            <strong>{agent.score.toFixed(2)}</strong>
            <em>{agent.seen} seen</em>
          </div>
        ))}
        <div className="stat">
          <span>Constraint</span>
          <strong>{frame.constraint_ok ? "held" : "broke"}</strong>
        </div>
        <div className="controls">
          <button type="button" onClick={() => setPlaying((p) => !p)}>
            {playing ? "Pause" : "Play"}
          </button>
          <button
            type="button"
            onClick={() => {
              setPlaying(false);
              setIndex((i) => Math.min(frames.length - 1, i + 1));
            }}
          >
            Step
          </button>
          <button
            type="button"
            onClick={() => {
              setIndex(frames.length - 1);
              setPlaying(false);
              onFinished();
            }}
          >
            Skip
          </button>
        </div>
        <div className="speeds">
          {SPEEDS.map((s) => (
            <button key={s} type="button" className={speed === s ? "on" : ""} onClick={() => setSpeed(s)}>
              {s}×
            </button>
          ))}
        </div>
        <button type="button" className={agentView ? "on" : ""} onClick={() => setAgentView((v) => !v)}>
          {agentView ? "Agent memory" : "True map"}
        </button>
        {index === frames.length - 1 && (
          <button type="button" className="begin" onClick={onFinished}>
            Debrief
          </button>
        )}
      </aside>
      <div className="stage">
        <GridCanvas
          residual={agentView ? memory.current : residual.current}
          grid={config.grid}
          agents={agents}
          trails={trailList}
          condition={spec.condition}
          vision={config.vision}
          attractR={config.attract_r}
          avoidR={config.avoid_r}
        />
      </div>
    </div>
  );
}

function reveal(
  memory: Float32Array,
  belief: Float32Array,
  residual: Float32Array,
  grid: number,
  x: number,
  y: number,
  radius: number,
) {
  const x0 = Math.max(0, x - radius);
  const x1 = Math.min(grid, x + radius + 1);
  const y0 = Math.max(0, y - radius);
  const y1 = Math.min(grid, y + radius + 1);
  for (let yy = y0; yy < y1; yy += 1) {
    for (let xx = x0; xx < x1; xx += 1) {
      const i = yy * grid + xx;
      const value = residual[i];
      memory[i] = value;
      if (value > 0 || belief[i] < 0) belief[i] = value;
    }
  }
}

function applyFull(src: number[][], dest: Float32Array) {
  let i = 0;
  for (const row of src) {
    for (const v of row) {
      dest[i] = v;
      i += 1;
    }
  }
}
