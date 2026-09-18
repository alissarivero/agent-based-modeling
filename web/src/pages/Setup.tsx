import { PreviewMap } from "../components/PreviewMap";
import type { AgentType, LandscapeClass, LandscapeItem, MissionSpec, SchedulerKind, SocialCondition } from "../types";

const AGENTS: { id: AgentType; title: string; copy: string }[] = [
  { id: "searcher", title: "Searcher", copy: "Clears every remembered high-value cell (≥ 0.7), nearest first." },
  { id: "maximizer", title: "Maximizer", copy: "Climbs value / distance. Will skip a 0.71 for a 0.95." },
  { id: "random", title: "Random", copy: "Uniform 8-neighbor walk. Still collects whatever it steps on." },
];

const CONDITIONS: { id: SocialCondition; title: string; copy: string; pair: "none" | "same" | "diff" }[] = [
  { id: "solo", title: "Solo", copy: "One agent. No spacing rule.", pair: "none" },
  { id: "same_attract", title: "Same-type tether", copy: "Two of the same type stay within 2 cells.", pair: "same" },
  { id: "diff_attract", title: "Mixed tether", copy: "Two different types stay within 2 cells.", pair: "diff" },
  { id: "same_avoid", title: "Same-type avoid", copy: "Two of the same type stay at least 5 apart.", pair: "same" },
  { id: "diff_avoid", title: "Mixed avoid", copy: "Two different types stay at least 5 apart.", pair: "diff" },
];

interface Props {
  landscapes: LandscapeItem[];
  spec: MissionSpec;
  onChange: (spec: MissionSpec) => void;
  onBegin: () => void;
  busy: boolean;
  error: string | null;
}

export function Setup({ landscapes, spec, onChange, onBegin, busy, error }: Props) {
  const condition = CONDITIONS.find((c) => c.id === spec.condition)!;
  const classes: LandscapeClass[] = ["smooth", "rough", "random"];
  const triplets = [0, 1, 2, 3, 4];

  function set<K extends keyof MissionSpec>(key: K, value: MissionSpec[K]) {
    const next = { ...spec, [key]: value };
    if (key === "condition") {
      const meta = CONDITIONS.find((c) => c.id === value)!;
      if (meta.pair === "none") next.agent_b = null;
      if (meta.pair === "same") next.agent_b = next.agent_a;
      if (meta.pair === "diff" && next.agent_b === next.agent_a) {
        next.agent_b = next.agent_a === "searcher" ? "maximizer" : "searcher";
      }
    }
    if (key === "agent_a" && condition.pair === "same") next.agent_b = value as AgentType;
    onChange(next);
  }

  return (
    <div className="setup">
      <header className="mast">
        <div>
          <p className="kicker">Experimental platform</p>
          <h1>Forage Lab</h1>
        </div>
        <p className="lede">
          Depleting 110×110 landscapes, local vision, three strategies, five social rules.
          Match-paired maps hold reward density constant so only spatial structure changes.
        </p>
      </header>

      <section>
        <div className="section-head">
          <h2>Landscape</h2>
          <span>Columns share the same values. Rows change clustering.</span>
        </div>
        <div className="gallery">
          <div className="gallery-corner" />
          {triplets.map((id) => (
            <div key={id} className="gallery-col">
              μ {landscapes.find((l) => l.triplet_id === id)?.density_mean.toFixed(2) ?? "—"}
            </div>
          ))}
          {classes.map((cls) => (
            <div key={cls} className="gallery-row">
              <div className="gallery-label">{cls}</div>
              {triplets.map((id) => {
                const item = landscapes.find((l) => l.triplet_id === id && l.landscape_class === cls);
                const selected = spec.landscape_class === cls && spec.triplet_id === id;
                return (
                  <button
                    key={`${cls}-${id}`}
                    className={selected ? "thumb on" : "thumb"}
                    onClick={() => onChange({ ...spec, landscape_class: cls, triplet_id: id })}
                    type="button"
                  >
                    {item ? <PreviewMap preview={item.preview} selected={selected} /> : <div className="preview" />}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </section>

      <section className="split">
        <div>
          <div className="section-head">
            <h2>Focal agent</h2>
          </div>
          <div className="cards">
            {AGENTS.map((agent) => (
              <button
                key={agent.id}
                type="button"
                className={spec.agent_a === agent.id ? "choice on" : "choice"}
                onClick={() => set("agent_a", agent.id)}
              >
                <strong>{agent.title}</strong>
                <span>{agent.copy}</span>
              </button>
            ))}
          </div>
        </div>
        {condition.pair !== "none" && (
          <div>
            <div className="section-head">
              <h2>{condition.pair === "same" ? "Partner (locked)" : "Partner"}</h2>
            </div>
            <div className="cards">
              {AGENTS.map((agent) => (
                <button
                  key={agent.id}
                  type="button"
                  disabled={condition.pair === "same" || (condition.pair === "diff" && agent.id === spec.agent_a)}
                  className={spec.agent_b === agent.id ? "choice on" : "choice"}
                  onClick={() => set("agent_b", agent.id)}
                >
                  <strong>{agent.title}</strong>
                  <span>{agent.copy}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      <section>
        <div className="section-head">
          <h2>Social rule</h2>
        </div>
        <div className="cards five">
          {CONDITIONS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={spec.condition === item.id ? "choice on" : "choice"}
              onClick={() => set("condition", item.id)}
            >
              <strong>{item.title}</strong>
              <span>{item.copy}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="toolbar">
        <div className="sched">
          <button
            type="button"
            className={spec.scheduler === "repeat_five" ? "choice on" : "choice"}
            onClick={() => set("scheduler", "repeat_five" as SchedulerKind)}
          >
            <strong>Same grid 5×</strong>
            <span>Resources refill. The agent is not told. Memory of the last grid stays.</span>
          </button>
          <button
            type="button"
            className={spec.scheduler === "each_grid" ? "choice on" : "choice"}
            onClick={() => set("scheduler", "each_grid")}
          >
            <strong>Each grid once</strong>
            <span>Five matched densities. Memory stays; the agent does not know the map changed.</span>
          </button>
        </div>
        <label className="seed">
          Seed
          <input
            type="number"
            value={spec.seed}
            onChange={(e) => set("seed", Number(e.target.value) || 1)}
          />
        </label>
        <button type="button" className="begin" onClick={onBegin} disabled={busy}>
          {busy ? "Running…" : "Begin mission"}
        </button>
      </section>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
