#!/usr/bin/env python3
"""Builds assets/hero.svg — edit the text below, then run: python3 scripts/build_hero.py"""
from pathlib import Path
from xml.sax.saxutils import escape

ROLES = [
    "Software Developer",
    "Open Source Contributor",
    "Google Student Ambassador",
    "AI/ML Explorer",
    "DSA, every single day",
]
META = [
    "B.Tech CSE '28  ·  SGGSIE&T, Nanded",
    "Focused on open source and daily problem solving",
    "Turning ideas into reliable, well-crafted software",
]
# (prompt, text) — prompt "$" lines are commands, "✓" lines are highlights
TERMINAL = [
    ("$", "whoami"),
    ("", "sameer chore — cse '28, sggsie&t"),
    ("$", "cat focus.txt"),
    ("✓", "open-source contributions"),
    ("✓", "clean, scalable software"),
    ("✓", "data structures & algorithms"),
    ("$", "echo $NEXT"),
    ("", "ai/ml · system design"),
]
STACK = ["C++", "Java", "Python", "JavaScript", "Node.js", "Go", "Rust",
         "HTML/CSS", "Git", "Linux", "Docker", "DSA", "Open Source"]

P, LIGHT, PALE, DEEP, HOT = "#9953EA", "#C79DF1", "#ECDDFD", "#6E1FA3", "#D946EF"
MONO = 'ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,Consolas,"DejaVu Sans Mono",monospace'
W, H = 1000, 380


def typing():
    """Discrete SMIL keyframes: each role types in, holds, deletes; one shared caret."""
    size, cw, x0, y = 21, 12.6, 80, 196
    type_s, hold_s, del_s, gap_s = 0.075, 1.7, 0.03, 0.25
    frames = []  # (time, role_index, chars)
    t = 0.0
    for i, r in enumerate(ROLES):
        for n in range(len(r) + 1):
            frames.append((t, i, n)); t += type_s
        t += hold_s
        for n in range(len(r), -1, -1):
            frames.append((t, i, n)); t += del_s
        t += gap_s
    total = t
    kt = ";".join(f"{f[0] / total:.5f}" for f in frames)

    out = [f'<text x="48" y="{y}" font-size="{size}" font-weight="700" fill="{HOT}">❯</text>']
    for i, r in enumerate(ROLES):
        widths = ";".join(f"{(n * cw if ri == i else 0):.1f}" for _, ri, n in frames)
        base = len(r) * cw if i == 0 else 0  # static renderers show the first role
        out.append(
            f'<clipPath id="r{i}"><rect x="{x0}" y="{y - 22}" width="{base:.1f}" height="30">'
            f'<animate attributeName="width" values="{widths}" keyTimes="{kt}" calcMode="discrete" '
            f'dur="{total:.2f}s" repeatCount="indefinite"/></rect></clipPath>'
            f'<text clip-path="url(#r{i})" x="{x0}" y="{y}" font-size="{size}" font-weight="600" '
            f'fill="{PALE}" textLength="{len(r) * cw:.1f}" lengthAdjust="spacing">{escape(r)}</text>')
    xs = ";".join(f"{x0 + n * cw + 2:.1f}" for _, _, n in frames)
    out.append(
        f'<rect x="{x0 + len(ROLES[0]) * cw + 2:.1f}" y="{y - 19}" width="11" height="23" fill="{P}">'
        f'<animate attributeName="x" values="{xs}" keyTimes="{kt}" calcMode="discrete" '
        f'dur="{total:.2f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="0.9s" '
        f'repeatCount="indefinite"/></rect>')
    return "\n".join(out)


