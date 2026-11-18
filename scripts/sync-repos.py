#!/usr/bin/env python3
"""Synchronize GitHub metadata into data/repositories.json and render static repo cards in index.html."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "repositories.json"
INDEX_FILE = ROOT / "index.html"
ORG = "ProjectNox-org"

ICONS = {
    "book": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    "activity": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "code": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "package": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    "server": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
    "sparkles": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
    "ticket": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/></svg>',
    "globe": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "shield": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
}

REPO_BTN_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>'
DOC_BTN_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
ACTION_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'


def fetch_org_repos() -> dict[str, dict]:
    url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100&type=public"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ProjectNox-Portal-Sync/2.0",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        items = json.loads(resp.read().decode("utf-8"))
    return {item["name"]: item for item in items if not item.get("private")}


def render_card(repo: dict) -> str:
    esc = html.escape
    icon_svg = ICONS.get(repo.get("icon", "code"), ICONS["code"])
    search_blob = " ".join(
        [
            repo["name"],
            repo["title"],
            repo["category_label"],
            repo["description"],
            repo.get("meta", ""),
            repo.get("license", ""),
            repo.get("search_keywords", ""),
        ]
    )

    specific_html = ""
    sa = repo.get("specific_action")
    if sa and sa.get("url"):
        ext_attrs = ' target="_blank" rel="noopener noreferrer"' if sa.get("external") else ""
        specific_html = (
            f'                <div class="repo-primary-action">\n'
            f'                  <a class="button gold sm repo-action-full" href="{esc(sa["url"])}"{ext_attrs}>\n'
            f'                    {ACTION_ICON}\n'
            f'                    <span>{esc(sa["label"])}</span>\n'
            f'                  </a>\n'
            f'                </div>\n'
        )

    return (
        f'              <article class="card repo-card" data-category="{esc(repo["category"])}" data-search="{esc(search_blob)}">\n'
        f'                <div class="repo-card-top">\n'
        f'                  <div class="repo-ident">\n'
        f'                    <span class="repo-icon" aria-hidden="true">{icon_svg}</span>\n'
        f'                    <div class="repo-title-group">\n'
        f'                      <h3>{esc(repo["title"])}</h3>\n'
        f'                      <span class="repo-slug">{esc(repo["name"])}</span>\n'
        f'                    </div>\n'
        f'                  </div>\n'
        f'                  <span class="pill green">{esc(repo["license"])}</span>\n'
        f'                </div>\n'
        f'                <p class="repo-desc">{esc(repo["description"])}</p>\n'
        f'                <div class="repo-meta-row">\n'
        f'                  <span class="repo-meta-chip">{esc(repo["category_label"])}</span>\n'
        f'                  <span class="repo-meta-chip">{esc(repo.get("meta", ""))}</span>\n'
        f'                </div>\n'
        f'                <div class="repo-actions-wrap">\n'
        f'{specific_html}'
        f'                  <div class="repo-universal-actions">\n'
        f'                    <a class="button secondary sm" href="{esc(repo["source_url"])}" target="_blank" rel="noopener noreferrer">\n'
        f'                      {REPO_BTN_ICON}\n'
        f'                      <span>Repositório</span>\n'
        f'                    </a>\n'
        f'                    <a class="button secondary sm" href="{esc(repo["docs_url"])}" target="_blank" rel="noopener noreferrer">\n'
        f'                      {DOC_BTN_ICON}\n'
        f'                      <span>Documentação</span>\n'
        f'                    </a>\n'
        f'                  </div>\n'
        f'                </div>\n'
        f'              </article>'
    )


def update_index_html(repos: list[dict]) -> None:
    if not INDEX_FILE.exists():
        return
    content = INDEX_FILE.read_text(encoding="utf-8")
    cards_html = "\n\n".join(render_card(r) for r in repos)
    new_block = f"<!-- REPO_GRID_START -->\n{cards_html}\n              <!-- REPO_GRID_END -->"
    updated = re.sub(
        r"<!-- REPO_GRID_START -->.*?<!-- REPO_GRID_END -->",
        new_block,
        content,
        flags=re.DOTALL,
    )
    if updated != content:
        INDEX_FILE.write_text(updated, encoding="utf-8")


def main() -> int:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if "--render-only" not in sys.argv:
        live = fetch_org_repos()
    else:
        live = {}

    known_names = {repo["name"] for repo in data["repositories"]}
    for repo in data["repositories"]:
        remote = live.get(repo["name"])
        if not remote:
            continue
        repo["default_branch"] = remote.get("default_branch", repo["default_branch"])
        license_info = remote.get("license")
        if license_info and license_info.get("spdx_id") not in (None, "NOASSERTION"):
            repo["license"] = license_info["spdx_id"]
        if remote.get("description") and not repo.get("description"):
            repo["description"] = remote["description"]

    for name in sorted(set(live.keys()) - known_names):
        remote = live[name]
        lic = remote.get("license", {}).get("spdx_id") if remote.get("license") else "AGPL-3.0"
        data["repositories"].append(
            {
                "name": name,
                "title": name,
                "category": "tools",
                "category_label": "Outros",
                "icon": "code",
                "description": remote.get("description") or "Repositório público da organização ProjectNox-org.",
                "meta": remote.get("language") or remote.get("default_branch", "main"),
                "license": lic or "AGPL-3.0",
                "default_branch": remote.get("default_branch", "main"),
                "source_url": remote["html_url"],
                "docs_url": f'{remote["html_url"]}#readme',
                "specific_action": {"label": "Acessar serviço", "url": remote["homepage"], "external": True} if remote.get("homepage") else None,
                "search_keywords": (remote.get("language") or "").lower(),
            }
        )
        print(f"Novo repositório adicionado automaticamente: {name}", file=sys.stderr)

    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_index_html(data["repositories"])
    print(f"Sincronizado e renderizado ({len(data['repositories'])} repositórios).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
