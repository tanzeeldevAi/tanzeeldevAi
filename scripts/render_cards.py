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
# Every colour here is taken from the profile photo, whose backdrop runs from
# a dark moss on the left to a lime green on the right. The hero repeats that
# sweep, so the photo sits in it rather than on it.

MOSS = "#222C0F"      # the photo's dark edge
FERN = "#36470F"      # the same green, a third of the way across
LIME = "#CEF12B"      # the photo's bright edge, pushed to full strength
INK = "#1A220A"       # text on lime
SOFT = "#D5DEB5"      # secondary text on the green ground

THEMES = {
    # GitHub's light page is white and its dark page is near-black, so the
    # cards need their own ground in each. Lime fails on a pale ground, so
    # the light theme marks the running card in a deeper green instead.
    "light": {"bg": "#F0F4E1", "title": INK, "body": "#55603A", "mark": "#5C7A0C"},
    "dark": {"bg": "#1E2710", "title": "#F5F8E8", "body": "#B7C296", "mark": LIME},
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
# seconds, so one lap is SLOT * len(AGENTS). The lap starts once the page has
# finished arriving.
START = 3.0
SLOT = 2.0
LAP = SLOT * len(AGENTS)

# One agent's turn, as a share of the lap. Every "while it is my turn"
# animation is written against these, so they stay in step with each other.
TURN = 100 / len(AGENTS)
ON = f"0%,{TURN:.3f}%,100%"
HELD = f"1.5%,{TURN - 1.6:.3f}%"


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


def count_up(x: float, y: float, n: int, font: str, size: float, fill: str,
             start: float, dur: float = 1.0) -> str:
    """A number that counts up from zero to `n`.

    CSS cannot change the text of an element, so the count is a stack of
    numbers in the same spot, each visible for a moment. The real value is the
    one left standing, and it is also the only one shown when motion is off.
    """
    final = text(x, y, str(n), font, size, fill)
    if STATIC or n < 2:
        return final
    steps = min(n, 14)
    # Ease out: quick at first, slowing as it nears the real number.
    values = sorted({round(n * (1 - (1 - i / steps) ** 2)) for i in range(steps)} - {n})
    each = dur / len(values)
    frames = "".join(
        text(x, y, str(v), font, size, fill,
             f' opacity="0" style="animation:show {each:.3f}s steps(1) '
             f'{start + i * each:.3f}s 1"')
        for i, v in enumerate(values))
    final = text(x, y, str(n), font, size, fill,
                 f' style="animation:wait {start + dur:.3f}s linear 1"')
    return frames + final


# Shared by every card: the pieces of the count-up.
COUNT_CSS = ("@keyframes show{from,to{opacity:1}}"
             "@keyframes wait{from,to{opacity:0}}")


def style(fonts: list[str], css: str) -> str:
    faces = "".join(font_face(f, FONTS[f]) for f in fonts)
    motion = "" if STATIC else COUNT_CSS + css
    return (f"<style>{faces}text{{font-kerning:normal}}{motion}"
            "@media (prefers-reduced-motion:reduce){"
            "*{animation:none!important}.shine{fill:#fff!important}}"
            "</style>")


# ------------------------------------------------------------------ the hero

def hero() -> str:
    W, H = 1200, 512
    avatar = base64.b64encode((ROOT / "assets" / "avatar.jpg").read_bytes()).decode()

    stars, repos = DATA["total_stars"], DATA["public_repos"]

    first, last = "Tanzeel", "Ur Rehman"
    size = fit(last, "display", 520, 74)
    statement = wrap("I build AI agents that do the repetitive work of a small "
                     "business: answering customers, keeping profiles fresh, "
                     "finding leads.", "regular", 24, 530)

    ring = 2 * 3.14159 * 60
    css = f"""
@keyframes pop{{from{{transform:scale(.6);opacity:0}}}}
@keyframes draw{{from{{stroke-dashoffset:{ring:.0f}}}}}
@keyframes pulse{{0%{{transform:scale(1);opacity:.75}}70%,100%{{transform:scale(1.5);opacity:0}}}}
@keyframes drift{{from{{transform:translate(0,0)}}to{{transform:translate(-190px,90px)}}}}
@keyframes rise{{from{{transform:translateY({size * 1.1:.0f}px)}}}}
@keyframes fade{{from{{opacity:0}}}}
@keyframes slide{{from{{opacity:0;transform:translateX(14px)}}}}
@keyframes on{{{ON}{{opacity:0}}{HELD}{{opacity:1}}}}
@keyframes name{{{ON}{{fill:#fff}}{HELD}{{fill:{INK}}}}}
@keyframes does{{{ON}{{fill:{SOFT}}}{HELD}{{fill:{INK}}}}}
@keyframes work{{0%{{transform:scaleX(0);opacity:.5}}{TURN - 1.6:.3f}%{{transform:scaleX(1);opacity:.5}}{TURN:.3f}%,100%{{transform:scaleX(1);opacity:0}}}}
.pop{{transform-box:fill-box;transform-origin:center;animation:pop .6s cubic-bezier(.2,1.4,.4,1) both}}
.draw{{animation:draw 1.1s cubic-bezier(.6,0,.2,1) .15s both}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 3.2s ease-out 1.5s infinite}}
.glow{{animation:drift 16s ease-in-out infinite alternate}}
.rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
.fade{{animation:fade .7s ease both}}
.row{{animation:slide .5s ease both}}
.hl{{animation:on {LAP:g}s linear infinite}}
.nm{{animation:name {LAP:g}s linear infinite}}
.ds{{animation:does {LAP:g}s linear infinite}}
.wk{{transform-box:fill-box;transform-origin:left;animation:work {LAP:g}s linear infinite}}
"""

    # A band of lime that crosses the name every few seconds. In SVG there is
    # no background-clip for text, so the name is filled with a gradient and
    # the gradient itself is what moves.
    sweep = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-0.75 0;0.75 0;0.75 0" keyTimes="0;0.2;1" dur="6.5s" '
        'begin="2.2s" repeatCount="indefinite"/>')

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Tanzeel Ur Rehman builds AI agents for small businesses">',
        style(["display", "semi", "regular"], css),
        "<defs>"
        f'<linearGradient id="ground" x1="0" x2="1" y1="0" y2="0.35">'
        f'<stop offset="0" stop-color="{MOSS}"/><stop offset="1" stop-color="{FERN}"/></linearGradient>'
        f'<radialGradient id="glow"><stop offset="0" stop-color="{LIME}" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="{LIME}" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="shine" x1="0" x2="1" gradientTransform="translate(-0.75 0)">'
        '<stop offset=".38" stop-color="#fff"/>'
        f'<stop offset=".5" stop-color="{LIME}"/>'
        f'<stop offset=".62" stop-color="#fff"/>{sweep}</linearGradient>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
        '<clipPath id="face"><circle cx="114" cy="112" r="52"/></clipPath>'
        f'<clipPath id="l1"><rect x="40" y="{262 - size:.0f}" width="620" height="{size + 10:.0f}"/></clipPath>'
        f'<clipPath id="l2"><rect x="40" y="{262 + size * 1.06 - size:.0f}" width="620" height="{size + 10:.0f}"/></clipPath>'
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="28" fill="url(#ground)"/>',
        # The lime light from the photo's backdrop, drifting slowly across
        # the corner the roster sits in.
        '<g clip-path="url(#card)">'
        '<circle class="glow" cx="1180" cy="20" r="430" fill="url(#glow)"/></g>',

        # The photo, with a ring that is drawn around it once and then sends
        # out a slow pulse.
        f'<circle class="pulse" cx="114" cy="112" r="60" fill="none" stroke="{LIME}" '
        f'stroke-width="2" opacity="0"/>',
        '<g class="pop">'
        f'<image x="58" y="56" width="112" height="112" clip-path="url(#face)" '
        f'xlink:href="data:image/jpeg;base64,{avatar}" href="data:image/jpeg;base64,{avatar}"/>'
        "</g>",
        f'<circle class="draw" cx="114" cy="112" r="60" fill="none" stroke="{LIME}" '
        f'stroke-width="3" stroke-linecap="round" stroke-dasharray="{ring:.0f}" '
        f'transform="rotate(-90 114 112)"/>',
    ]

    # "17 stars across 11 public repositories", with both numbers counting up.
    x, y, fs = 198, 136, 18.5
    out.append('<g class="fade" style="animation-delay:.25s">')
    out.append(text(198, 106, "@tanzeeldevAi", "semi", 23, "#fff"))
    for n, words in ((stars, f" star{'s' if stars != 1 else ''} across "),
                     (repos, " public repositories")):
        out.append(count_up(x, y, n, "semi", fs, "#fff", start=0.7))
        x += width(str(n), "semi", fs)
        out.append(text(x, y, words, "regular", fs, SOFT,
                        ' xml:space="preserve"'))
        x += width(words, "regular", fs)
    out.append("</g>")

    out += [
        f'<g clip-path="url(#l1)"><g class="rise" style="animation-delay:.2s">'
        + text(57, 262, first, "display", size, "url(#shine)", ' class="shine"')
        + "</g></g>",
        f'<g clip-path="url(#l2)"><g class="rise" style="animation-delay:.34s">'
        + text(57, 262 + size * 1.06, last, "display", size, "url(#shine)",
               ' class="shine"') + "</g></g>",
    ]

    y = 262 + size * 1.06 + 58
    out.append('<g class="fade" style="animation-delay:.75s">')
    for i, line in enumerate(statement):
        out.append(text(60, y + i * 34, line, "regular", 24, "#EDF2DA"))
    out.append("</g>")

    # The roster. One row is lit at a time, and the highlight walks down the
    # list for as long as the page is open: the agents take turns, which is
    # what they do. A line fills along the lit row while its turn lasts.
    out.append('<g class="fade" style="animation-delay:.9s">'
               + text(686, 78, "What the agents do", "semi", 20, SOFT) + "</g>")
    for i, a in enumerate(AGENTS):
        top = 100 + i * 64
        lit = STATIC and i == 0
        run = f' style="animation-delay:{START + i * SLOT:g}s"'
        out.append(
            f'<g class="row" style="animation-delay:{1.0 + i * .09:g}s">'
            f'<rect class="hl"{run} x="664" y="{top}" width="476" height="58" rx="13" '
            f'fill="{LIME}" opacity="{1 if lit else 0}"/>'
            f'<rect class="wk"{run} x="676" y="{top + 53}" width="452" height="2.5" '
            f'rx="1.25" fill="{INK}" opacity="0"/>'
            + text(686, top + 26, a["name"], "semi", 22, INK if lit else "#fff",
                   f' class="nm"{run}')
            + text(686, top + 46, a["does"], "regular", 17.5,
                   INK if lit else SOFT, f' class="ds"{run}')
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

    # Cards arrive after the hero has finished, a row at a time.
    arrive = 1.3 + index * 0.13
    turn = START + index * SLOT
    lit = STATIC and index == 0

    # Everything under "my turn" runs for the same two seconds the hero
    # names this agent: the border lights, a band of light crosses the card,
    # a line fills along the bottom, and the language dot beats.
    css = f"""
@keyframes in{{from{{opacity:0;transform:translateY(30px) scale(.96)}}60%{{transform:translateY(-4px) scale(1.004)}}}}
@keyframes spin{{from{{transform:rotate(-140deg) scale(0)}}60%{{transform:rotate(12deg) scale(1.25)}}}}
@keyframes on{{{ON}{{opacity:0}}{HELD}{{opacity:1}}}}
@keyframes sweep{{0%{{transform:translateX(0);opacity:1}}{TURN * .55:.3f}%{{transform:translateX({W + 260}px);opacity:1}}{TURN * .56:.3f}%,100%{{transform:translateX({W + 260}px);opacity:0}}}}
@keyframes work{{0%{{transform:scaleX(0);opacity:1}}{TURN - 1.6:.3f}%{{transform:scaleX(1);opacity:1}}{TURN:.3f}%,100%{{transform:scaleX(1);opacity:0}}}}
@keyframes beat{{{ON}{{transform:scale(1)}}{TURN * .25:.3f}%,{TURN * .75:.3f}%{{transform:scale(1.45)}}{TURN * .5:.3f}%{{transform:scale(1)}}}}
.in{{transform-box:fill-box;transform-origin:center;animation:in .75s cubic-bezier(.2,.9,.3,1) {arrive:g}s both}}
.spin{{transform-box:fill-box;transform-origin:center;animation:spin .6s cubic-bezier(.2,.9,.3,1) {arrive + .45:g}s both}}
.hl{{animation:on {LAP:g}s linear {turn:g}s infinite}}
.sw{{animation:sweep {LAP:g}s linear {turn:g}s infinite}}
.wk{{transform-box:fill-box;transform-origin:left;animation:work {LAP:g}s linear {turn:g}s infinite}}
.bt{{transform-box:fill-box;transform-origin:center;animation:beat {LAP:g}s ease-in-out {turn:g}s infinite}}
"""

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FULL_W} {FULL_H}" '
        f'width="{FULL_W}" height="{FULL_H}" role="img" aria-label="{escape(agent["title"])}">',
        style(["semi", "regular"], css),
        "<defs>"
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        f'<linearGradient id="band" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{t["mark"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{t["mark"]}" stop-opacity=".2"/>'
        f'<stop offset="1" stop-color="{t["mark"]}" stop-opacity="0"/></linearGradient>'
        "</defs>",
        f'<g transform="translate({x0} 0)"><g class="in">',
        f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>',
        f'<g clip-path="url(#c)">'
        f'<g transform="skewX(-18)"><rect class="sw" x="-190" y="-10" width="150" '
        f'height="{H + 20}" fill="url(#band)" opacity="0"/></g>'
        f'<rect class="wk" x="0" y="{H - 4}" width="{W}" height="4" fill="{t["mark"]}" opacity="0"/>'
        "</g>",
        f'<rect class="hl" x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="14.5" '
        f'fill="none" stroke="{t["mark"]}" stroke-width="3" opacity="{1 if lit else 0}"/>',
        text(32, 62, agent["title"], "semi", 26, t["title"]),
    ]
    for i, line in enumerate(wrap(agent["blurb"], "regular", 19, W - 64)):
        out.append(text(32, 102 + i * 28, line, "regular", 19, t["body"]))

    x, y = 32, H - 34
    if lang:
        out.append(f'<circle class="bt" cx="{x + 7}" cy="{y - 6}" r="7" '
                   f'fill="{LANG.get(lang, t["body"])}"/>')
        out.append(text(x + 22, y, lang, "regular", 17.5, t["body"]))
        x += 22 + width(lang, "regular", 17.5) + 26
    if stars:
        out.append(f'<g transform="translate({x:g} {y - 15}) scale(1.06)">'
                   f'<path class="spin" fill="{t["body"]}" d="{STAR}"/></g>')
        out.append(count_up(x + 23, y, stars, "semi", 17.5, t["body"],
                            start=arrive + .55, dur=.8))

    out.append("</g></g></svg>")
    return "".join(out)


