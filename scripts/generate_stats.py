#!/usr/bin/env python3
"""Renders assets/stats.svg from live GitHub data. Runs daily in .github/workflows/stats.yml.

Local run: GITHUB_TOKEN=<token> python3 scripts/generate_stats.py
"""
import json
import os
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = "samc4e"
HIDE_LANGS = {"C++"}  # kept out of the language breakdown, as on the old card
HEAT_WEEKS = 24
SHORT_NAMES = {"Jupyter Notebook": "Jupyter"}

P, LIGHT, PALE, HOT = "#9953EA", "#C79DF1", "#ECDDFD", "#D946EF"
LANG_SHADES = [PALE, LIGHT, P, HOT, "#7C3AED", "#5B21B6"]
HEAT = ["#1E1230", "#4C1D95", "#7C3AED", "#9953EA", "#D8B4FE"]
MONO = 'ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,Consolas,"DejaVu Sans Mono",monospace'

QUERY = """
query($login: String!, $merged: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
  merged: search(query: $merged, type: ISSUE, first: 100) {
    issueCount
    nodes { ... on PullRequest { repository { owner { login } } } }
  }
}
"""


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {
        "login": LOGIN, "merged": f"is:pr is:merged author:{LOGIN} -user:{LOGIN}"}}).encode()
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
    orgs = {n["repository"]["owner"]["login"] for n in d["merged"]["nodes"] if n}
    return {"total": cal["totalContributions"], "days": days, "langs": langs,
            "merged": d["merged"]["issueCount"], "orgs": len(orgs)}


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


