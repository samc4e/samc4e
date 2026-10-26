#!/usr/bin/env python3
"""Builds assets/hero.svg from the text below and the cached LeetCode stats in assets/leetcode.json.

generate_stats.py refreshes the LeetCode numbers daily; to change the text, edit below and run
python3 scripts/build_hero.py
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

NAME = "Sameer Chore"
EYEBROW = "B.TECH CSE '28  ·  SGGSIE&T, NANDED"
TAGLINE = "Software Developer  ·  Open Source Contributor"
FACTS = [
    ("ROLE", "Google Student Ambassador"),
    ("FOCUS", "Software engineering · AI/ML"),
    ("NOW", "Open source and daily problem solving"),
]
STACK = ["C++", "Java", "Python", "JavaScript", "Node.js", "Go", "Rust", "Git", "Linux", "Docker"]
LEETCODE_USER = "samc4e"

P, LIGHT, PALE = "#E58AA2", "#C4C4CC", "#F6F6F8"  # blush, frost, snow — from the avatar
DIFF = {"Easy": "#FCE7EC", "Medium": "#F2B8C6", "Hard": "#E58AA2"}  # ordinal ramp validated against the surface
SANS = '-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace'
W, H = 1000, 340
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def leetcode_panel(lc):
    x, y, w, h = 600, 40, 352, 222
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#FFFFFF" fill-opacity="0.025" stroke="{P}" stroke-opacity="0.35"/>',
        f'<text x="{x + 24}" y="{y + 34}" font-family=\'{MONO}\' font-size="11" letter-spacing="2.5" fill="{LIGHT}" fill-opacity="0.8">LEETCODE</text>',
        f'<text x="{x + w - 24}" y="{y + 34}" text-anchor="end" font-family=\'{MONO}\' font-size="11" fill="{LIGHT}" fill-opacity="0.5">@{LEETCODE_USER}</text>',
        f'<text x="{x + 24}" y="{y + 82}" font-size="40" font-weight="700" fill="{PALE}">{lc["solved"]}'
        f'<tspan dx="10" font-size="14" font-weight="400" fill="{LIGHT}" fill-opacity="0.75">problems solved</tspan></text>',
    ]
    # composition of solved problems by difficulty, with a 2px surface gap between segments
    bx, by, bw = x + 24, y + 100, w - 48
    total = sum(lc[d] for d in DIFF) or 1
    out.append(f'<clipPath id="lcbar"><rect x="{bx}" y="{by}" width="{bw}" height="8" rx="4"/></clipPath><g clip-path="url(#lcbar)">')
    cx = bx
    for d, col in DIFF.items():
        seg = bw * lc[d] / total
        if seg:
            out.append(f'<rect x="{cx:.1f}" y="{by}" width="{max(seg - 2, 1.5):.1f}" height="8" fill="{col}"/>')
        cx += seg
    out.append("</g>")
    for i, (d, col) in enumerate(DIFF.items()):
        lx = bx + i * 104
        out.append(f'<circle cx="{lx + 4}" cy="{by + 30}" r="4" fill="{col}"/>'
                   f'<text x="{lx + 14}" y="{by + 34}" font-size="13" fill="{LIGHT}" fill-opacity="0.8">{d} '
                   f'<tspan fill="{PALE}" font-weight="600">{lc[d]}</tspan></text>')
    out.append(f'<path d="M{x + 24} {y + 158}H{x + w - 24}" stroke="{P}" stroke-opacity="0.22"/>')
    rank = lc["ranking"]
    rank_s = f"{rank / 1000:.0f}K" if rank >= 10000 else f"{rank:,}"
    for i, (val, label) in enumerate([(lc["active_days"], "ACTIVE DAYS"), (f'{lc["streak"]}d', "BEST STREAK"),
                                      (rank_s, "GLOBAL RANK")]):
        sx = x + 24 + i * 108
        out.append(f'<text x="{sx}" y="{y + 188}" font-size="19" font-weight="700" fill="{PALE}">{val}</text>'
                   f'<text x="{sx}" y="{y + 206}" font-family=\'{MONO}\' font-size="9.5" letter-spacing="1.2" fill="{LIGHT}" fill-opacity="0.65">{label}</text>')
    return "\n".join(out)


def stack_row():
    out, x, y = [], 48.0, 290
    for s in STACK:
        w = len(s) * 7.6 + 24
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="26" rx="6" fill="{P}" fill-opacity="0.08" stroke="{P}" stroke-opacity="0.35"/>'
                   f'<text x="{x + w / 2:.1f}" y="{y + 17.5}" text-anchor="middle" font-family=\'{MONO}\' font-size="12.5" fill="{PALE}" fill-opacity="0.9">{escape(s)}</text>')
        x += w + 8
    return "\n".join(out)


def build(lc):
    facts = "\n".join(
        f'<text x="48" y="{214 + i * 26}" font-family=\'{MONO}\' font-size="10.5" letter-spacing="2" fill="{LIGHT}" fill-opacity="0.6">{k}</text>'
        f'<text x="128" y="{214 + i * 26}" font-size="15" fill="{PALE}" fill-opacity="0.92">{escape(v)}</text>'
        for i, (k, v) in enumerate(FACTS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(NAME)} — {escape(TAGLINE)}. LeetCode: {lc["solved"]} problems solved.">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#141417"/><stop offset="1" stop-color="#08080A"/></linearGradient>
  <radialGradient id="glow" cx="0.15" cy="0.1" r="0.7"><stop offset="0" stop-color="{P}" stop-opacity="0.22"/><stop offset="1" stop-color="{P}" stop-opacity="0"/></radialGradient>
  <linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{PALE}"/><stop offset="1" stop-color="{LIGHT}"/></linearGradient>
  <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P}"/><stop offset="1" stop-color="{P}" stop-opacity="0"/></linearGradient>
</defs>
<g font-family='{SANS}'>
<rect x="1" y="1" width="998" height="{H - 2}" rx="20" fill="url(#bg)"/>
<rect x="1" y="1" width="998" height="{H - 2}" rx="20" fill="url(#glow)"/>
<rect x="1" y="1" width="998" height="{H - 2}" rx="20" fill="none" stroke="{P}" stroke-opacity="0.3" stroke-width="1.5"/>

<text x="48" y="70" font-family='{MONO}' font-size="11.5" letter-spacing="2.5" fill="{LIGHT}" fill-opacity="0.7">{escape(EYEBROW)}</text>
<text x="46" y="126" font-size="54" font-weight="700" letter-spacing="-0.5" fill="url(#nameGrad)">{escape(NAME)}</text>
<text x="48" y="160" font-size="18" fill="{LIGHT}">{escape(TAGLINE)}</text>
<rect x="48" y="182" width="500" height="1.5" fill="url(#rule)"/>
{facts}
{leetcode_panel(lc)}
{stack_row()}
</g>
</svg>
'''


def write(lc):
    (ASSETS / "hero.svg").write_text(build(lc), encoding="utf-8")


if __name__ == "__main__":
    write(json.loads((ASSETS / "leetcode.json").read_text()))
    print("wrote assets/hero.svg")
