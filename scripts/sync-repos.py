#!/usr/bin/env python3
"""Synchronize live GitHub metadata into data/repositories.json without runtime API calls."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "repositories.json"
ORG = "ProjectNox-org"


def fetch_org_repos() -> dict[str, dict]:
    url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100&type=public"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ProjectNox-Portal-Sync/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        items = json.loads(resp.read().decode("utf-8"))
    return {item["name"]: item for item in items if not item.get("private")}


def main() -> int:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    live = fetch_org_repos()

    known_names = {repo["name"] for repo in data["repositories"]}
    for repo in data["repositories"]:
        remote = live.get(repo["name"])
        if not remote:
            continue
        repo["default_branch"] = remote.get("default_branch", repo["default_branch"])
        license_info = remote.get("license")
        if license_info and license_info.get("spdx_id") not in (None, "NOASSERTION"):
            repo["license"] = license_info["spdx_id"]
            repo["license_status"] = "verified"
        else:
            repo["license"] = "Sem arquivo LICENSE"
            repo["license_status"] = "unlicensed"

    missing = sorted(set(live.keys()) - known_names)
    if missing:
        print(f"Aviso: novos repositórios públicos detectados no GitHub: {', '.join(missing)}", file=sys.stderr)

    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Sincronizado com sucesso ({len(data['repositories'])} repositórios).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
