#!/usr/bin/env python3
"""Synchronize GitHub metadata into data/repositories.json and render static HTML in index.html."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "repositories.json"
INDEX_FILE = ROOT / "index.html"
ORG = "ProjectNox-org"

ICONS = {
    "book": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    "activity": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "code": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "package": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    "server": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
    "sparkles": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
    "ticket": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/></svg>',
    "globe": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "shield": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
}

CATEGORY_ORDER = [
    ("platforms", "Plataformas & Web"),
    ("extensions", "Extensões"),
    ("infrastructure", "Infraestrutura"),
    ("tools", "Ferramentas & IA"),
    ("community", "Suporte"),
    ("institutional", "Institucional"),
]

REPO_BTN_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>'
DOC_BTN_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
ACTION_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'


def _default_urlopen(req: urllib.request.Request, timeout: int = 20):
    return urllib.request.urlopen(req, timeout=timeout)


def _parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        segs = [s.strip() for s in part.split(";")]
        if len(segs) >= 2 and 'rel="next"' in segs[1:]:
            url = segs[0]
            if url.startswith("<") and url.endswith(">"):
                return url[1:-1]
    return None


def fetch_org_repos(
    org: str = ORG,
    urlopen_fn: Callable = _default_urlopen,
) -> dict[str, dict]:
    """Fetch complete paginated list of public non-private repositories from GitHub."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ProjectNox-Portal-Sync/3.0",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    next_url: str | None = f"https://api.github.com/orgs/{org}/repos?per_page=100&type=public&page=1"
    collected: dict[str, dict] = {}
    pages_seen = 0

    while next_url:
        req = urllib.request.Request(next_url, headers=headers)
        with urlopen_fn(req, timeout=20) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                raise RuntimeError(f"GitHub API returned unexpected HTTP {status}")
            payload = json.loads(resp.read().decode("utf-8"))
            if not isinstance(payload, list):
                raise RuntimeError("GitHub API response payload is not a list")
            for item in payload:
                if not item.get("private") and item.get("name"):
                    collected[item["name"]] = item
            link_header = resp.headers.get("Link") if hasattr(resp, "headers") and resp.headers else None
            next_url = _parse_next_link(link_header)
            pages_seen += 1
            if pages_seen > 50:
                raise RuntimeError("Pagination safety limit exceeded")

    return collected


def resolve_license(remote: dict) -> tuple[str, str]:
    """Resolve license SPDX ID and verification status without guessing."""
    license_info = remote.get("license")
    if isinstance(license_info, dict):
        spdx = license_info.get("spdx_id")
        if spdx and spdx not in ("NOASSERTION", "NONE"):
            status = "verified_agpl" if spdx == "AGPL-3.0" else "verified_other"
            return spdx, status
    return "Licença não identificada", "unidentified"


def esc(val: object) -> str:
    return html.escape("" if val is None else str(val), quote=True)