# ------------------------------------------------------- contribution graph

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# Five steps of the same green per theme, empty to busiest, so the graph reads
# as part of the profile rather than GitHub's own widget pasted in.
LEVELS = {
    "light": ["#DCE4C2", "#B9D36A", "#93B92E", "#6A8F12", "#435C08"],
    "dark": ["#2B361A", "#4E6A14", "#7EA51A", "#A9D021", LIME],
}


def graph(theme: str) -> str:
    from datetime import date

    path = ROOT / "data" / "contributions.json"
    days = json.loads(path.read_text()) if path.exists() else []
    t = THEMES[theme]
    W, H = 1200, 336
    left, top = 40, 146

    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    best = max(days, key=lambda d: d["count"]) if days else None

    # Columns are weeks starting on Sunday, which is how GitHub lays it out.
    first = date.fromisoformat(days[0]["date"]) if days else date.today()
    offset = (first.weekday() + 1) % 7

    # A year is 53 or 54 columns depending on where it starts, so the square
    # size comes from the width available rather than a fixed number, which
    # pushed the last week off the card.
    ncols = (len(days) + offset + 6) // 7 or 53
    pitch = (W - 2 * left) / ncols
    gap = pitch * .19
    cell = pitch - gap

    css = f"""
@keyframes pop{{from{{transform:scale(0);opacity:0}}}}
@keyframes now{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.35)}}}}
@keyframes fade{{from{{opacity:0}}}}
.col{{animation:fade .01s both}}
.col rect{{transform-box:fill-box;transform-origin:center;animation:pop .35s cubic-bezier(.2,1.5,.4,1) both;animation-delay:inherit}}
.now{{transform-box:fill-box;transform-origin:center;animation:now 1.8s ease-in-out 3s infinite}}
.fade{{animation:fade .7s ease both}}
"""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{total} contributions in the last year">',
        style(["semi", "regular"], css),
        f'<rect width="{W}" height="{H}" rx="20" fill="{t["bg"]}"/>',
        '<g class="fade">',
        count_up(left, 62, total, "semi", 30, t["title"], start=.3, dur=1.1),
        text(left + width(f"{total} ", "semi", 30), 62,
             "contributions in the last year", "semi", 30, t["title"]),
    ]
    facts = [f"{active} active day{'s' if active != 1 else ''}"]
    if best and best["count"]:
        d = date.fromisoformat(best["date"])
        facts.append(f"busiest day {d.day} {MONTHS[d.month - 1]} "
                     f"with {best['count']}")
    out.append(text(left, 92, ", ".join(facts), "regular", 19, t["body"]))
    out.append("</g>")

    # Month names over the week they start in.
    seen = set()
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        col = (i + offset) // 7
        if dt.day <= 7 and (dt.year, dt.month) not in seen and col < ncols - 2:
            seen.add((dt.year, dt.month))
            out.append(text(left + col * pitch, top - 12,
                            MONTHS[dt.month - 1], "regular", 15, t["body"]))

    # One group per week, so the sweep is one delay per column rather than
    # one per square.
    cols: dict[int, list[str]] = {}
    for i, d in enumerate(days):
        col, row = divmod(i + offset, 7)
        last = i == len(days) - 1
        fill = LEVELS[theme][d["level"]]
        cls = ' class="now"' if last and not STATIC else ""
        cols.setdefault(col, []).append(
            f'<rect{cls} x="{left + col * pitch:.1f}" '
            f'y="{top + row * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
            f'rx="3.5" fill="{fill}"/>')
    for col, rects in cols.items():
        out.append(f'<g class="col" style="animation-delay:{.6 + col * .022:.3f}s">'
                   + "".join(rects) + "</g>")

    # The key, under the right edge.
    kx = W - left - 5 * pitch - 40
    ky = top + 7 * pitch + 12
    out.append(text(kx - 42, ky + 14, "Less", "regular", 15, t["body"]))
    for i, c in enumerate(LEVELS[theme]):
        out.append(f'<rect x="{kx + i * pitch:.1f}" y="{ky:.1f}" width="{cell:.1f}" '
                   f'height="{cell:.1f}" rx="3.5" fill="{c}"/>')
    out.append(text(kx + 5 * pitch + 6, ky + 14, "More", "regular", 15, t["body"]))

    out.append("</svg>")
    return "".join(out)


def main() -> None:
    CARDS.mkdir(exist_ok=True)
    (CARDS / "hero.svg").write_text(hero())
    for theme in THEMES:
        (CARDS / f"graph-{theme}.svg").write_text(graph(theme))
    for i, agent in enumerate(AGENTS):
        for theme in THEMES:
            (CARDS / f"{agent['key']}-{theme}.svg").write_text(card(i, agent, theme))
    for f in sorted(CARDS.glob("*.svg")):
        print(f"{f.name:22} {f.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
