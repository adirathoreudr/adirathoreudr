#!/usr/bin/env python3
"""Render a streak card from data/contributions.json - a self-hosted
replacement for third-party streak badges that rate-limit or die with a
broken image on the profile.

Three columns: total contributions, current streak (in a ring that draws
itself), longest streak. Regenerated daily by the same Actions cron that
refreshes the heatmap. STATIC=1 emits a frozen frame for previews.

Run:  python scripts/make_streak_card.py   # writes streak-card.svg
"""
import datetime as dt
import json
import math
import os

SRC = "data/contributions.json"
OUT = "streak-card.svg"
STATIC = os.environ.get("STATIC") == "1"

WIDTH, HEIGHT = 640, 208
BAR_H = 28

BG = "#0d1117"
BORDER = "#30363d"
GREEN = "#00ff41"
INK = "#c9d1d9"
DIM = "#8b949e"
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Menlo,Consolas,monospace"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt(date_str: str) -> str:
    d = dt.date.fromisoformat(date_str)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def fmt_short(date_str: str) -> str:
    d = dt.date.fromisoformat(date_str)
    return f"{MONTHS[d.month - 1]} {d.day}"


def streaks(days: list[dict]) -> tuple[dict, dict]:
    """Return (current, longest) streaks with their date ranges."""
    longest = {"len": 0, "start": None, "end": None}
    run_start = None
    run_len = 0
    for d in days:
        if d["count"] > 0:
            run_start = run_start or d["date"]
            run_len += 1
            if run_len > longest["len"]:
                longest = {"len": run_len, "start": run_start, "end": d["date"]}
        else:
            run_start, run_len = None, 0

    trailing = days[:-1] if days and days[-1]["count"] == 0 else days
    cur_len = 0
    cur_start = None
    for d in reversed(trailing):        # today being 0 doesn't break the streak
        if d["count"] == 0:
            break
        cur_len += 1
        cur_start = d["date"]
    current = {"len": cur_len, "start": cur_start,
               "end": trailing[-1]["date"] if cur_len else None}
    return current, longest


def appear(inner: str, begin: float) -> str:
    if STATIC:
        return f"<g>{inner}</g>"
    return (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{begin:.2f}s" dur="0.5s" fill="freeze"/>{inner}</g>'
    )


def main() -> None:
    with open(SRC) as f:
        data = json.load(f)
    days = data["days"]
    total = sum(d["count"] for d in days)
    current, longest = streaks(days)

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{FONT}">'
    )
    out.append(f'<rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{BG}" stroke="{BORDER}"/>')
    out.append(f'<line x1="1" y1="{BAR_H}" x2="{WIDTH - 1}" y2="{BAR_H}" stroke="{BORDER}"/>')
    for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 18}" cy="{BAR_H // 2}" r="5" fill="{dot}"/>')
    out.append(
        f'<text x="{WIDTH // 2}" y="{BAR_H // 2 + 4}" text-anchor="middle" '
        f'font-size="13" fill="{DIM}">adi@github: ~/streak</text>'
    )

    cy = BAR_H + (HEIGHT - BAR_H) // 2
    cols = [WIDTH // 6, WIDTH // 2, 5 * WIDTH // 6]
    for x in (WIDTH // 3, 2 * WIDTH // 3):
        out.append(
            f'<line x1="{x}" y1="{BAR_H + 22}" x2="{x}" y2="{HEIGHT - 22}" stroke="{BORDER}"/>'
        )

    # total contributions
    first_active = next((d["date"] for d in days if d["count"] > 0), days[0]["date"])
    out.append(appear(
        f'<text x="{cols[0]}" y="{cy - 4}" text-anchor="middle" font-size="34" '
        f'font-weight="bold" fill="{INK}">{total:,}</text>'
        f'<text x="{cols[0]}" y="{cy + 24}" text-anchor="middle" font-size="13" '
        f'fill="{INK}">Total Contributions</text>'
        f'<text x="{cols[0]}" y="{cy + 44}" text-anchor="middle" font-size="10" '
        f'fill="{DIM}">{fmt(first_active)} — Present</text>', 0.2))

    # current streak inside a ring that draws itself
    r = 46
    circ = 2 * math.pi * r
    ring_anim = "" if STATIC else (
        f'<animate attributeName="stroke-dashoffset" from="{circ:.1f}" to="0" '
        f'begin="0.55s" dur="1.1s" fill="freeze" calcMode="spline" '
        f'keySplines="0.25 0.1 0.25 1"/>'
    )
    cur_range = (f"{fmt_short(current['start'])} — {fmt_short(current['end'])}"
                 if current["len"] else "—")
    out.append(appear(
        f'<circle cx="{cols[1]}" cy="{cy - 6}" r="{r}" fill="none" '
        f'stroke="{BORDER}" stroke-width="5"/>'
        f'<circle cx="{cols[1]}" cy="{cy - 6}" r="{r}" fill="none" stroke="{GREEN}" '
        f'stroke-width="5" stroke-linecap="round" stroke-dasharray="{circ:.1f}" '
        f'stroke-dashoffset="{0 if STATIC else circ:.1f}" '
        f'transform="rotate(-90 {cols[1]} {cy - 6})">{ring_anim}</circle>'
        f'<text x="{cols[1]}" y="{cy + 5}" text-anchor="middle" font-size="34" '
        f'font-weight="bold" fill="{GREEN}">{current["len"]}</text>'
        f'<text x="{cols[1]}" y="{cy + 58}" text-anchor="middle" font-size="13" '
        f'fill="{GREEN}">Current Streak</text>'
        f'<text x="{cols[1]}" y="{cy + 76}" text-anchor="middle" font-size="10" '
        f'fill="{DIM}">{cur_range}</text>', 0.45))

    # longest streak
    long_range = (f"{fmt_short(longest['start'])} — {fmt_short(longest['end'])}"
                  if longest["len"] else "—")
    out.append(appear(
        f'<text x="{cols[2]}" y="{cy - 4}" text-anchor="middle" font-size="34" '
        f'font-weight="bold" fill="{INK}">{longest["len"]}</text>'
        f'<text x="{cols[2]}" y="{cy + 24}" text-anchor="middle" font-size="13" '
        f'fill="{INK}">Longest Streak</text>'
        f'<text x="{cols[2]}" y="{cy + 44}" text-anchor="middle" font-size="10" '
        f'fill="{DIM}">{long_range}</text>', 0.7))

    out.append("</svg>")
    svg = "\n".join(out)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({WIDTH}x{HEIGHT}{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