def render_card(repo: dict) -> str:
    icon_svg = ICONS.get(repo.get("icon", "code"), ICONS["code"])
    cat_key = repo.get("category", "tools")
    cat_label = repo.get("category_label", "Outros")
    lic_text = repo.get("license") or "Licença não identificada"
    lic_status = repo.get("license_status", "unidentified")
    lic_class = "repo-license" if lic_status == "verified_agpl" else "repo-license neutral"

    search_blob = " ".join(
        str(x)
        for x in (
            repo.get("name", ""),
            repo.get("title", ""),
            cat_label,
            repo.get("description", ""),
            repo.get("meta", ""),
            lic_text,
            repo.get("search_keywords", ""),
        )
        if x
    )

    specific_html = ""
    sa = repo.get("specific_action")
    if isinstance(sa, dict) and sa.get("url") and sa.get("label"):
        ext_attrs = ' target="_blank" rel="noopener noreferrer"' if sa.get("external") else ""
        specific_html = (
            f'                <div class="repo-primary-action">\n'
            f'                  <a class="button primary sm repo-action-full" href="{esc(sa["url"])}"{ext_attrs}>\n'
            f'                    {ACTION_ICON}\n'
            f'                    <span>{esc(sa["label"])}</span>\n'
            f'                  </a>\n'
            f'                </div>\n'
        )

    return (
        f'              <article class="card repo-card" data-category="{esc(cat_key)}" data-search="{esc(search_blob)}">\n'
        f'                <div class="repo-card-top">\n'
        f'                  <div class="repo-ident">\n'
        f'                    <span class="repo-icon cat-{esc(cat_key)}" aria-hidden="true">{icon_svg}</span>\n'
        f'                    <div class="repo-title-group">\n'
        f'                      <h3>{esc(repo.get("title") or repo.get("name"))}</h3>\n'
        f'                      <span class="repo-slug">{esc(repo.get("name"))}</span>\n'
        f'                    </div>\n'
        f'                  </div>\n'
        f'                  <span class="{lic_class}">{esc(lic_text)}</span>\n'
        f'                </div>\n'
        f'                <p class="repo-desc">{esc(repo.get("description"))}</p>\n'
        f'                <div class="repo-meta-row">\n'
        f'                  <span class="repo-meta-chip">{esc(cat_label)}</span>\n'
        f'                  <span class="repo-meta-chip">{esc(repo.get("meta") or repo.get("default_branch", "main"))}</span>\n'
        f'                </div>\n'
        f'                <div class="repo-actions-wrap">\n'
        f'{specific_html}'
        f'                  <div class="repo-universal-actions">\n'
        f'                    <a class="button secondary sm" href="{esc(repo.get("source_url") or "#")}" target="_blank" rel="noopener noreferrer">\n'
        f'                      {REPO_BTN_ICON}\n'
        f'                      <span>Repositório</span>\n'
        f'                    </a>\n'
        f'                    <a class="button secondary sm" href="{esc(repo.get("docs_url") or "#")}" target="_blank" rel="noopener noreferrer">\n'
        f'                      {DOC_BTN_ICON}\n'
        f'                      <span>Documentação</span>\n'
        f'                    </a>\n'
        f'                  </div>\n'
        f'                </div>\n'
        f'              </article>'
    )


def render_filters(repos: list[dict]) -> str:
    counts: dict[str, int] = {}
    labels: dict[str, str] = dict(CATEGORY_ORDER)
    for r in repos:
        c = r.get("category", "tools")
        counts[c] = counts.get(c, 0) + 1
        if c not in labels:
            labels[c] = r.get("category_label", c.title())

    chips = [
        f'                <button class="filter-chip" type="button" data-category="all" aria-pressed="true">Todos ({len(repos)})</button>'
    ]
    for key, label in CATEGORY_ORDER:
        if counts.get(key, 0) > 0:
            chips.append(
                f'                <button class="filter-chip" type="button" data-category="{esc(key)}" aria-pressed="false">{esc(label)} ({counts[key]})</button>'
            )
    for key, count in counts.items():
        if key not in dict(CATEGORY_ORDER) and count > 0:
            chips.append(
                f'                <button class="filter-chip" type="button" data-category="{esc(key)}" aria-pressed="false">{esc(labels[key])} ({count})</button>'
            )
    return "\n".join(chips)


def render_agpl_summary(repos: list[dict]) -> str:
    total = len(repos)
    agpl_count = sum(1 for r in repos if r.get("license_status") == "verified_agpl")
    if total > 0 and agpl_count == total:
        return f"Todos os {total} repositórios públicos verificados de ProjectNox-org adotam a GNU AGPL-3.0"
    return f"{agpl_count} de {total} repositórios públicos verificados de ProjectNox-org adotam a GNU AGPL-3.0"


