#!/usr/bin/env python3
"""Draw the profile README as SVG cards.

A GitHub README cannot run scripts or load a stylesheet, but it can show an
image, and an SVG image carries its own CSS and fonts. So the layout lives in
README.md and everything visual lives in cards/*.svg, drawn here.

    python scripts/render_cards.py            animated cards
    STATIC=1 python scripts/render_cards.py   final frame, for screenshots

Standard library only, so the daily Action needs no install step. Text is
measured with the advance widths in fonts/metrics.json, which is what lets
lines wrap and names fit without a browser in the loop.
"""
from __future__ import annotations

import base64
import json
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

DATA = json.loads((ROOT / "data" / "github.json").read_text())
METRICS = json.loads((ROOT / "fonts" / "metrics.json").read_text())

# ---------------------------------------------------------------- the palette

COBALT = "#2233DD"
LIME = "#CEF12B"
INK = "#0E1330"

THEMES = {
    # GitHub's light page is white and its dark page is near-black, so the
    # cards need their own ground in each. Lime fails on a pale ground, so
    # the light theme marks the running card in cobalt instead.
    "light": {"bg": "#EEF1FB", "title": INK, "body": "#4A5377", "mark": COBALT},
    "dark": {"bg": "#161D4D", "title": "#F3F5FF", "body": "#B4BBE3", "mark": LIME},
}

# GitHub's own language colours, because that is how a reader already knows
# them.
LANG = {"Python": "#3572A5", "JavaScript": "#F1E05A", "HTML": "#E34C26"}

# ----------------------------------------------------------------- the agents
# Order matters: it is the order the hero cycles through, and the order the
# cards sit in the README, so the card that lights up is the one being named.

AGENTS = [
    {"repo": "google-business-profile-ai-automation",
     "key": "gbp",
     "name": "Google Business Profile",
     "does": "audits the profile, fixes it, replies to reviews",
     "title": "Google Business Profile autopilot",
     "blurb": "Audits a profile against local SEO rules, fixes what it can, "
              "and replies to every review."},
    {"repo": "whatsapp-ai-chatbot-support-agent",
     "key": "whatsapp",
     "name": "WhatsApp",
     "does": "answers customers in the app you already use",
     "title": "WhatsApp support agent",
     "blurb": "Answers customers from inside WhatsApp Business, in English, "
              "Urdu and Roman Urdu."},
    {"repo": "linkedin-automation-ai-agent",
     "key": "linkedin",
     "name": "LinkedIn",
     "does": "one post a day, comments, connection notes",
     "title": "LinkedIn agent",
     "blurb": "One post a day, useful comments and connection notes, behind "
              "hard safety rails."},
    {"repo": "reddit-lead-generation-ai-agent",
     "key": "reddit",
     "name": "Reddit and Quora",
     "does": "finds the threads where your customers ask",
     "title": "Reddit and Quora lead finder",
     "blurb": "Finds threads where people have the problem you solve and "
              "drafts a useful reply."},
    {"repo": "upwork-ai-proposal-bot",
     "key": "upwork",
     "name": "Upwork",
     "does": "scores new jobs and drafts the proposal",
     "title": "Upwork proposal bot",
     "blurb": "Catches new jobs within a minute, scores them, and sends a "
              "proposal draft to your phone."},
    {"repo": "zara-ai-laptop-agent",
     "key": "zara",
     "name": "Zara",
     "does": "runs a Windows laptop from your phone",
     "title": "Zara, a laptop agent",
     "blurb": "Runs a Windows laptop from Discord on your phone, by text or "
              "by voice note."},
]

# The cycle every card shares. Each agent holds the highlight for SLOT
# seconds, so one lap is SLOT * len(AGENTS).
START = 2.0
SLOT = 2.0
LAP = SLOT * len(AGENTS)


# ------------------------------------------------------------------ type

def font_face(name: str, family: str) -> str:
    raw = (ROOT / "fonts" / f"archivo-{name}.woff").read_bytes()
    b64 = base64.b64encode(raw).decode()
    return (f"@font-face{{font-family:'{family}';"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}")


FONTS = {"display": "AX", "semi": "A6", "regular": "A4"}


def width(text: str, font: str, size: float) -> float:
    m = METRICS[font]
    fallback = m["adv"]["n"]
    return sum(m["adv"].get(ch, fallback) for ch in text) * size / m["upm"]


def wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if width(trial, font, size) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fit(text: str, font: str, max_width: float, ceiling: float) -> float:
    """The largest size, up to `ceiling`, at which `text` fits `max_width`."""
    return min(ceiling, ceiling * max_width / width(text, font, ceiling))


def text(x: float, y: float, s: str, font: str, size: float, fill: str,
         extra: str = "") -> str:
    return (f'<text x="{x:g}" y="{y:g}" font-family="{FONTS[font]}" '
            f'font-size="{size:g}" fill="{fill}"{extra}>{escape(s)}</text>')


def style(fonts: list[str], css: str) -> str:
    faces = "".join(font_face(f, FONTS[f]) for f in fonts)
    motion = "" if STATIC else css
    return (f"<style>{faces}text{{font-kerning:normal}}{motion}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            "</style>")


# ------------------------------------------------------------------ the hero

def hero() -> str:
    W, H = 1200, 512
    avatar = base64.b64encode((ROOT / "assets" / "avatar.jpg").read_bytes()).decode()

    stars, repos = DATA["total_stars"], DATA["public_repos"]
    stat = (f"{stars} star{'s' if stars != 1 else ''} across "
            f"{repos} public repositories")

    first, last = "Tanzeel", "Ur Rehman"
    size = fit(last, "display", 520, 74)
    statement = wrap("I build AI agents that do the repetitive work of a small "
                     "business: answering customers, keeping profiles fresh, "
                     "finding leads.", "regular", 24, 530)

    css = f"""
@keyframes pop{{from{{transform:scale(.6);opacity:0}}}}
@keyframes rise{{from{{transform:translateY({size * 1.1:.0f}px)}}}}
@keyframes fade{{from{{opacity:0}}}}
@keyframes slide{{from{{opacity:0;transform:translateX(14px)}}}}
@keyframes on{{0%,16.66%,100%{{opacity:0}}1.5%,15%{{opacity:1}}}}
@keyframes name{{0%,16.66%,100%{{fill:#fff}}1.5%,15%{{fill:{INK}}}}}
@keyframes does{{0%,16.66%,100%{{fill:#C9CEF6}}1.5%,15%{{fill:{INK}}}}}
.pop{{transform-box:fill-box;transform-origin:center;animation:pop .6s cubic-bezier(.2,1.4,.4,1) both}}
.rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
.fade{{animation:fade .7s ease both}}
.row{{animation:slide .5s ease both}}
.hl{{animation:on {LAP:g}s linear infinite}}
.nm{{animation:name {LAP:g}s linear infinite}}
.ds{{animation:does {LAP:g}s linear infinite}}
"""

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Tanzeel Ur Rehman builds AI agents for small businesses">',
        style(["display", "semi", "regular"], css),
        "<defs>"
        '<clipPath id="face"><circle cx="114" cy="112" r="52"/></clipPath>'
        f'<clipPath id="l1"><rect x="40" y="{262 - size:.0f}" width="620" height="{size + 10:.0f}"/></clipPath>'
        f'<clipPath id="l2"><rect x="40" y="{262 + size * 1.06 - size:.0f}" width="620" height="{size + 10:.0f}"/></clipPath>'
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="28" fill="{COBALT}"/>',

        # The photo. Its own background is lime, which is where the accent
        # colour for the whole profile comes from.
        '<g class="pop">'
        f'<circle cx="114" cy="112" r="60" fill="none" stroke="{LIME}" stroke-width="3"/>'
        f'<image x="58" y="56" width="112" height="112" clip-path="url(#face)" '
        f'xlink:href="data:image/jpeg;base64,{avatar}" href="data:image/jpeg;base64,{avatar}"/>'
        "</g>",
        '<g class="fade" style="animation-delay:.25s">',
        text(198, 106, "@tanzeeldevAi", "semi", 23, "#fff"),
        text(198, 136, stat, "regular", 18.5, "#C9CEF6"),
        "</g>",

        f'<g clip-path="url(#l1)"><g class="rise" style="animation-delay:.2s">'
        + text(57, 262, first, "display", size, "#fff") + "</g></g>",
        f'<g clip-path="url(#l2)"><g class="rise" style="animation-delay:.34s">'
        + text(57, 262 + size * 1.06, last, "display", size, "#fff") + "</g></g>",
    ]

    y = 262 + size * 1.06 + 58
    out.append('<g class="fade" style="animation-delay:.75s">')
    for i, line in enumerate(statement):
        out.append(text(60, y + i * 34, line, "regular", 24, "#E4E7FF"))
    out.append("</g>")

    # The roster. One row is lit at a time, and the highlight walks down the
    # list for as long as the page is open: the agents take turns, which is
    # what they do.
    out.append('<g class="fade" style="animation-delay:.9s">'
               + text(686, 78, "What the agents do", "semi", 20, "#C9CEF6") + "</g>")
    for i, a in enumerate(AGENTS):
        top = 100 + i * 64
        delay = START + i * SLOT
        lit = STATIC and i == 0
        run = f' style="animation-delay:{delay:g}s"'
        out.append(
            f'<g class="row" style="animation-delay:{1.0 + i * .09:g}s">'
            f'<rect class="hl"{run} x="664" y="{top}" width="476" height="58" rx="13" '
            f'fill="{LIME}" opacity="{1 if lit else 0}"/>'
            + text(686, top + 26, a["name"], "semi", 22, INK if lit else "#fff",
                   f' class="nm"{run}')
            + text(686, top + 47, a["does"], "regular", 17.5,
                   INK if lit else "#C9CEF6", f' class="ds"{run}')
            + "</g>")

    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------ one agent card

