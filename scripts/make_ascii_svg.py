#!/usr/bin/env python3
"""
make_ascii_svg.py — convert source-prepped.png into a self-typing,
monochrome ASCII-art SVG.

Usage:
    python scripts/make_ascii_svg.py
Writes:
    ali-ascii.svg
"""
import html
from PIL import Image

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense); leading space clears bg to nothing
GRID_W = 100             # characters wide
CELL_W = 6.6             # px per character cell (monospace)
CELL_H = 12.0            # px per row
FONT_SIZE = 12
FILL = "#8b949e"         # single monochrome fill — no rainbow coloring
BG = "#0d1117"           # terminal-dark background baked into the SVG
STAGGER = 0.028          # seconds between each row starting its wipe
WIPE_DUR = 0.35          # seconds for a single row to fully type in


def image_to_ascii_rows(path: str, grid_w: int = GRID_W):
    img = Image.open(path).convert("L")
    w, h = img.size
    # Correct for monospace character cells being taller than wide so the
    # portrait doesn't look squashed.
    grid_h = max(1, int(h * (grid_w / w) * (CELL_W / CELL_H)))
    img = img.resize((grid_w, grid_h))
    pixels = list(img.getdata())

    ramp_len = len(RAMP)
    rows = []
    for y in range(grid_h):
        row_chars = []
        for x in range(grid_w):
            brightness = pixels[y * grid_w + x]  # 0=black .. 255=white
            idx = int((255 - brightness) / 256 * ramp_len)
            idx = max(0, min(ramp_len - 1, idx))
            row_chars.append(RAMP[idx])
        rows.append("".join(row_chars))
    return rows


def build_svg(rows, out_path: str = "ali-ascii.svg"):
    grid_h = len(rows)
    width = GRID_W * CELL_W
    height = grid_h * CELL_H
    total_duration = STAGGER * grid_h + WIPE_DUR

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.0f}" height="{height:.0f}" font-family="Menlo, Consolas, monospace">'
    )
    parts.append(f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="{BG}" rx="10"/>')

    defs = ["<defs>"]
    rows_svg = []
    for i, row_text in enumerate(rows):
        escaped = html.escape(row_text) if row_text.strip() else "&#160;"
        clip_id = f"clip{i}"
        y_baseline = (i + 1) * CELL_H - 2
        begin = i * STAGGER

        # Clip rect that wipes from 0 width to full width -> "typing" reveal.
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{i * CELL_H:.1f}" width="0" height="{CELL_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{width:.1f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze" calcMode="linear"/>'
            f'</rect></clipPath>'
        )

        rows_svg.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{y_baseline:.1f}" fill="{FILL}" font-size="{FONT_SIZE}" '
            f'xml:space="preserve">{escaped}</text>'
            f'</g>'
        )

        # Small block cursor riding the wipe edge, disappears once the row finishes.
        rows_svg.append(
            f'<rect x="0" y="{i * CELL_H + 1:.1f}" width="{CELL_W - 1:.1f}" height="{CELL_H - 3:.1f}" '
            f'fill="{FILL}" opacity="0">'
            f'<animate attributeName="x" from="0" to="{width - CELL_W:.1f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze" calcMode="linear"/>'
            f'<animate attributeName="opacity" values="0;0.85;0.85;0" keyTimes="0;0.01;0.9;1" '
            f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze"/>'
            f'</rect>'
        )
    defs.append("</defs>")

    parts.extend(defs)
    parts.extend(rows_svg)
    parts.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path} ({width:.0f}x{height:.0f}, {grid_h} rows, total anim ~{total_duration:.2f}s)")


if __name__ == "__main__":
    rows = image_to_ascii_rows("source-prepped.png")
    build_svg(rows)
