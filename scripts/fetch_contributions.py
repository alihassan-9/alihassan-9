#!/usr/bin/env python3
"""
fetch_contributions.py — scrape the public contributions calendar for a
GitHub username. No GraphQL API, no personal access token required.

Usage:
    python scripts/fetch_contributions.py <username>
Writes:
    data/contributions.json
"""
import re
import sys
import json
import datetime
import requests
from bs4 import BeautifulSoup

URL_TMPL = "https://github.com/users/{username}/contributions"

# Tooltip text looks like "No contributions on July 27th." or
# "4 contributions on June 5th." or "1 contribution on May 2nd."
COUNT_RE = re.compile(r"^(No|\d+)\s+contribution")


def parse_tooltip_count(text: str) -> int:
    text = text.strip()
    match = COUNT_RE.match(text)
    if not match:
        return 0
    token = match.group(1)
    return 0 if token == "No" else int(token)


def fetch(username: str) -> dict:
    resp = requests.get(
        URL_TMPL.format(username=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Current GitHub markup: each day is a <td class="ContributionCalendar-day">
    # with data-date/data-level, but the actual count lives in a sibling
    # <tool-tip for="<td id>"> element's text, not a data-count attribute.
    tooltip_by_id = {}
    for tip in soup.select("tool-tip"):
        target_id = tip.get("for")
        if target_id:
            tooltip_by_id[target_id] = tip.get_text()

    days = []
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        cells = soup.select("rect.ContributionCalendar-day")

    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")
        if date is None:
            continue
        count = 0
        count_attr = cell.get("data-count")
        if count_attr is not None:
            count = int(count_attr)
        else:
            tip_text = tooltip_by_id.get(cell.get("id"), "")
            count = parse_tooltip_count(tip_text)
        days.append({
            "date": date,
            "level": int(level) if level is not None else 0,
            "count": count,
        })

    days.sort(key=lambda d: d["date"])
    stats = compute_stats(days)
    return {
        "username": username,
        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }


def compute_stats(days: list) -> dict:
    if not days:
        return {}

    total = sum(d["count"] for d in days)

    # Current streak: consecutive contributing days ending at the most recent day.
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Longest streak across the whole window.
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"])

    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": monthly,
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "alihassan-9"
    data = fetch(username)
    with open("data/contributions.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote data/contributions.json — {len(data['days'])} days, "
          f"{data['stats'].get('total_contributions', 0)} total contributions")