def name():
    txt, x, y, tl = "SAMEER CHORE", 46, 134, 476
    common = f'x="{x}" y="{y}" font-size="58" font-weight="800" textLength="{tl}" lengthAdjust="spacingAndGlyphs"'
    glitch = []
    for color, dx in ((HOT, -3), (LIGHT, 3)):
        glitch.append(
            f'<text {common} fill="{color}" opacity="0">{txt}'
            f'<animate attributeName="opacity" values="0;0.75;0;0.6;0;0" '
            f'keyTimes="0;0.70;0.715;0.73;0.745;1" calcMode="discrete" dur="5s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx} 0;{-dx} 1;{dx} -1;0 0;0 0" '
            f'keyTimes="0;0.70;0.715;0.73;0.745;1" calcMode="discrete" dur="5s" repeatCount="indefinite"/></text>')
    return "\n".join(glitch) + f'\n<text {common} fill="url(#nameGrad)">{txt}</text>'


def terminal():
    x, y, w, h = 590, 78, 362, 222
    out = [
        f'<g filter="url(#shadow)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#0D0718" fill-opacity="0.92" stroke="{P}" stroke-opacity="0.4"/></g>',
        f'<path d="M{x} {y + 30}h{w}" stroke="{P}" stroke-opacity="0.25"/>',
    ]
    for i, c in enumerate((HOT, P, LIGHT)):
        out.append(f'<circle cx="{x + 18 + i * 16}" cy="{y + 15}" r="5" fill="{c}" fill-opacity="0.85"/>')
    out.append(f'<text x="{x + w / 2}" y="{y + 19.5}" text-anchor="middle" font-size="11" fill="{LIGHT}" fill-opacity="0.6" letter-spacing="1">sameer@sggs: ~</text>')
    step = 0.55
    for i, (pr, body) in enumerate(TERMINAL):
        ly = y + 54 + i * 21
        begin = 0.4 + i * step
        if pr == "$":
            spans = f'<tspan fill="{HOT}">$ </tspan><tspan fill="{PALE}">{escape(body)}</tspan>'
        elif pr == "✓":
            spans = f'<tspan fill="{P}">✓ </tspan><tspan fill="{LIGHT}">{escape(body)}</tspan>'
        else:
            spans = f'<tspan fill="{LIGHT}" fill-opacity="0.75">{escape(body)}</tspan>'
        out.append(
            f'<text x="{x + 18}" y="{ly}" font-size="13.5">{spans}'
            f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{begin / (begin + 0.3):.4f};1" '
            f'dur="{begin + 0.3:.2f}s" fill="freeze"/></text>')
    last = TERMINAL[-1][1]
    cx = x + 18 + (len(last) + 1) * 8.1
    out.append(f'<rect x="{cx:.1f}" y="{y + 54 + (len(TERMINAL) - 1) * 21 - 11}" width="8" height="14" fill="{P}">'
               f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>')
    return "\n".join(out)


def ticker():
    y, h = 322, 40
    cw, pad, gap = 8.4, 30, 12
    chips, x = [], 0.0
    for s in STACK:
        tw = len(s) * cw
        chips.append(
            f'<g transform="translate({x:.1f},0)"><rect y="{y + 7}" width="{tw + pad:.1f}" height="26" rx="13" '
            f'fill="{P}" fill-opacity="0.10" stroke="{P}" stroke-opacity="0.45"/>'
            f'<circle cx="13" cy="{y + 20}" r="3" fill="{HOT}"/>'
            f'<text x="22" y="{y + 24.5}" font-size="13" font-weight="600" fill="{PALE}" textLength="{tw:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{escape(s)}</text></g>')
        x += tw + pad + gap
    set_w = x
    row = "".join(chips)
    return (
        f'<rect x="1" y="{y}" width="998" height="{h}" fill="{P}" fill-opacity="0.05"/>'
        f'<path d="M1 {y}h998M1 {y + h}h998" stroke="{P}" stroke-opacity="0.22"/>'
        f'<g mask="url(#fadeX)"><g transform="translate(24,0)">'
        f'<g>{row}<g transform="translate({set_w:.1f},0)">{row}</g>'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{-set_w:.1f} 0" '
        f'dur="28s" repeatCount="indefinite"/></g></g></g>')


def build():
    meta = "\n".join(
        f'<rect x="50" y="{226 + i * 28}" width="7" height="7" rx="1.5" transform="rotate(45 53.5 {229.5 + i * 28})" fill="{P}"/>'
        f'<text x="70" y="{234 + i * 28}" font-size="15" fill="{LIGHT}" fill-opacity="0.85">{escape(m)}</text>'
        for i, m in enumerate(META))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Sameer Chore — software developer and open source contributor">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#140A22"/><stop offset="1" stop-color="#0A0612"/></linearGradient>
  <radialGradient id="glowA"><stop offset="0" stop-color="{P}" stop-opacity="0.45"/><stop offset="1" stop-color="{P}" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowB"><stop offset="0" stop-color="{HOT}" stop-opacity="0.25"/><stop offset="1" stop-color="{HOT}" stop-opacity="0"/></radialGradient>
  <linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{PALE}"/><stop offset="0.45" stop-color="{LIGHT}"/><stop offset="1" stop-color="{P}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-0.3 0;0.3 0;-0.3 0" dur="7s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{HOT}"/><stop offset="0.4" stop-color="{P}" stop-opacity="0.6"/><stop offset="1" stop-color="{P}" stop-opacity="0"/></linearGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{LIGHT}" fill-opacity="0.13"/></pattern>
  <linearGradient id="fadeGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.06" stop-color="#fff"/><stop offset="0.94" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <mask id="fadeX"><rect width="{W}" height="{H}" fill="url(#fadeGrad)"/></mask>
  <clipPath id="card"><rect x="1" y="1" width="998" height="378" rx="20"/></clipPath>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="{P}" flood-opacity="0.28"/></filter>
</defs>
<g font-family='{MONO}'>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <circle cx="170" cy="90" r="300" fill="url(#glowA)">
    <animateTransform attributeName="transform" type="translate" values="0 0;60 30;0 0" dur="14s" repeatCount="indefinite"/>
  </circle>
  <circle cx="880" cy="340" r="260" fill="url(#glowB)">
    <animateTransform attributeName="transform" type="translate" values="0 0;-70 -20;0 0" dur="11s" repeatCount="indefinite"/>
  </circle>
  <rect y="-40" width="{W}" height="40" fill="{LIGHT}" fill-opacity="0.035">
    <animate attributeName="y" values="-40;{H}" dur="6s" repeatCount="indefinite"/>
  </rect>
</g>
<rect x="1" y="1" width="998" height="378" rx="20" fill="none" stroke="{P}" stroke-opacity="0.3" stroke-width="1.5"/>

<rect x="48" y="38" width="12" height="12" rx="2" transform="rotate(45 54 44)" fill="none" stroke="{HOT}" stroke-width="2"/>
<text x="70" y="49" font-size="12" letter-spacing="4" fill="{LIGHT}" fill-opacity="0.75">SAMC4E <tspan fill-opacity="0.45">/ README.md</tspan></text>

<rect x="752" y="31" width="200" height="26" rx="13" fill="{P}" fill-opacity="0.12" stroke="{P}" stroke-opacity="0.5"/>
<circle cx="768" cy="44" r="4" fill="#4ADE80"><animate attributeName="r" values="4;6;4" dur="1.8s" repeatCount="indefinite"/><animate attributeName="fill-opacity" values="1;0.4;1" dur="1.8s" repeatCount="indefinite"/></circle>
<text x="780" y="48.5" font-size="11" letter-spacing="1.6" font-weight="700" fill="{PALE}">OPEN TO COLLABORATE</text>

{name()}
<rect x="48" y="152" width="510" height="2" fill="url(#rule)"/>
{typing()}
{meta}
{terminal()}
{ticker()}
</g>
</svg>
'''


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "hero.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
