from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from sim.config import DEFAULT_CONFIG, LandscapeClass, SimConfig

LANDSCAPE_CLASSES = (
    LandscapeClass.smooth,
    LandscapeClass.rough,
    LandscapeClass.random,
)


def landscape_filename(triplet_id: int, landscape_class: LandscapeClass) -> str:
    return f"triplet{triplet_id}_{landscape_class.value}.npz"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def draw_shared_values(n: int, mean: float, rng: np.random.Generator, concentration: float) -> np.ndarray:
    alpha = max(mean * concentration, 1e-6)
    beta = max((1.0 - mean) * concentration, 1e-6)
    return rng.beta(alpha, beta, size=n).astype(np.float64)


def structured_field(shape: tuple[int, int], sigma: float, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(shape)
    if sigma <= 0:
        return noise
    return gaussian_filter(noise, sigma=sigma, mode="reflect")


def assign_by_rank(values_flat: np.ndarray, field: np.ndarray) -> np.ndarray:
    out = np.empty(field.shape, dtype=np.float64)
    order = np.argsort(field, axis=None, kind="mergesort")
    out.reshape(-1)[order] = np.sort(values_flat)
    return out


def generate_triplet(
    triplet_id: int,
    config: SimConfig | None = None,
) -> dict[LandscapeClass, np.ndarray]:
    cfg = config or DEFAULT_CONFIG
    if triplet_id < 0 or triplet_id >= cfg.n_triplets:
        raise ValueError(f"triplet_id must be in 0..{cfg.n_triplets - 1}")
    mean = cfg.density_means[triplet_id]
    rng = np.random.default_rng(cfg.landscape_seed + 1009 * (triplet_id + 1))
    values = draw_shared_values(cfg.grid * cfg.grid, mean, rng, cfg.beta_concentration)
    smooth_field = structured_field((cfg.grid, cfg.grid), cfg.grf_smooth_sigma, rng)
    rough_field = structured_field((cfg.grid, cfg.grid), cfg.grf_rough_sigma, rng)
    smooth = assign_by_rank(values, smooth_field)
    rough = assign_by_rank(values, rough_field)
    random_map = values.copy()
    rng.shuffle(random_map)
    random_map = random_map.reshape(cfg.grid, cfg.grid)
    return {
        LandscapeClass.smooth: smooth,
        LandscapeClass.rough: rough,
        LandscapeClass.random: random_map,
    }


def generate_library(config: SimConfig | None = None, force: bool = False) -> dict:
    cfg = config or DEFAULT_CONFIG
    out_dir = Path(cfg.data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    for triplet_id in range(cfg.n_triplets):
        maps = generate_triplet(triplet_id, cfg)
        for landscape_class, grid in maps.items():
            name = landscape_filename(triplet_id, landscape_class)
            path = out_dir / name
            if path.exists() and not force:
                files[name] = sha256_file(path)
                continue
            np.savez_compressed(
                path,
                values=grid,
                triplet_id=np.int32(triplet_id),
                landscape_class=np.asarray(landscape_class.value),
                density_mean=np.float64(cfg.density_means[triplet_id]),
                grid=np.int32(cfg.grid),
                landscape_seed=np.int32(cfg.landscape_seed),
            )
            files[name] = sha256_file(path)
    manifest = {
        "grid": cfg.grid,
        "n_triplets": cfg.n_triplets,
        "density_means": list(cfg.density_means),
        "landscape_seed": cfg.landscape_seed,
        "grf_smooth_sigma": cfg.grf_smooth_sigma,
        "grf_rough_sigma": cfg.grf_rough_sigma,
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_manifest(config: SimConfig | None = None) -> dict:
    cfg = config or DEFAULT_CONFIG
    path = Path(cfg.data_dir) / "manifest.json"
    if not path.exists():
        return generate_library(cfg)
    return json.loads(path.read_text(encoding="utf-8"))


def load_landscape(
    triplet_id: int,
    landscape_class: LandscapeClass,
    config: SimConfig | None = None,
) -> np.ndarray:
    cfg = config or DEFAULT_CONFIG
    path = Path(cfg.data_dir) / landscape_filename(triplet_id, landscape_class)
    if not path.exists():
        generate_library(cfg)
    with np.load(path) as data:
        return np.asarray(data["values"], dtype=np.float64)


def list_landscapes(config: SimConfig | None = None) -> list[dict]:
    cfg = config or DEFAULT_CONFIG
    manifest = load_manifest(cfg)
    items = []
    for triplet_id in range(cfg.n_triplets):
        for landscape_class in LANDSCAPE_CLASSES:
            grid = load_landscape(triplet_id, landscape_class, cfg)
            items.append(
                {
                    "triplet_id": triplet_id,
                    "landscape_class": landscape_class.value,
                    "density_mean": float(cfg.density_means[triplet_id]),
                    "actual_mean": float(grid.mean()),
                    "total_reward": float(grid.sum()),
                    "preview": downsample(grid, 36),
                }
            )
    manifest["count"] = len(items)
    return items


def downsample(grid: np.ndarray, size: int) -> list[list[float]]:
    h, w = grid.shape
    ys = np.linspace(0, h, size + 1).astype(int)
    xs = np.linspace(0, w, size + 1).astype(int)
    preview = []
    for i in range(size):
        row = []
        for j in range(size):
            block = grid[ys[i] : max(ys[i] + 1, ys[i + 1]), xs[j] : max(xs[j] + 1, xs[j + 1])]
            row.append(round(float(block.mean()), 5))
        preview.append(row)
    return preview


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate match-paired landscape library")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    manifest = generate_library(force=args.force)
    print(json.dumps({k: manifest[k] for k in ("grid", "n_triplets", "landscape_seed")}, indent=2))
    print(f"Wrote {len(manifest['files'])} landscapes")


if __name__ == "__main__":
    main()
