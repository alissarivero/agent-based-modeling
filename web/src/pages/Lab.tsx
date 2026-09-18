import { useEffect, useState } from "react";
import { batchCsvUrl, fetchBatch, startBatch } from "../api";
import type { AgentType, BatchSummaryRow, LandscapeClass, SchedulerKind, SocialCondition } from "../types";

const CLASSES: LandscapeClass[] = ["smooth", "rough", "random"];
const CONDITIONS: SocialCondition[] = [
  "solo",
  "same_attract",
  "diff_attract",
  "same_avoid",
  "diff_avoid",
];
const AGENTS: AgentType[] = ["searcher", "maximizer", "random"];
const SCHEDULERS: SchedulerKind[] = ["repeat_five", "each_grid"];

interface Props {
  onBack: () => void;
}

export function Lab({ onBack }: Props) {
  const [classes, setClasses] = useState<LandscapeClass[]>(["smooth", "rough", "random"]);
  const [conditions, setConditions] = useState<SocialCondition[]>(["solo"]);
  const [agents, setAgents] = useState<AgentType[]>(["searcher", "maximizer", "random"]);
  const [schedulers, setSchedulers] = useState<SchedulerKind[]>(["repeat_five"]);
  const [nSeeds, setNSeeds] = useState(1);
  const [baseSeed, setBaseSeed] = useState(1000);
  const [jobId, setJobId] = useState<string | null>(null);
  const [done, setDone] = useState(0);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("idle");
  const [summary, setSummary] = useState<BatchSummaryRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!jobId || (status !== "running" && status !== "idle")) return;
    const id = window.setInterval(async () => {
      const job = await fetchBatch(jobId);
      setDone(job.done);
      setTotal(job.total);
      setStatus(job.status);
      setSummary(job.summary);
      setError(job.error);
      if (job.status !== "running") window.clearInterval(id);
    }, 600);
    return () => window.clearInterval(id);
  }, [jobId, status]);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const job = await startBatch({
        landscape_classes: classes,
        conditions,
        agent_types: agents,
        schedulers,
        triplet_ids: [0, 1, 2, 3, 4],
        n_seeds: nSeeds,
        base_seed: baseSeed,
      });
      setJobId(job.job_id);
      setTotal(job.total);
      setDone(0);
      setStatus("running");
      setSummary([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch failed");
    } finally {
      setBusy(false);
    }
  }

  const maxReward = Math.max(0.01, ...summary.map((row) => row.reward));

  return (
    <div className="lab">
      <header className="mast">
        <div>
          <p className="kicker">Factorial runner</p>
          <h1>Lab</h1>
        </div>
        <button type="button" className="text-btn" onClick={onBack}>
          Back to missions
        </button>
      </header>

      <div className="lab-factors">
        <Factor label="Landscapes" values={CLASSES} selected={classes} onChange={setClasses} />
        <Factor label="Conditions" values={CONDITIONS} selected={conditions} onChange={setConditions} />
        <Factor label="Strategies" values={AGENTS} selected={agents} onChange={setAgents} />
        <Factor label="Schedulers" values={SCHEDULERS} selected={schedulers} onChange={setSchedulers} />
      </div>

      <div className="toolbar">
        <label className="seed">
          Seeds
          <input type="number" min={1} value={nSeeds} onChange={(e) => setNSeeds(Number(e.target.value) || 1)} />
        </label>
        <label className="seed">
          Base seed
          <input type="number" value={baseSeed} onChange={(e) => setBaseSeed(Number(e.target.value) || 1)} />
        </label>
        <button type="button" className="begin" onClick={run} disabled={busy || !classes.length}>
          {busy ? "Starting…" : "Run batch"}
        </button>
        {jobId && status === "done" && (
          <a className="begin" href={batchCsvUrl(jobId)}>
            Download CSV
          </a>
        )}
      </div>

      {total > 0 && (
        <div className="progress">
          <div className="bar" style={{ width: `${total ? (100 * done) / total : 0}%` }} />
          <span>
            {done} / {total} sessions · {status}
          </span>
        </div>
      )}
      {error && <p className="error">{error}</p>}

      {summary.length > 0 && (
        <div className="bars">
          {summary.map((row) => (
            <div key={`${row.agent_type}-${row.landscape_class}-${row.condition}-${row.scheduler}`} className="bar-row">
              <span>
                {row.agent_type} · {row.landscape_class} · {row.condition} · {row.scheduler}
              </span>
              <i style={{ width: `${(100 * row.reward) / maxReward}%` }} />
              <em>{row.reward.toFixed(2)}</em>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Factor<T extends string>({
  label,
  values,
  selected,
  onChange,
}: {
  label: string;
  values: T[];
  selected: T[];
  onChange: (next: T[]) => void;
}) {
  return (
    <fieldset>
      <legend>{label}</legend>
      {values.map((value) => (
        <label key={value}>
          <input
            type="checkbox"
            checked={selected.includes(value)}
            onChange={(e) => {
              if (e.target.checked) onChange([...selected, value]);
              else onChange(selected.filter((item) => item !== value));
            }}
          />
          {value.replaceAll("_", " ")}
        </label>
      ))}
    </fieldset>
  );
}
