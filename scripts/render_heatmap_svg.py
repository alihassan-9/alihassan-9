#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day calendar of rounded, colored boxes, animated as a
diagonal, line-after-line slide-down that plays once on load.

Usage:
    python scripts/render_heatmap_svg.py
Writes:
    contrib-heatmap.svg
"""
import json
import datetime

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end, since GitHub itself only
# goes to level 4 -- this bumps the very best day for visual pop)

CELL = 11
GAP = 3
LEFT_PAD = 28     # room for day-of-week labels
TOP_PAD = 24      # room for month labels
BG = "#0d1117"
TEXT = "#8b949e"
FONT = "Menlo, Consolas, monospace"
STAGGER = 0.012   # seconds between diagonal bands
SLIDE_DUR = 0.30

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # sparse labels, GitHub-style


def load_weeks(days):
    """Group the flat day list into GitHub's week columns (Sun-start)."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []
    start = datetime.date.fromisoformat(days[0]["date"])
    end = datetime.date.fromisoformat(days[-1]["date"])

    # Back up to the preceding Sunday so week columns align like GitHub's grid.
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        entry = by_date.get(cur.isoformat(), {"date": cur.isoformat(), "level": 0, "count": 0})
        week.append(entry)
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += datetime.timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append({"date": None, "level": 0, "count": 0})
        weeks.append(week)
    return weeks


def cap_level(entry, max_count):
    """Bump the single best day to a level-5 neon accent for visual pop."""
    if max_count > 0 and entry["count"] == max_count and entry["count"] > 0:
        return 5
    return min(entry.get("level", 0), 4)


def build_svg(data: dict, out_path: str = "contrib-heatmap.svg"):
    days = data["days"]
    stats = data["stats"]
    weeks = load_weeks(days)
    n_weeks = len(weeks)

    max_count = stats.get("best_day", {}).get("count", 0)

    grid_w = n_weeks * (CELL + GAP)
    grid_h = 7 * (CELL + GAP)
    width = LEFT_PAD + grid_w + 10
    height = TOP_PAD + grid_h + 56  # + legend/footer band

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{FONT}">'
    )
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{BG}" rx="10"/>')

    # Month labels along the top -- print once per month at the week column
    # where that month first appears.
    seen_months = set()
    for w_idx, week in enumerate(weeks):
        for entry in week:
            if not entry["date"]:
                continue
            d = datetime.date.fromisoformat(entry["date"])
            key = (d.year, d.month)
            if key not in seen_months and d.day <= 7:
                seen_months.add(key)
                x = LEFT_PAD + w_idx * (CELL + GAP)
                parts.append(
                    f'<text x="{x}" y="14" fill="{TEXT}" font-size="10">{MONTH_ABBR[d.month - 1]}</text>'
                )
            break

    # Day-of-week labels down the left side.
    for row, label in DOW_LABELS.items():
        y = TOP_PAD + row * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="0" y="{y}" fill="{TEXT}" font-size="9">{label}</text>')

    # Diagonal stagger: band index = week + day, so cells slide in on
    # anti-diagonals top-left -> bottom-right instead of column by column.
    for w_idx, week in enumerate(weeks):
        for d_idx, entry in enumerate(week):
            level = cap_level(entry, max_count)
            color = PALETTE[level]
            x = LEFT_PAD + w_idx * (CELL + GAP)
            y = TOP_PAD + d_idx * (CELL + GAP)
            band = w_idx + d_idx
            begin = band * STAGGER
            title = entry["date"] or ""
            count = entry["count"]

            parts.append(
                f'<rect x="{x}" y="{y - 6}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{color}" opacity="0">'
                f'<title>{count} contribution{"s" if count != 1 else ""} on {title}</title>'
                f'<animate attributeName="y" from="{y - 6}" to="{y}" begin="{begin:.3f}s" '
                f'dur="{SLIDE_DUR}s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>'
                f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" '
                f'dur="{SLIDE_DUR}s" fill="freeze"/>'
                f'</rect>'
            )

    # Legend: Less -> More
    legend_y = TOP_PAD + grid_h + 22
    legend_x = LEFT_PAD
    parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" fill="{TEXT}" font-size="10">Less</text>')
    lx = legend_x + 32
    for color in PALETTE[:5]:  # legend shows the standard 0-4 scale
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 8}" fill="{TEXT}" font-size="10">More</text>')

    # Stats footer
    total = stats.get("total_contributions", 0)
    streak = stats.get("longest_streak", 0)
    footer_y = legend_y + 24
    parts.append(
        f'<text x="{legend_x}" y="{footer_y}" fill="{TEXT}" font-size="11">'
        f'{total} contributions in the last year * longest streak {streak} days</text>'
    )

    parts.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path} ({width}x{height}, {n_weeks} weeks)")


if __name__ == "__main__":
    with open("data/contributions.json") as f:
        data = json.load(f)
    build_svg(data)