STAR = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 "
        ".416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347"
        "l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 "
        "0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")


def card(index: int, agent: dict, theme: str) -> str:
    # The README sets two cards side by side at exactly 50% each with no
    # space between them, so the pair spans the same width as the hero. The
    # gutter therefore has to live inside the image: the left card leaves 8
    # units empty on its right, the right card 8 on its left, and both leave
    # 8 underneath so the rows sit as far apart as the columns do.
    FULL_W, FULL_H = 600, 240
    W, H = 592, 232
    x0 = 0 if index % 2 == 0 else FULL_W - W
    t = THEMES[theme]
    repo = DATA["repos"].get(agent["repo"], {})
    stars = repo.get("stars", 0)
    lang = repo.get("language") or ""

    # Lit for the same two seconds the hero names this agent.
    css = (f"@keyframes on{{0%,16.66%,100%{{opacity:0}}1.5%,15%{{opacity:1}}}}"
           f".hl{{animation:on {LAP:g}s linear infinite;"
           f"animation-delay:{START + index * SLOT:g}s}}")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FULL_W} {FULL_H}" '
        f'width="{FULL_W}" height="{FULL_H}" role="img" aria-label="{escape(agent["title"])}">',
        style(["semi", "regular"], css),
        f'<g transform="translate({x0} 0)">',
        f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>',
        f'<rect class="hl" x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="14.5" '
        f'fill="none" stroke="{t["mark"]}" stroke-width="3" '
        f'opacity="{1 if STATIC and index == 0 else 0}"/>',
        text(32, 62, agent["title"], "semi", 26, t["title"]),
    ]
    for i, line in enumerate(wrap(agent["blurb"], "regular", 19, W - 64)):
        out.append(text(32, 102 + i * 28, line, "regular", 19, t["body"]))

    x, y = 32, H - 34
    if lang:
        out.append(f'<circle cx="{x + 7}" cy="{y - 6}" r="7" fill="{LANG.get(lang, t["body"])}"/>')
        out.append(text(x + 22, y, lang, "regular", 17.5, t["body"]))
        x += 22 + width(lang, "regular", 17.5) + 26
    if stars:
        out.append(f'<path transform="translate({x:g} {y - 15}) scale(1.06)" '
                   f'fill="{t["body"]}" d="{STAR}"/>')
        out.append(text(x + 23, y, str(stars), "semi", 17.5, t["body"]))

    out.append("</g></svg>")
    return "".join(out)


def main() -> None:
    CARDS.mkdir(exist_ok=True)
    (CARDS / "hero.svg").write_text(hero())
    for i, agent in enumerate(AGENTS):
        for theme in THEMES:
            (CARDS / f"{agent['key']}-{theme}.svg").write_text(card(i, agent, theme))
    for f in sorted(CARDS.glob("*.svg")):
        print(f"{f.name:22} {f.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
