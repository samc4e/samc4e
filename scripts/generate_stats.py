#!/usr/bin/env python3
"""Renders assets/stats.svg from live GitHub data. Runs daily in .github/workflows/stats.yml.

Local run: GITHUB_TOKEN=<token> python3 scripts/generate_stats.py
"""
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_hero  # noqa: E402

LOGIN = "samc4e"
HIDE_LANGS = {"C++"}  # kept out of the language breakdown, as on the old card
HEAT_WEEKS = 24
SHORT_NAMES = {"Jupyter Notebook": "Jupyter"}

P, LIGHT, PALE = "#9953EA", "#C79DF1", "#ECDDFD"
LANG_SHADES = ["#ECDDFD", "#C79DF1", "#A66BEE", "#8B4FE0", "#6E1FA3", "#4C1D95"]
HEAT = ["#1E1230", "#6230B0", "#8B4FE0", "#B98AF4", "#E4D0FD"]  # ramp validated against the card surface
LINE = "#A66BEE"
SANS = '-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,Consolas,"DejaVu Sans Mono",monospace'

LC_QUERY = """
query($u: String!) {
  matchedUser(username: $u) {
    profile { ranking }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    userCalendar { streak totalActiveDays }
  }
}
"""

QUERY = """
query($login: String!, $merged: String!, $opened: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
  merged: search(query: $merged, type: ISSUE) { issueCount }
  opened: search(query: $opened, type: ISSUE) { issueCount }
}
"""


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {
        "login": LOGIN, "merged": f"is:pr is:merged author:{LOGIN} -user:{LOGIN}",
        "opened": f"is:pr author:{LOGIN} -user:{LOGIN}"}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if res.get("errors"):
        raise SystemExit(f"GraphQL error: {res['errors']}")
    d = res["data"]
    langs = Counter()
    for repo in d["user"]["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
    cal = d["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(x["date"], x["contributionCount"]) for w in cal["weeks"] for x in w["contributionDays"]]
    return {"total": cal["totalContributions"], "days": days, "langs": langs,
            "merged": d["merged"]["issueCount"], "opened": d["opened"]["issueCount"]}


def fetch_leetcode():
    body = json.dumps({"query": LC_QUERY, "variables": {"u": build_hero.LEETCODE_USER}}).encode()
    req = urllib.request.Request("https://leetcode.com/graphql", data=body, headers={
        "Content-Type": "application/json", "Referer": "https://leetcode.com", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        u = json.load(r)["data"]["matchedUser"]
    solved = {x["difficulty"]: x["count"] for x in u["submitStatsGlobal"]["acSubmissionNum"]}
    return {"solved": solved["All"], "Easy": solved["Easy"], "Medium": solved["Medium"], "Hard": solved["Hard"],
            "ranking": u["profile"]["ranking"], "streak": u["userCalendar"]["streak"],
            "active_days": u["userCalendar"]["totalActiveDays"]}


def streaks(days):
    counts = [c for _, c in sorted(days)]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    if counts and counts[-1] == 0:  # today not counted yet: don't break the streak
        counts = counts[:-1]
    current = 0
    for c in reversed(counts):
        if not c:
            break
        current += 1
    return current, longest


def calendar_weeks(days):
    """Day counts grouped into Sunday-first weeks, as GitHub's calendar does; None pads the first week."""
    days = sorted(days)
    pad = (date.fromisoformat(days[0][0]).weekday() + 1) % 7
    cells = [None] * pad + [c for _, c in days]
    return [cells[i:i + 7] for i in range(0, len(cells), 7)]


def tiles(data):
    current, longest = streaks(data["days"])
    items = [
        (data["total"], "CONTRIBUTIONS 1Y"),
        (data["merged"], "MERGED PRs"),
        (data["opened"], "PRs OPENED"),
        (f"{current}d", f"STREAK · MAX {longest}d"),
    ]
    out = []
    for i, (val, label) in enumerate(items):
        x, y = 28 + (i % 2) * 156, 58 + (i // 2) * 86
        out.append(
            f'<g><rect x="{x}" y="{y}" width="146" height="76" rx="11" fill="{P}" fill-opacity="0.08" stroke="{P}" stroke-opacity="0.3"/>'
            f'<rect x="{x}" y="{y + 16}" width="3" height="26" rx="1.5" fill="{P}"/>'
            f'<text x="{x + 16}" y="{y + 40}" font-size="29" font-weight="800" fill="{PALE}">{escape(str(val))}</text>'
            f'<text x="{x + 16}" y="{y + 61}" font-family=\'{MONO}\' font-size="9.5" letter-spacing="1.2" fill="{LIGHT}" fill-opacity="0.7">{escape(label)}</text></g>')
    return "\n".join(out)


def heatmap(data):
    weeks = calendar_weeks(data["days"])[-HEAT_WEEKS:]
    nonzero = sorted(c for w in weeks for c in w if c)
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)] if nonzero else [1, 2, 3]

    def level(c):
        return 0 if not c else 1 + sum(c > k for k in cuts)

    x0, y0, s = 356, 82, 12.6
    out = [f'<text x="{x0}" y="70" font-size="11" font-family=\'{MONO}\' letter-spacing="2.5" font-weight="700" fill="{PALE}">ACTIVITY · {HEAT_WEEKS} WEEKS</text>']
    for wi, w in enumerate(weeks):
        for di, c in enumerate(w):
            if c is None:
                continue
            out.append(f'<rect x="{x0 + wi * s:.1f}" y="{y0 + di * s:.1f}" width="10" height="10" rx="2.2" fill="{HEAT[level(c)]}"/>')
    ly = y0 + 7 * s + 22
    out.append(f'<text x="{x0}" y="{ly + 9}" font-size="10" fill="{LIGHT}" fill-opacity="0.65">less</text>')
    for i, col in enumerate(HEAT):
        out.append(f'<rect x="{x0 + 34 + i * 13}" y="{ly}" width="10" height="10" rx="2.2" fill="{col}"/>')
    out.append(f'<text x="{x0 + 34 + 5 * 13 + 4}" y="{ly + 9}" font-size="10" fill="{LIGHT}" fill-opacity="0.65">more</text>')
    active = sum(1 for w in weeks for c in w if c)
    out.append(f'<text x="{x0 + HEAT_WEEKS * s - 2.6:.1f}" y="{ly + 9}" text-anchor="end" font-size="10" fill="{LIGHT}" fill-opacity="0.65">{active} active days</text>')
    return "\n".join(out)


def languages(data):
    langs = [(n, b) for n, b in data["langs"].most_common() if n not in HIDE_LANGS]
    top = langs[:6]
    total = sum(b for _, b in langs) or 1
    x0, w = 696, 276
    out = [f'<text x="{x0}" y="70" font-size="11" font-family=\'{MONO}\' letter-spacing="2.5" font-weight="700" fill="{PALE}">TOP LANGUAGES</text>',
           f'<clipPath id="bar"><rect x="{x0}" y="84" width="{w}" height="10" rx="5"/></clipPath>',
           f'<rect x="{x0}" y="84" width="{w}" height="10" rx="5" fill="#1E1230"/><g clip-path="url(#bar)">']
    x = x0
    for i, (name, b) in enumerate(top):
        seg = w * b / total
        out.append(f'<rect x="{x:.1f}" y="84" width="{seg + 0.5:.1f}" height="10" fill="{LANG_SHADES[i]}"/>')
        x += seg
    out.append("</g>")
    for i, (name, b) in enumerate(top):
        cx, cy = x0 + (i % 2) * 142, 122 + (i // 2) * 30
        out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{LANG_SHADES[i]}"/>'
                   f'<text x="{cx + 16}" y="{cy}" font-size="12.5" fill="{PALE}">{escape(SHORT_NAMES.get(name, name))}'
                   f'<tspan fill="{LIGHT}" fill-opacity="0.6" font-size="11"> {100 * b / total:.1f}%</tspan></text>')
    return "\n".join(out)


def trend(data):
    """Single-series area chart of weekly contributions over the last 52 weeks."""
    weeks = calendar_weeks(data["days"])[-52:]
    first = date.fromisoformat(sorted(data["days"])[-1][0]) - timedelta(days=(len(weeks) - 1) * 7)
    first -= timedelta(days=(first.weekday() + 1) % 7)
    totals = [sum(c or 0 for c in w) for w in weeks]
    peak = max(totals) or 1
    step = max(1, -(-peak // 2))  # two gridline steps above zero, rounded to a whole number
    top = step * 2
    x0, x1, y0, y1 = 318, 968, 62, 162
    dx = (x1 - x0) / (len(totals) - 1)
    pts = [(x0 + i * dx, y1 - (y1 - y0) * t / top) for i, t in enumerate(totals)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    out = []
    for v in (0, step, top):
        gy = y1 - (y1 - y0) * v / top
        out.append(f'<path d="M{x0} {gy:.1f}H{x1}" stroke="{LIGHT}" stroke-opacity="{0.22 if v == 0 else 0.08}"/>'
                   f'<text x="{x0 - 10}" y="{gy + 3.5:.1f}" text-anchor="end" font-size="10" fill="{LIGHT}" fill-opacity="0.55">{v}</text>')
    last_x = -99
    for i in range(len(weeks)):
        d = first + timedelta(days=7 * i)
        prev = first + timedelta(days=7 * (i - 1))
        x = x0 + i * dx
        if (i == 0 or d.month != prev.month) and x - last_x > 44 and x < x1 - 20:
            out.append(f'<text x="{x:.1f}" y="{y1 + 20}" font-size="10" fill="{LIGHT}" fill-opacity="0.55">{d.strftime("%b")}</text>')
            last_x = x
    out.append(f'<path d="{line} L{x1} {y1} L{x0} {y1}Z" fill="url(#area)"/>')
    out.append(f'<path d="{line}" fill="none" stroke="{LINE}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    pi = totals.index(max(totals))
    px, py = pts[pi]
    anchor = "end" if px > x1 - 60 else "start" if px < x0 + 60 else "middle"
    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{LINE}" stroke="#120920" stroke-width="2"/>'
               f'<text x="{px:.1f}" y="{py - 10:.1f}" text-anchor="{anchor}" font-size="10.5" font-weight="700" fill="{PALE}">peak {max(totals)}</text>')
    lx, ly = pts[-1]
    out.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="{PALE}" stroke="#120920" stroke-width="2"/>')

    active_weeks = sum(1 for t in totals if t)
    side = [(max(totals), "BEST WEEK"), (f"{sum(totals) / len(totals):.1f}", "WEEKLY AVERAGE"),
            (f"{active_weeks}/{len(totals)}", "ACTIVE WEEKS")]
    for i, (val, label) in enumerate(side):
        y = 72 + i * 42
        out.append(f'<text x="28" y="{y}" font-size="22" font-weight="800" fill="{PALE}">{val}</text>'
                   f'<text x="28" y="{y + 16}" font-family=\'{MONO}\' font-size="9.5" letter-spacing="1.2" fill="{LIGHT}" fill-opacity="0.7">{label}</text>')
    out.append(f'<path d="M250 58v134" stroke="{P}" stroke-opacity="0.18" stroke-dasharray="3 5"/>')
    return "\n".join(out)


def card(h, title, aside, body, label):
    """Shared frame for every generated card: surface, glow, hairline border, header row."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {h}" width="1000" height="{h}" role="img" aria-label="{escape(label)}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#140A22"/><stop offset="1" stop-color="#0A0612"/></linearGradient>
  <radialGradient id="glow"><stop offset="0" stop-color="{P}" stop-opacity="0.32"/><stop offset="1" stop-color="{P}" stop-opacity="0"/></radialGradient>
  <linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{LINE}" stop-opacity="0.4"/><stop offset="1" stop-color="{LINE}" stop-opacity="0"/></linearGradient>
  <clipPath id="card"><rect x="1" y="1" width="998" height="{h - 2}" rx="20"/></clipPath>
</defs>
<g font-family='{SANS}'>
<g clip-path="url(#card)">
  <rect width="1000" height="{h}" fill="url(#bg)"/>
  <circle cx="520" cy="0" r="320" fill="url(#glow)"/>
</g>
<rect x="1" y="1" width="998" height="{h - 2}" rx="20" fill="none" stroke="{P}" stroke-opacity="0.3" stroke-width="1.5"/>
<rect x="28" y="22" width="4" height="14" rx="2" fill="{P}"/>
<text x="44" y="33.5" font-family='{MONO}' font-size="11.5" letter-spacing="3.5" fill="{LIGHT}" fill-opacity="0.8">{title}</text>
<text x="972" y="33.5" text-anchor="end" font-family='{MONO}' font-size="10.5" letter-spacing="1" fill="{LIGHT}" fill-opacity="0.5">{aside}</text>
{body}
</g>
</svg>
'''


def render(data, updated):
    body = (f'<path d="M336 58v162M672 58v162" stroke="{P}" stroke-opacity="0.18" stroke-dasharray="3 5"/>\n'
            f'{tiles(data)}\n{heatmap(data)}\n{languages(data)}')
    return card(240, f'GITHUB.COM/{LOGIN.upper()} <tspan fill-opacity="0.5">· LIVE STATS</tspan>', f"auto-updated {updated}", body,
                f'GitHub stats for {LOGIN}: {data["total"]} contributions in the last year, {data["merged"]} merged pull requests')


def render_activity(data):
    weeks = calendar_weeks(data["days"])[-52:]
    total = sum(c or 0 for w in weeks for c in w)
    return card(210, 'CONTRIBUTION TREND <tspan fill-opacity="0.5">· WEEKLY, LAST 52 WEEKS</tspan>',
                f"{total} contributions", trend(data),
                f"Weekly contributions over the last 52 weeks for {LOGIN}, {total} in total")


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN")
    data = fetch(token)
    assets = Path(__file__).resolve().parent.parent / "assets"
    (assets / "stats.svg").write_text(render(data, datetime.now(timezone.utc).strftime("%d %b %Y")), encoding="utf-8")
    (assets / "activity.svg").write_text(render_activity(data), encoding="utf-8")
    cache = assets / "leetcode.json"
    try:
        lc = fetch_leetcode()
        cache.write_text(json.dumps(lc, indent=2) + "\n", encoding="utf-8")
    except Exception as e:  # LeetCode has no official API; keep the last good numbers
        print(f"LeetCode fetch failed, using cached stats: {e}")
        lc = json.loads(cache.read_text())
    build_hero.write(lc)
    print(f"wrote hero.svg, stats.svg, activity.svg: {data['total']} contributions, {data['merged']} merged PRs")


if __name__ == "__main__":
    main()
