import { useEffect, useRef } from "react";
import { viridis } from "../colormap";

export function PreviewMap({ preview, selected }: { preview: number[][]; selected?: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !preview.length) return;
    const n = preview.length;
    canvas.width = n;
    canvas.height = n;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const image = ctx.createImageData(n, n);
    for (let y = 0; y < n; y += 1) {
      for (let x = 0; x < n; x += 1) {
        const [r, g, b] = viridis(preview[y][x]);
        const i = (y * n + x) * 4;
        image.data[i] = r;
        image.data[i + 1] = g;
        image.data[i + 2] = b;
        image.data[i + 3] = 255;
      }
    }
    ctx.putImageData(image, 0, 0);
  }, [preview]);
  return <canvas ref={ref} className={selected ? "preview selected" : "preview"} />;
}