def tiles(data):
    current, longest = streaks(data["days"])
    items = [
        (data["total"], "CONTRIBUTIONS 1Y"),
        (data["merged"], "MERGED PRs"),
        (data["orgs"], "OSS ORGS"),
        (f"{current}d", f"STREAK · MAX {longest}d"),
    ]
    out = []
    for i, (val, label) in enumerate(items):
        x, y = 28 + (i % 2) * 156, 58 + (i // 2) * 86
        out.append(
            f'<g><rect x="{x}" y="{y}" width="146" height="76" rx="11" fill="{P}" fill-opacity="0.08" stroke="{P}" stroke-opacity="0.3"/>'
            f'<rect x="{x}" y="{y + 16}" width="3" height="26" rx="1.5" fill="{HOT}"/>'
            f'<text x="{x + 16}" y="{y + 40}" font-size="29" font-weight="800" fill="url(#num)">{escape(str(val))}</text>'
            f'<text x="{x + 16}" y="{y + 61}" font-size="9.5" letter-spacing="1.2" fill="{LIGHT}" fill-opacity="0.7">{escape(label)}</text>'
            f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{0.1 + i * 0.12:.2f};1" dur="{0.5 + i * 0.15:.2f}s" fill="freeze"/></g>')
    return "\n".join(out)


def heatmap(data):
    days = sorted(data["days"])
    # align to whole weeks (Sunday-first, as GitHub's calendar does) and keep the latest HEAT_WEEKS
    first = date.fromisoformat(days[0][0])
    pad = (first.weekday() + 1) % 7
    cells = [None] * pad + [c for _, c in days]
    weeks = [cells[i:i + 7] for i in range(0, len(cells), 7)][-HEAT_WEEKS:]
    nonzero = sorted(c for w in weeks for c in w if c)
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)] if nonzero else [1, 2, 3]

    def level(c):
        return 0 if not c else 1 + sum(c > k for k in cuts)

    x0, y0, s = 356, 82, 12.6
    out = [f'<text x="{x0}" y="70" font-size="11" letter-spacing="2.5" font-weight="700" fill="{PALE}">ACTIVITY · {HEAT_WEEKS} WEEKS</text>']
    for wi, w in enumerate(weeks):
        for di, c in enumerate(w):
            if c is None:
                continue
            out.append(f'<rect x="{x0 + wi * s:.1f}" y="{y0 + di * s:.1f}" width="10" height="10" rx="2.2" fill="{HEAT[level(c)]}">'
                       f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{wi / len(weeks) * 0.8:.3f};1" dur="1.4s" fill="freeze"/></rect>')
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
    out = [f'<text x="{x0}" y="70" font-size="11" letter-spacing="2.5" font-weight="700" fill="{PALE}">TOP LANGUAGES</text>',
           f'<clipPath id="bar"><rect x="{x0}" y="84" width="{w}" height="10" rx="5"/></clipPath>',
           f'<rect x="{x0}" y="84" width="{w}" height="10" rx="5" fill="#1E1230"/><g clip-path="url(#bar)">']
    x = x0
    for i, (name, b) in enumerate(top):
        seg = w * b / total
        out.append(f'<rect x="{x:.1f}" y="84" width="{seg + 0.5:.1f}" height="10" fill="{LANG_SHADES[i]}"/>')
        x += seg
    out.append(f'<animate attributeName="opacity" values="0;1" dur="0.8s" fill="freeze"/></g>')
    for i, (name, b) in enumerate(top):
        cx, cy = x0 + (i % 2) * 142, 122 + (i // 2) * 30
        out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{LANG_SHADES[i]}"/>'
                   f'<text x="{cx + 16}" y="{cy}" font-size="12.5" fill="{PALE}">{escape(SHORT_NAMES.get(name, name))}'
                   f'<tspan fill="{LIGHT}" fill-opacity="0.6" font-size="11"> {100 * b / total:.1f}%</tspan></text>')
    return "\n".join(out)


def render(data, updated):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 240" width="1000" height="240" role="img" aria-label="GitHub stats for {LOGIN}: {data["total"]} contributions in the last year, {data["merged"]} merged upstream pull requests">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#140A22"/><stop offset="1" stop-color="#0A0612"/></linearGradient>
  <radialGradient id="glow"><stop offset="0" stop-color="{P}" stop-opacity="0.32"/><stop offset="1" stop-color="{P}" stop-opacity="0"/></radialGradient>
  <linearGradient id="num" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{PALE}"/><stop offset="1" stop-color="{P}"/></linearGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{HOT}"/><stop offset="1" stop-color="{LIGHT}"/></linearGradient>
  <clipPath id="card"><rect x="1" y="1" width="998" height="238" rx="20"/></clipPath>
</defs>
<g font-family='{MONO}'>
<g clip-path="url(#card)">
  <rect width="1000" height="240" fill="url(#bg)"/>
  <circle cx="520" cy="0" r="320" fill="url(#glow)"/>
</g>
<rect x="1" y="1" width="998" height="238" rx="20" fill="none" stroke="{P}" stroke-opacity="0.3" stroke-width="1.5"/>
<rect x="1" y="1" width="998" height="238" rx="20" fill="none" stroke="url(#beam)" stroke-width="2.2" stroke-linecap="round" pathLength="1000" stroke-dasharray="90 410">
  <animate attributeName="stroke-dashoffset" values="0;1000" dur="9s" repeatCount="indefinite"/>
</rect>
<rect x="28" y="24" width="10" height="10" rx="2" transform="rotate(45 33 29)" fill="none" stroke="{HOT}" stroke-width="2"/>
<text x="46" y="33.5" font-size="11.5" letter-spacing="3.5" fill="{LIGHT}" fill-opacity="0.8">GITHUB.COM/{LOGIN.upper()} <tspan fill-opacity="0.5">· LIVE STATS</tspan></text>
<text x="972" y="33.5" text-anchor="end" font-size="10.5" letter-spacing="1" fill="{LIGHT}" fill-opacity="0.5">auto-updated {updated}</text>
<path d="M336 58v162M672 58v162" stroke="{P}" stroke-opacity="0.18" stroke-dasharray="3 5"/>
{tiles(data)}
{heatmap(data)}
{languages(data)}
</g>
</svg>
'''


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN")
    data = fetch(token)
    out = Path(__file__).resolve().parent.parent / "assets" / "stats.svg"
    out.write_text(render(data, datetime.now(timezone.utc).strftime("%d %b %Y")), encoding="utf-8")
    print(f"wrote {out}: {data['total']} contributions, {data['merged']} merged PRs")


if __name__ == "__main__":
    main()