def update_index_html(repos: list[dict], index_file: Path = INDEX_FILE) -> bool:
    if not index_file.exists():
        return False
    original = index_file.read_text(encoding="utf-8")
    updated = original

    cards_html = "\n\n".join(render_card(r) for r in repos)
    updated = re.sub(
        r"<!-- REPO_GRID_START -->.*?<!-- REPO_GRID_END -->",
        f"<!-- REPO_GRID_START -->\n{cards_html}\n              <!-- REPO_GRID_END -->",
        updated,
        flags=re.DOTALL,
    )

    filters_html = render_filters(repos)
    updated = re.sub(
        r"<!-- REPO_FILTERS_START -->.*?<!-- REPO_FILTERS_END -->",
        f"<!-- REPO_FILTERS_START -->\n{filters_html}\n              <!-- REPO_FILTERS_END -->",
        updated,
        flags=re.DOTALL,
    )

    updated = re.sub(
        r"<!-- REPO_STATUS_START -->.*?<!-- REPO_STATUS_END -->",
        f"<!-- REPO_STATUS_START -->{len(repos)} projetos disponíveis<!-- REPO_STATUS_END -->",
        updated,
        flags=re.DOTALL,
    )

    updated = re.sub(
        r"<!-- REPO_AGPL_SUMMARY_START -->.*?<!-- REPO_AGPL_SUMMARY_END -->",
        f"<!-- REPO_AGPL_SUMMARY_START -->{esc(render_agpl_summary(repos))}<!-- REPO_AGPL_SUMMARY_END -->",
        updated,
        flags=re.DOTALL,
    )

    if updated != original:
        index_file.write_text(updated, encoding="utf-8")
        return True
    return False


def sync_repositories(
    data_file: Path = DATA_FILE,
    index_file: Path = INDEX_FILE,
    render_only: bool = False,
    urlopen_fn: Callable = _default_urlopen,
) -> tuple[list[dict], bool]:
    """Sync metadata idempotently and update index.html."""
    data = json.loads(data_file.read_text(encoding="utf-8"))
    original_repos = json.loads(json.dumps(data.get("repositories", [])))

    if render_only:
        repos = data.get("repositories", [])
        html_changed = update_index_html(repos, index_file)
        return repos, html_changed

    live = fetch_org_repos(org=data.get("organization", ORG), urlopen_fn=urlopen_fn)
    if not live:
        raise RuntimeError("Empty repository inventory returned; aborting to protect catalog")

    # Keep only repositories confirmed still public in the full paginated inventory
    updated_repos: list[dict] = []
    known_names: set[str] = set()
    for repo in data.get("repositories", []):
        name = repo["name"]
        remote = live.get(name)
        if remote is None:
            continue
        known_names.add(name)
        lic_text, lic_status = resolve_license(remote)
        repo["default_branch"] = remote.get("default_branch") or repo.get("default_branch", "main")
        repo["license"] = lic_text
        repo["license_status"] = lic_status
        if not repo.get("description"):
            repo["description"] = remote.get("description") or "Repositório público da organização ProjectNox-org."
        updated_repos.append(repo)

    # Append newly discovered public repositories without inventing descriptions
    for name in sorted(set(live.keys()) - known_names):
        remote = live[name]
        lic_text, lic_status = resolve_license(remote)
        homepage = remote.get("homepage")
        updated_repos.append(
            {
                "name": name,
                "title": name,
                "category": "tools",
                "category_label": "Ferramentas & IA",
                "icon": "code",
                "description": remote.get("description") or "Repositório público da organização ProjectNox-org.",
                "meta": remote.get("language") or remote.get("default_branch") or "main",
                "license": lic_text,
                "license_status": lic_status,
                "default_branch": remote.get("default_branch") or "main",
                "source_url": remote.get("html_url") or f"https://github.com/{ORG}/{name}",
                "docs_url": f'{remote.get("html_url") or f"https://github.com/{ORG}/{name}"}#readme',
                "specific_action": (
                    {"label": "Acessar serviço", "url": homepage, "external": True}
                    if homepage
                    else None
                ),
                "search_keywords": (remote.get("language") or "").lower(),
            }
        )
        print(f"Novo repositório detectado: {name}", file=sys.stderr)

    data_changed = updated_repos != original_repos
    if data_changed:
        data["repositories"] = updated_repos
        data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    html_changed = update_index_html(updated_repos, index_file)
    return updated_repos, (data_changed or html_changed)


def main() -> int:
    render_only = "--render-only" in sys.argv
    repos, changed = sync_repositories(render_only=render_only)
    state = "atualizado" if changed else "sem alterações (idempotente)"
    print(f"Catálogo processado ({len(repos)} repositórios, {state}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
