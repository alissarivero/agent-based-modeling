from __future__ import annotations

import numpy as np


class GridWorld:
    def __init__(self, original: np.ndarray):
        self.original = np.asarray(original, dtype=np.float64)
        self.residual = self.original.copy()
        self.grid = int(self.original.shape[0])
        self.dirty: list[tuple[int, int, float]] = []

    def reset(self) -> None:
        self.residual = self.original.copy()
        self.dirty = []

    def collect(self, x: int, y: int) -> float:
        value = float(self.residual[y, x])
        if value != 0.0:
            self.residual[y, x] = 0.0
            self.dirty.append((x, y, 0.0))
        return value

    def vision_window(self, x: int, y: int, radius: int) -> tuple[int, int, int, int]:
        x0 = max(0, x - radius)
        x1 = min(self.grid, x + radius + 1)
        y0 = max(0, y - radius)
        y1 = min(self.grid, y + radius + 1)
        return x0, x1, y0, y1

    def high_value_mask(self, tau: float) -> np.ndarray:
        return self.original >= tau

    def take_dirty(self) -> list[tuple[int, int, float]]:
        dirty = self.dirty
        self.dirty = []
        return dirty
