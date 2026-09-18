import { useEffect, useState } from "react";
import { createMission, fetchConfig, fetchLandscapes, fetchReplay } from "./api";
import { Debrief } from "./pages/Debrief";
import { Lab } from "./pages/Lab";
import { Play } from "./pages/Play";
import { Setup } from "./pages/Setup";
import type { Frame, LandscapeItem, MissionSpec, SessionDebrief, SimConfig } from "./types";

type View = "setup" | "play" | "debrief" | "lab";

const DEFAULT_SPEC: MissionSpec = {
  landscape_class: "smooth",
  triplet_id: 2,
  condition: "solo",
  agent_a: "searcher",
  agent_b: null,
  scheduler: "repeat_five",
  seed: 1,
};

export function App() {
  const [view, setView] = useState<View>("setup");
  const [spec, setSpec] = useState<MissionSpec>(DEFAULT_SPEC);
  const [config, setConfig] = useState<SimConfig | null>(null);
  const [landscapes, setLandscapes] = useState<LandscapeItem[]>([]);
  const [debrief, setDebrief] = useState<SessionDebrief | null>(null);
  const [frames, setFrames] = useState<Frame[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig().then(setConfig).catch((err) => setError(String(err)));
    fetchLandscapes().then(setLandscapes).catch((err) => setError(String(err)));
  }, []);

  async function begin() {
    setBusy(true);
    setError(null);
    try {
      const created = await createMission(spec);
      const replay = await fetchReplay(created.run_id);
      setDebrief(created.debrief);
      setFrames(replay);
      setView("play");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run mission");
    } finally {
      setBusy(false);
    }
  }

  if (!config) {
    return (
      <div className="boot">
        <p>{error ?? "Loading Forage Lab…"}</p>
      </div>
    );
  }

  return (
    <div className="app">
      <nav>
        <button type="button" className={view !== "lab" ? "on" : ""} onClick={() => setView("setup")}>
          Mission
        </button>
        <button type="button" className={view === "lab" ? "on" : ""} onClick={() => setView("lab")}>
          Lab
        </button>
      </nav>
      {view === "setup" && (
        <Setup landscapes={landscapes} spec={spec} onChange={setSpec} onBegin={begin} busy={busy} error={error} />
      )}
      {view === "play" && frames.length > 0 && (
        <Play spec={spec} config={config} frames={frames} onFinished={() => setView("debrief")} onAbort={() => setView("setup")} />
      )}
      {view === "debrief" && debrief && (
        <Debrief spec={spec} config={config} debrief={debrief} onReplay={() => setView("play")} onNew={() => setView("setup")} />
      )}
      {view === "lab" && <Lab onBack={() => setView("setup")} />}
    </div>
  );
}
