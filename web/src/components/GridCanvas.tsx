import { useEffect, useRef } from "react";
import { paintHeatmap } from "../colormap";
import type { FrameAgent, SocialCondition } from "../types";

interface Trail {
  id: number;
  points: { x: number; y: number }[];
}

interface Props {
  residual: Float32Array;
  grid: number;
  agents: FrameAgent[];
  trails: Trail[];
  condition: SocialCondition;
  vision: number;
  attractR: number;
  avoidR: number;
  overlayPaths?: { color: string; points: [number, number][] }[];
}

const AGENT_COLORS = ["#3db8a6", "#e07a3d"];

export function GridCanvas({
  residual,
  grid,
  agents,
  trails,
  condition,
  vision,
  attractR,
  avoidR,
  overlayPaths,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    const avail = Math.min(parent?.clientWidth ?? 720, parent?.clientHeight ?? 720);
    const cell = Math.max(2, Math.floor(avail / grid));
    const size = cell * grid;
    if (canvas.width !== size) {
      canvas.width = size;
      canvas.height = size;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const image = ctx.createImageData(size, size);
    paintHeatmap(image, residual, grid, cell);
    ctx.putImageData(image, 0, 0);

    const toPx = (x: number, y: number) => ({
      px: x * cell + cell / 2,
      py: y * cell + cell / 2,
    });

    if (overlayPaths) {
      for (const path of overlayPaths) {
        if (path.points.length < 2) continue;
        ctx.beginPath();
        ctx.strokeStyle = path.color;
        ctx.globalAlpha = 0.75;
        ctx.lineWidth = Math.max(1, cell * 0.35);
        path.points.forEach(([x, y], i) => {
          const { px, py } = toPx(x, y);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    }

    for (const trail of trails) {
      if (trail.points.length < 2) continue;
      ctx.beginPath();
      ctx.strokeStyle = AGENT_COLORS[trail.id % AGENT_COLORS.length];
      ctx.globalAlpha = 0.45;
      ctx.lineWidth = Math.max(1, cell * 0.28);
      trail.points.forEach((p, i) => {
        const { px, py } = toPx(p.x, p.y);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    for (const agent of agents) {
      const color = AGENT_COLORS[agent.id % AGENT_COLORS.length];
      const { px, py } = toPx(agent.x, agent.y);
      const half = (vision + 0.5) * cell;
      ctx.strokeStyle = color;
      ctx.globalAlpha = 0.55;
      ctx.lineWidth = 1;
      ctx.strokeRect(px - half, py - half, half * 2, half * 2);
      ctx.globalAlpha = 1;
    }

    if (agents.length === 2) {
      const a = toPx(agents[0].x, agents[0].y);
      const b = toPx(agents[1].x, agents[1].y);
      if (condition.includes("attract")) {
        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = "#e8b86d";
        ctx.lineWidth = 1.5;
        ctx.moveTo(a.px, a.py);
        ctx.lineTo(b.px, b.py);
        ctx.stroke();
        const tether = (attractR + 0.5) * cell;
        ctx.strokeRect(a.px - tether, a.py - tether, tether * 2, tether * 2);
        ctx.setLineDash([]);
      }
      if (condition.includes("avoid")) {
        const r = (avoidR + 0.5) * cell;
        ctx.setLineDash([3, 5]);
        ctx.strokeStyle = "rgba(232, 184, 109, 0.7)";
        ctx.beginPath();
        ctx.arc(a.px, a.py, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(b.px, b.py, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    for (const agent of agents) {
      const color = AGENT_COLORS[agent.id % AGENT_COLORS.length];
      const { px, py } = toPx(agent.x, agent.y);
      ctx.beginPath();
      ctx.fillStyle = color;
      ctx.arc(px, py, Math.max(2.5, cell * 0.55), 0, Math.PI * 2);
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = "#12141a";
      ctx.stroke();
    }

  }, [residual, grid, agents, trails, condition, vision, attractR, avoidR, overlayPaths]);

  return <canvas ref={canvasRef} className="grid-canvas" />;
}
