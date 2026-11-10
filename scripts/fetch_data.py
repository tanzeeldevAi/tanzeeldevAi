#!/usr/bin/env python3
"""Refresh data/github.json: star counts, languages and the repo total.

Standard library only. In the Action it authenticates with the workflow's own
GITHUB_TOKEN; without one it still works, at GitHub's 60 requests an hour.

If GitHub cannot be reached the old file is left alone. Yesterday's numbers
are a better thing to show than a broken card.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

USER = "tanzeeldevAi"
DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "github.json"
CALENDAR = DATA / "contributions.json"


def get(url: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-cards",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def contributions() -> list[dict]:
    """The last year of the contribution calendar, one entry per day.

    There is no API for this without a token with more scope than the
    workflow's own, so it is read from the same public page the profile
    renders. The page gives each day a level (0-4) on one element and its
    count in a tooltip on another, tied together by an id.
    """
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": f"{USER}-profile-cards"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")

    days = {}
    for m in re.finditer(r'<td[^>]*data-date="(\d{4}-\d\d-\d\d)"[^>]*'
                         r'id="(contribution-day-component-\d+-\d+)"[^>]*'
                         r'data-level="(\d)"', html):
        days[m.group(2)] = {"date": m.group(1), "level": int(m.group(3)),
                            "count": 0}
    for m in re.finditer(r'<tool-tip[^>]*for="(contribution-day-component-'
                         r'\d+-\d+)"[^>]*>\s*(\d+) contribution', html):
        if m.group(1) in days:
            days[m.group(1)]["count"] = int(m.group(2))
    if len(days) < 300:
        raise ValueError(f"calendar page changed shape ({len(days)} days)")
    return sorted(days.values(), key=lambda d: d["date"])


def main() -> int:
    try:
        repos, page = [], 1
        while True:
            batch = get(f"https://api.github.com/users/{USER}/repos"
                        f"?per_page=100&page={page}")
            repos += batch
            if len(batch) < 100:
                break
            page += 1
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"could not reach GitHub ({exc}); keeping the existing data")
        return 0 if OUT.exists() else 1

    # Forks are someone else's work, so their stars are not counted here.
    own = [r for r in repos if not r.get("fork")]
    data = {
        "public_repos": len(repos),
        "total_stars": sum(r["stargazers_count"] for r in own),
        "repos": {r["name"]: {"stars": r["stargazers_count"],
                              "language": r["language"]} for r in own},
    }
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"{data['public_repos']} repos, {data['total_stars']} stars")

    # Separate from the stars, so a change to the calendar page cannot cost
    # the cards their star counts.
    try:
        days = contributions()
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"could not read the contribution calendar ({exc}); keeping it")
        return 0
    CALENDAR.write_text(json.dumps(days) + "\n")
    print(f"{len(days)} days, {sum(d['count'] for d in days)} contributions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
