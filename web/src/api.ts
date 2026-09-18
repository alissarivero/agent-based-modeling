import type {
  BatchSummaryRow,
  Frame,
  LandscapeItem,
  MissionSpec,
  SessionDebrief,
  SimConfig,
} from "./types";

export async function fetchConfig(): Promise<SimConfig> {
  const res = await fetch("/api/config");
  if (!res.ok) throw new Error("Could not load config");
  return res.json();
}

export async function fetchLandscapes(): Promise<LandscapeItem[]> {
  const res = await fetch("/api/landscapes");
  if (!res.ok) throw new Error("Could not load landscapes");
  const data = await res.json();
  return data.items;
}

export async function createMission(spec: MissionSpec): Promise<{
  run_id: string;
  debrief: SessionDebrief;
  n_frames: number;
}> {
  const res = await fetch("/api/missions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(spec),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || "Mission failed");
  }
  return res.json();
}

export async function fetchReplay(runId: string): Promise<Frame[]> {
  const res = await fetch(`/api/missions/${runId}/replay`);
  if (!res.ok) throw new Error("Could not load replay");
  const data = await res.json();
  return data.frames;
}

export function missionCsvUrl(runId: string): string {
  return `/api/missions/${runId}/csv`;
}

export async function startBatch(body: Record<string, unknown>): Promise<{
  job_id: string;
  total: number;
}> {
  const res = await fetch("/api/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchBatch(jobId: string): Promise<{
  job_id: string;
  status: string;
  done: number;
  total: number;
  error: string | null;
  n_rows: number;
  summary: BatchSummaryRow[];
}> {
  const res = await fetch(`/api/batch/${jobId}`);
  if (!res.ok) throw new Error("Batch not found");
  return res.json();
}

export function batchCsvUrl(jobId: string): string {
  return `/api/batch/${jobId}/csv`;
}
