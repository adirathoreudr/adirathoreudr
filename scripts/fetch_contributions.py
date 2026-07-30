#!/usr/bin/env python3
"""Fetch the real contribution calendar - no token needed.

GitHub serves the contribution calendar as public HTML at
https://github.com/users/<username>/contributions - the same fragment
the profile page itself uses. Parse the day cells and write
data/contributions.json with raw days plus derived stats.

Run:  python scripts/fetch_contributions.py
"""
import datetime as dt
import json
import re

import requests
from bs4 import BeautifulSoup

USERNAME = "adirathoreudr"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = "data/contributions.json"


def fetch_days() -> list[dict]:
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (profile-art)"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # counts live in <tool-tip for="<cell id>"> "N contributions on ..."
    tips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        m = re.match(r"(\d+|No)\b", tip.get_text(strip=True))
        if target and m:
            tips[target] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        date = cell["data-date"]
        level = int(cell.get("data-level", 0))
        count = tips.get(cell.get("id"))
        if count is None:
            # fallback: some markup variants inline the text in the cell
            m = re.match(r"(\d+|No)\b", cell.get_text(strip=True))
            count = 0 if not m or m.group(1) == "No" else int(m.group(1))
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no day cells parsed - did GitHub change the markup?")
    return days


def derive_stats(days: list[dict]) -> dict:
    counts = [d["count"] for d in days]
    total = sum(counts)

    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)

    current = 0
    trailing = counts[:-1] if counts and counts[-1] == 0 else counts
    for c in reversed(trailing):        # today being 0 doesn't break the streak
        if c == 0:
            break
        current += 1

    best = max(days, key=lambda d: d["count"])
    monthly: dict[str, int] = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main() -> None:
    days = fetch_days()
    payload = {
        "user": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "days": days,
        "stats": derive_stats(days),
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"wrote {OUT}: {len(days)} days, {payload['stats']['total']} contributions")


if __name__ == "__main__":
    main()
