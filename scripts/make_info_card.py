#!/usr/bin/env python3
"""Hand-author the neofetch-style info card SVG.

A title bar, then colored key/value rows - Now, Prev, Stack, Highlights.
The graph already covers the GitHub stats, so the card is for the story
numbers can't tell. Each line fades and slides in on a short stagger so
the panel looks like it's printing next to the portrait.

STATIC=1 emits a frozen frame for local previews.

Run:  python scripts/make_info_card.py   # writes info-card.svg
"""
import os

OUT = "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

WIDTH = 660
BAR_H = 28
PAD_X, PAD_Y = 18, 18
LINE_H = 22
FONT_SIZE = 13
KEY_W = 104

BG = "#0d1117"
BORDER = "#30363d"
GREEN = "#00ff41"      # accent - matches the rest of the profile
INK = "#c9d1d9"
DIM = "#8b949e"
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Menlo,Consolas,monospace"

T0 = 0.25              # s before the first line prints
STAGGER = 0.16         # s between lines
FADE = 0.45            # s per line

ROWS = [
    ("Role", "DevOps & AI Infrastructure Engineer"),
    ("Now", "Web3 rails · agentic AI infra · full-stack builds"),
    ("Prev", "freelance infra · contract builds · partnerships"),
    ("Stack", "TypeScript · Python · Rust · Solidity"),
    ("Infra", "AWS EKS · Terraform · Docker · K8s · ArgoCD"),
    ("AI", "LangChain · NVIDIA NIM · DeepSeek · agents"),
    ("Web3", "Solana · Anchor · Token-2022 · ZK Compression"),
    ("Highlights", "adiisingh.xyz — Vogue-inspired portfolio"),
    ("Open to", "remote Full Stack / Web3 / DevOps & MLOps"),
    ("Contact", "adirathoreudr@gmail.com · UTC+5:30 (IST)"),
]

PALETTE_BLOCKS = ["#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0",
                  "#00ff41", "#c9d1d9", "#8b949e"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def animated(inner: str, index: int) -> str:
    """Wrap a line so it fades and slides in on its stagger slot."""
    if STATIC:
        return f"<g>{inner}</g>"
    begin = T0 + index * STAGGER
    return (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{begin:.2f}s" dur="{FADE}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="-8 0" to="0 0" begin="{begin:.2f}s" dur="{FADE}s" fill="freeze"/>'
        f"{inner}</g>"
    )


def main() -> None:
    n_lines = 2 + len(ROWS)                      # header + separator + rows
    body_h = n_lines * LINE_H + 14 + 30          # + gap + palette strip
    height = BAR_H + PAD_Y + body_h + PAD_Y - 8

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="{FONT}" font-size="{FONT_SIZE}">'
    )
    out.append(f'<rect width="{WIDTH}" height="{height}" rx="8" fill="{BG}" stroke="{BORDER}"/>')
    out.append(f'<line x1="1" y1="{BAR_H}" x2="{WIDTH - 1}" y2="{BAR_H}" stroke="{BORDER}"/>')
    for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 18}" cy="{BAR_H // 2}" r="5" fill="{dot}"/>')
    out.append(
        f'<text x="{WIDTH // 2}" y="{BAR_H // 2 + 4}" text-anchor="middle" '
        f'fill="{DIM}">adi@github: ~</text>'
    )

    y = BAR_H + PAD_Y + LINE_H - 6
    idx = 0

    out.append(animated(
        f'<text x="{PAD_X}" y="{y}" fill="{GREEN}" font-weight="bold">adi@github</text>', idx))
    idx += 1
    y += LINE_H
    out.append(animated(
        f'<text x="{PAD_X}" y="{y}" fill="{DIM}">{esc("-" * 44)}</text>', idx))
    idx += 1

    for key, val in ROWS:
        y += LINE_H
        out.append(animated(
            f'<text x="{PAD_X}" y="{y}" fill="{GREEN}">{esc(key)}</text>'
            f'<text x="{PAD_X + KEY_W}" y="{y}" fill="{INK}">{esc(val)}</text>', idx))
        idx += 1

    # neofetch signature palette strip
    y += LINE_H + 8
    blocks = "".join(
        f'<rect x="{PAD_X + i * 26}" y="{y - 12}" width="22" height="16" rx="2" fill="{c}"/>'
        for i, c in enumerate(PALETTE_BLOCKS)
    )
    out.append(animated(blocks, idx))

    out.append("</svg>")
    svg = "\n".join(out)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({WIDTH}x{height}{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
