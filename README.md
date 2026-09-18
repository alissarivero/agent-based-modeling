# Forage Lab

A discrete-space, discrete-time agent-based foraging model plus a browser lab UI. Built for a full factorial of **strategy × landscape class × social condition × schedule**, with frozen match-paired maps so a paper can regenerate every figure from a seed.

This repository does **not** claim to fit human or animal data. It is a methods-and-results platform.

## Model (v1)

- 110×110 grid, rewards in `[0, 1]`, collect-and-deplete, 200 steps, 8-neighbor Chebyshev moves, vision radius 7.
- Three strategies: **searcher** (cover cells ≥ 0.7), **maximizer** (`value / distance`), **random**.
- Five social rules: solo; same/different type tether (distance ≤ 2); same/different type avoid (distance ≥ 5).
- Five match-paired triplets (smooth / rough / random) that share an **identical value multiset**. Only spatial clustering changes.
- Two schedules: same grid five times, or each of the five grids once.
- **Memory:** episode 1 is fully obscure. Agents write values into memory only when a cell enters vision. They keep that last-grid memory on later episodes and are **never told** that resources refilled or that the map changed.

Details: [docs/ODD.md](docs/ODD.md).

## Run

From the repository root:

```bash
python3 -m pip install -e ".[dev]"
python3 -m sim                 # write data/landscapes/*.npz + checksums
python3 -m pytest
uvicorn api.main:app --reload --port 8000
```

In another terminal:

```bash
cd web && npm install && npm run dev
```

Open http://127.0.0.1:5173 — Mission for a live run, Lab for a factorial batch and CSV export.

## Reproducibility

- Landscape seed `20260918` (see `data/landscapes/manifest.json` SHA-256).
- Every session logs `run_id`, mission spec, and seed. Same seed replays the same paths.
- Tidy CSV columns: `run_id, seed, landscape_class, triplet_id, condition, scheduler, agent_type, role, episode, reward, ...`
