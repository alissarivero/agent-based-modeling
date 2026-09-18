import { useMemo, useState } from "react";
import { missionCsvUrl } from "../api";
import { GridCanvas } from "../components/GridCanvas";
import type { MissionSpec, SessionDebrief, SimConfig } from "../types";

interface Props {
  spec: MissionSpec;
  config: SimConfig;
  debrief: SessionDebrief;
  onReplay: () => void;
  onNew: () => void;
}

export function Debrief({ spec, config, debrief, onReplay, onNew }: Props) {
  const [episodeIndex, setEpisodeIndex] = useState(0);
  const episode = debrief.episodes[Math.min(episodeIndex, debrief.episodes.length - 1)];
  const residual = useMemo(() => {
    const out = new Float32Array(config.grid * config.grid);
    const src = episode.original ?? debrief.episodes[0].original;
    if (src) {
      let i = 0;
      for (const row of src) {
        for (const v of row) {
          out[i] = v;
          i += 1;
        }
      }
    }
    return out;
  }, [episode, debrief.episodes, config.grid]);

  const overlay = episode.agents.map((agent, i) => ({
    color: i === 0 ? "#3db8a6" : "#e07a3d",
    points: agent.path,
  }));

  return (
    <div className="debrief">
      <header className="mast">
        <div>
          <p className="kicker">After-action</p>
          <h1>Debrief</h1>
        </div>
        <p className="lede">
          {debrief.agent_a}
          {debrief.agent_b ? ` + ${debrief.agent_b}` : ""} · {debrief.condition.replaceAll("_", " ")} ·{" "}
          {debrief.scheduler === "repeat_five" ? "same grid 5×" : "each grid"} · seed {debrief.seed}
        </p>
      </header>

      <div className="score-strip">
        {debrief.episodes.map((ep, i) => (
          <button
            key={ep.episode}
            type="button"
            className={i === episodeIndex ? "score-card on" : "score-card"}
            onClick={() => setEpisodeIndex(i)}
          >
            <span>
              Ep {ep.episode + 1}
              {debrief.scheduler === "each_grid" ? ` · grid ${ep.triplet_id + 1}` : ""}
            </span>
            <strong>{ep.agents[0].reward.toFixed(2)}</strong>
            {ep.agents[1] && <em>partner {ep.agents[1].reward.toFixed(2)}</em>}
          </button>
        ))}
        {debrief.learning_gain !== null && (
          <div className="score-card gain">
            <span>Episode 1 → last</span>
            <strong>
              {debrief.learning_gain >= 0 ? "+" : ""}
              {debrief.learning_gain.toFixed(2)}
            </strong>
          </div>
        )}
      </div>

      <div className="debrief-grid">
        <div className="stage">
          <GridCanvas
            residual={residual}
            grid={config.grid}
            agents={[]}
            trails={[]}
            condition={spec.condition}
            vision={config.vision}
            attractR={config.attract_r}
            avoidR={config.avoid_r}
            overlayPaths={overlay}
          />
        </div>
        <table className="metrics">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Reward</th>
              <th>Visited</th>
              <th>High-value</th>
              <th>Seen</th>
            </tr>
          </thead>
          <tbody>
            {episode.agents.map((agent) => (
              <tr key={agent.agent_id}>
                <td>
                  {agent.role} · {agent.agent_type}
                </td>
                <td>{agent.reward.toFixed(3)}</td>
                <td>{agent.cells_visited}</td>
                <td>
                  {agent.high_value_cleared} / {episode.high_value_total}
                </td>
                <td>{agent.cells_seen}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="caption">
        Remaining {episode.remaining_reward.toFixed(1)} of {episode.total_reward_available.toFixed(1)} · high-value
        cleared on map {episode.high_value_cleared} · constraint violations {episode.constraint_violations}
        {episode.mean_pairwise_distance !== null
          ? ` · mean distance ${episode.mean_pairwise_distance.toFixed(2)}`
          : ""}
      </p>

      <div className="toolbar">
        <button type="button" onClick={onReplay}>
          Replay
        </button>
        <button type="button" onClick={onNew}>
          New mission
        </button>
        <a className="begin" href={missionCsvUrl(debrief.run_id)}>
          Download CSV
        </a>
        <button
          type="button"
          onClick={() => navigator.clipboard.writeText(String(debrief.seed))}
        >
          Copy seed
        </button>
      </div>
    </div>
  );
}
