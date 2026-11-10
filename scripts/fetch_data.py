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
import sys
import urllib.error
import urllib.request
from pathlib import Path

USER = "tanzeeldevAi"
OUT = Path(__file__).resolve().parent.parent / "data" / "github.json"


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
