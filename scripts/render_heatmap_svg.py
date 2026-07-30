#!/usr/bin/env python3
"""Render data/contributions.json as the classic 53-week x 7-day
calendar of rounded, colored boxes.

The grid reveals itself once with a diagonal, line-after-line slide-down
(CSS keyframes that play on load, then freeze - no looping glow), plus a
Less -> More legend and a stats footer. Output: contrib-heatmap.svg
"""
import datetime as dt
import json

SRC = "data/contributions.json"
OUT = "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

CELL, PITCH = 12, 15
PAD_X, PAD_Y = 16, 12
LABEL_W = 30           # Mon/Wed/Fri gutter
LABEL_H = 18           # month row
BAR_H = 28
FOOTER_H = 34

BG = "#0d1117"
BORDER = "#30363d"
DIM = "#8b949e"
GREEN = "#00ff41"
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Menlo,Consolas,monospace"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main() -> None:
    with open(SRC) as f:
        data = json.load(f)
    days, stats = data["days"], data["stats"]

    best = max((stats["best_day"]["count"], 1))
    neon_floor = max(4, int(best * 0.8))     # level 5: the standout days

    # lay out into week columns, Sunday first (GitHub convention)
    weeks: list[list[dict | None]] = []
    col: list[dict | None] = []
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        dow = (date.weekday() + 1) % 7       # Sunday = 0
        if dow == 0 and col:
            weeks.append(col)
            col = []
        while len(col) < dow:
            col.append(None)
        col.append(d)
    if col:
        weeks.append(col)
    weeks = weeks[-53:]

    grid_w = len(weeks) * PITCH
    grid_x = PAD_X + LABEL_W
    grid_y = BAR_H + PAD_Y + LABEL_H
    width = grid_x + grid_w + PAD_X - 3
    height = grid_y + 7 * PITCH + FOOTER_H

    reveal_done = 0.45 + (len(weeks) + 6) * 0.022    # last cell's delay + dur

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" font-size="11">'
    )
    out.append(
        "<style>"
        ".d{opacity:0;animation:drop .45s ease-out forwards}"
        "@keyframes drop{from{opacity:0;transform:translateY(-8px)}"
        "to{opacity:1;transform:none}}"
        f".f{{opacity:0;animation:fade .6s ease-out {reveal_done:.2f}s forwards}}"
        "@keyframes fade{to{opacity:1}}"
        "</style>"
    )
    out.append(f'<rect width="{width}" height="{height}" rx="8" fill="{BG}" stroke="{BORDER}"/>')
    out.append(f'<line x1="1" y1="{BAR_H}" x2="{width - 1}" y2="{BAR_H}" stroke="{BORDER}"/>')
    for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 18}" cy="{BAR_H // 2}" r="5" fill="{dot}"/>')
    out.append(
        f'<text x="{width // 2}" y="{BAR_H // 2 + 4}" text-anchor="middle" '
        f'fill="{DIM}">adi@github: ~/contributions --last-year</text>'
    )

    # month labels where the month changes (skip labels that would collide)
    seen = None
    last_x = -100.0
    for w, week in enumerate(weeks):
        first = next((d for d in week if d), None)
        if not first:
            continue
        month = dt.date.fromisoformat(first["date"]).month
        if month != seen:
            seen = month
            x = grid_x + w * PITCH
            if x - last_x >= 34:
                last_x = x
                out.append(
                    f'<text class="f" x="{x}" y="{grid_y - 6}" '
                    f'fill="{DIM}">{MONTHS[month - 1]}</text>'
                )

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        out.append(
            f'<text class="f" x="{PAD_X}" y="{grid_y + row * PITCH + CELL - 2}" '
            f'fill="{DIM}">{label}</text>'
        )

    # the grid, revealed diagonally line after line
    for w, week in enumerate(weeks):
        for d, day in enumerate(week):
            if day is None:
                continue
            level = day["level"]
            if day["count"] >= neon_floor and level >= 4:
                level = 5
            delay = (w + d) * 0.022
            out.append(
                f'<rect class="d" style="animation-delay:{delay:.3f}s" '
                f'x="{grid_x + w * PITCH}" y="{grid_y + d * PITCH}" '
                f'width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{PALETTE[min(level, 5)]}"/>'
            )

    # stats footer + Less -> More legend
    fy = grid_y + 7 * PITCH + 22
    total = stats["total"]
    footer = (
        f'{total:,} contributions in the last year'
        f' · streak {stats["current_streak"]}d (longest {stats["longest_streak"]}d)'
        f' · best day {stats["best_day"]["count"]}'
    )
    out.append(
        f'<text class="f" x="{grid_x}" y="{fy}" fill="{DIM}">'
        f'<tspan fill="{GREEN}">&#9656;</tspan> {footer}</text>'
    )

    lx = width - PAD_X - 6 * 17 - 76
    out.append(f'<text class="f" x="{lx - 34}" y="{fy}" fill="{DIM}">Less</text>')
    for i, c in enumerate(PALETTE):
        out.append(
            f'<rect class="f" x="{lx + i * 17}" y="{fy - 10}" width="{CELL}" '
            f'height="{CELL}" rx="3" fill="{c}"/>'
        )
    out.append(f'<text class="f" x="{lx + 6 * 17 + 6}" y="{fy}" fill="{DIM}">More</text>')

    out.append("</svg>")
    svg = "\n".join(out)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({width}x{height}, {len(svg) // 1024} KiB)")


if __name__ == "__main__":
    main()
