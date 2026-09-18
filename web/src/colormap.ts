/** Viridis-like LUT, sampled from the public colormap. */
const STOPS: [number, number, number][] = [
  [68, 1, 84],
  [72, 40, 120],
  [62, 74, 137],
  [49, 104, 142],
  [38, 130, 142],
  [31, 158, 137],
  [53, 183, 121],
  [109, 205, 89],
  [180, 222, 44],
  [253, 231, 37],
];

export function viridis(t: number): [number, number, number] {
  const x = Math.min(1, Math.max(0, t));
  const scaled = x * (STOPS.length - 1);
  const i = Math.min(STOPS.length - 2, Math.floor(scaled));
  const f = scaled - i;
  const a = STOPS[i];
  const b = STOPS[i + 1];
  return [
    Math.round(a[0] + (b[0] - a[0]) * f),
    Math.round(a[1] + (b[1] - a[1]) * f),
    Math.round(a[2] + (b[2] - a[2]) * f),
  ];
}

export function paintHeatmap(
  image: ImageData,
  residual: Float32Array,
  grid: number,
  cell: number,
): void {
  const { data, width } = image;
  data.fill(0);
  for (let y = 0; y < grid; y += 1) {
    for (let x = 0; x < grid; x += 1) {
      const value = residual[y * grid + x];
      const [r, g, b] = value < 0 ? [18, 20, 26] : viridis(value);
      const x0 = x * cell;
      const y0 = y * cell;
      for (let py = 0; py < cell; py += 1) {
        for (let px = 0; px < cell; px += 1) {
          const i = ((y0 + py) * width + (x0 + px)) * 4;
          data[i] = r;
          data[i + 1] = g;
          data[i + 2] = b;
          data[i + 3] = 255;
        }
      }
    }
  }
}
