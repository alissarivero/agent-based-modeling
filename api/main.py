from __future__ import annotations

import asyncio
import io
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sim.config import BatchSpec, DEFAULT_CONFIG, MissionSpec
from sim.experiment import expand_batch, run_batch
from sim.export import sessions_to_frame
from sim.landscapes import generate_library, list_landscapes, load_manifest
from sim.scheduler import run_session


@asynccontextmanager
async def lifespan(_app: FastAPI):
    generate_library(DEFAULT_CONFIG)
    yield


app = FastAPI(title="Forage Lab", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MISSIONS: dict[str, dict[str, Any]] = {}
BATCHES: dict[str, dict[str, Any]] = {}


def _debrief_payload(session) -> dict:
    payload = session.model_dump(mode="json")
    payload.pop("frames", None)
    return payload


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/config")
def config() -> dict:
    return DEFAULT_CONFIG.model_dump(mode="json")


@app.get("/api/landscapes")
def landscapes() -> dict:
    return {"manifest": load_manifest(), "items": list_landscapes()}


@app.post("/api/missions")
def create_mission(spec: MissionSpec) -> dict:
    session = run_session(spec, record_frames=True, include_original=True)
    MISSIONS[session.run_id] = {
        "spec": spec.model_dump(mode="json"),
        "session": session,
    }
    return {
        "run_id": session.run_id,
        "debrief": _debrief_payload(session),
        "n_frames": len(session.frames),
    }


@app.get("/api/missions/{run_id}")
def get_mission(run_id: str) -> dict:
    item = MISSIONS.get(run_id)
    if not item:
        raise HTTPException(404, "mission not found")
    return {"run_id": run_id, "debrief": _debrief_payload(item["session"])}


@app.get("/api/missions/{run_id}/replay")
def get_replay(run_id: str) -> dict:
    item = MISSIONS.get(run_id)
    if not item:
        raise HTTPException(404, "mission not found")
    session = item["session"]
    return {"run_id": run_id, "frames": session.frames}


@app.get("/api/missions/{run_id}/csv")
def mission_csv(run_id: str) -> StreamingResponse:
    item = MISSIONS.get(run_id)
    if not item:
        raise HTTPException(404, "mission not found")
    frame = sessions_to_frame([item["session"]])
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="mission-{run_id[:8]}.csv"'},
    )


@app.websocket("/api/ws/missions/{run_id}")
async def mission_ws(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    item = MISSIONS.get(run_id)
    if not item:
        await websocket.send_json({"error": "mission not found"})
        await websocket.close()
        return
    try:
        for frame in item["session"].frames:
            await websocket.send_json(frame)
            await asyncio.sleep(0)
        await websocket.send_json({"type": "end"})
    except WebSocketDisconnect:
        return


@app.post("/api/batch")
def start_batch(spec: BatchSpec) -> dict:
    missions = expand_batch(spec)
    job_id = f"batch-{len(BATCHES) + 1:04d}-{spec.base_seed}"
    BATCHES[job_id] = {
        "status": "running",
        "done": 0,
        "total": len(missions),
        "sessions": [],
        "error": None,
    }

    def worker() -> None:
        try:
            def progress(done: int, total: int, session) -> None:
                BATCHES[job_id]["done"] = done
                BATCHES[job_id]["total"] = total
                BATCHES[job_id]["sessions"].append(session)

            run_batch(spec, record_frames=False, progress=progress)
            BATCHES[job_id]["status"] = "done"
        except Exception as exc:  # pragma: no cover
            BATCHES[job_id]["status"] = "error"
            BATCHES[job_id]["error"] = str(exc)

    threading.Thread(target=worker, daemon=True).start()
    return {"job_id": job_id, "total": len(missions)}


@app.get("/api/batch/{job_id}")
def get_batch(job_id: str) -> dict:
    job = BATCHES.get(job_id)
    if not job:
        raise HTTPException(404, "batch not found")
    frame = sessions_to_frame(job["sessions"])
    summary = []
    if not frame.empty:
        grouped = (
            frame[frame["role"] == "focal"]
            .groupby(["agent_type", "landscape_class", "condition", "scheduler"], as_index=False)["reward"]
            .mean()
        )
        summary = grouped.to_dict(orient="records")
    return {
        "job_id": job_id,
        "status": job["status"],
        "done": job["done"],
        "total": job["total"],
        "error": job["error"],
        "n_rows": int(len(frame)),
        "summary": summary,
    }


@app.get("/api/batch/{job_id}/csv")
def batch_csv(job_id: str) -> StreamingResponse:
    job = BATCHES.get(job_id)
    if not job:
        raise HTTPException(404, "batch not found")
    frame = sessions_to_frame(job["sessions"])
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.csv"'},
    )
