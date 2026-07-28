#!/usr/bin/env python3
"""
make_info_card.py — a neofetch-style info panel that fades in line by line.

Set STATIC=1 to emit a frozen (non-animated) frame, useful for local
Quick Look previews where SMIL/CSS animation doesn't play.

Usage:
    python scripts/make_info_card.py
Writes:
    info-card.svg
"""
import os
import html

WIDTH = 490
BG = "#0d1117"
BORDER = "#30363d"
TITLE_BAR = "#161b22"
KEY_COLOR = "#7ee787"      # green key labels, like neofetch
VAL_COLOR = "#c9d1d9"
DIM_COLOR = "#8b949e"
FONT = "Menlo, Consolas, monospace"
LINE_H = 22
TOP_PAD = 46
LEFT_PAD = 20
STAGGER = 0.12
FADE_DUR = 0.35

STATIC = os.environ.get("STATIC") == "1"

# (key, value) rows — value can be a list for multi-line entries (e.g. Highlights)
ROWS = [
    ("Now", "Fresher AI/ML Engineer, open to roles"),
    ("Prev", "AI Contractor @ Turing"),
    ("Stack", "Python * LangChain/LangGraph * Google ADK"),
    ("", "FastAPI * Next.js * FAISS/RAG"),
    ("Highlights", "Axiom AI - neuro-symbolic invoice auditor"),
    ("", "Atlas - multi-agent orchestration system"),
    ("", "One Mix AI - sketch/prompt to UI generator"),
]


def esc(s: str) -> str:
    return html.escape(s)


def build_svg(out_path: str = "info-card.svg"):
    n_rows = len(ROWS)
    height = TOP_PAD + n_rows * LINE_H + 26

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="{FONT}">'
    )

    # Card frame
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>'
    )
    # Title bar
    parts.append(f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="30" rx="10" fill="{TITLE_BAR}"/>')
    parts.append(f'<rect x="0.5" y="20.5" width="{WIDTH - 1}" height="10" fill="{TITLE_BAR}"/>')
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{20 + i * 18}" cy="15.5" r="6" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2:.0f}" y="20" text-anchor="middle" fill="{DIM_COLOR}" '
        f'font-size="12">ali@github ~ %</text>'
    )

    # Header line: name + rule, styled like neofetch's user@host + separator
    header_y = TOP_PAD - 14
    parts.append(f'<text x="{LEFT_PAD}" y="{header_y}" fill="{VAL_COLOR}" font-size="13">'
                  f'<tspan fill="{KEY_COLOR}">ali</tspan>@github</text>')
    parts.append(
        f'<line x1="{LEFT_PAD}" y1="{header_y + 8}" x2="{WIDTH - LEFT_PAD}" y2="{header_y + 8}" '
        f'stroke="{BORDER}"/>'
    )

    key_col_w = 108
    for i, (key, value) in enumerate(ROWS):
        y = TOP_PAD + i * LINE_H + 14
        begin = i * STAGGER

        group_attrs = "" if STATIC else f' opacity="0"'
        parts.append(f'<g{group_attrs}>')
        if key:
            parts.append(
                f'<text x="{LEFT_PAD}" y="{y}" fill="{KEY_COLOR}" font-size="13">{esc(key)}</text>'
            )
        parts.append(
            f'<text x="{LEFT_PAD + key_col_w}" y="{y}" fill="{VAL_COLOR}" font-size="13">{esc(value)}</text>'
        )
        if not STATIC:
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" '
                f'dur="{FADE_DUR}s" fill="freeze"/>'
            )
        parts.append("</g>")

    parts.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path} ({WIDTH}x{height}, static={STATIC})")


if __name__ == "__main__":
    build_svg()
