"""Unit tests for scripts/sync-repos.py."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "sync-repos.py"
SPEC = importlib.util.spec_from_file_location("sync_repos", SCRIPT_PATH)
sync_repos = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(sync_repos)


class _FakeHeaders:
    def __init__(self, link: str | None = None):
        self._link = link

    def get(self, key: str, default=None):
        if key.lower() == "link":
            return self._link
        return default


class _FakeResp:
    def __init__(self, payload, status: int = 200, link: str | None = None):
        self._payload = payload
        self.status = status
        self.headers = _FakeHeaders(link)

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


SAMPLE_INDEX = """<!doctype html>
<html><body>
<strong id="agpl"><!-- REPO_AGPL_SUMMARY_START -->old<!-- REPO_AGPL_SUMMARY_END --></strong>
<div class="filter-bar"><!-- REPO_FILTERS_START -->old<!-- REPO_FILTERS_END --></div>
<p id="directory-status"><!-- REPO_STATUS_START -->old<!-- REPO_STATUS_END --></p>
<div id="repo-grid"><!-- REPO_GRID_START -->old<!-- REPO_GRID_END --></div>
</body></html>
"""


class SyncReposTests(unittest.TestCase):
    def _make_env(self, initial_repos: list[dict]):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        data_file = root / "repositories.json"
        index_file = root / "index.html"
        data_file.write_text(
            json.dumps(
                {
                    "organization": "ProjectNox-org",
                    "updated_at": "2026-11-17T00:00:00Z",
                    "repositories": initial_repos,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        index_file.write_text(SAMPLE_INDEX, encoding="utf-8")
        return tmp, data_file, index_file

    def test_url_validation(self):
        self.assertEqual(sync_repos.validate_url("https://github.com/ProjectNox-org"), "https://github.com/ProjectNox-org")
        self.assertEqual(sync_repos.validate_url("extensoes/#mihon"), "extensoes/#mihon")
        self.assertIsNone(sync_repos.validate_url("javascript:alert(1)"))
        self.assertIsNone(sync_repos.validate_url("data:text/html,<script>"))
        self.assertIsNone(sync_repos.validate_url("//evil.example.com"))

    def test_agpl_variants_unlicensed_other_missing_readme_and_xss(self):
        tmp, data_file, index_file = self._make_env(
            [
                {
                    "name": "repo-agpl",
                    "title": "Repo AGPL",
                    "category": "platforms",
                    "category_label": "Plataformas & Web",
                    "description": "Plataforma.",
                    "source_url": "https://github.com/ProjectNox-org/repo-agpl",
                    "docs_url": "https://github.com/ProjectNox-org/repo-agpl#readme",
                    "specific_action": {"label": "Bad", "url": "javascript:alert(1)", "external": True},
                },
                {
                    "name": "repo-removed",
                    "title": "Removed",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Removed.",
                },
            ]
        )
        self.addCleanup(tmp.cleanup)

        api_items = [
            {
                "name": "repo-agpl",
                "private": False,
                "default_branch": "main",
                "license": {"spdx_id": "AGPL-3.0-only"},
                "html_url": "https://github.com/ProjectNox-org/repo-agpl",
            },
            {
                "name": "repo-unlicensed",
                "private": False,
                "default_branch": "main",
                "license": None,
                "description": None,
                "language": None,
                "homepage": None,
                "html_url": "https://github.com/ProjectNox-org/repo-unlicensed",
            },
            {
                "name": "repo-apache",
                "private": False,
                "default_branch": "main",
                "license": {"spdx_id": "Apache-2.0"},
                "description": 'Special <script>alert(1)</script> & "quotes"',
                "language": "Python",
                "homepage": "javascript:alert(2)",
                "html_url": "https://github.com/ProjectNox-org/repo-apache",
            },
        ]

        def fake_urlopen(req, timeout=20):
            url = req.full_url
            if "/readme" in url:
                if "repo-unlicensed" in url:
                    raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
                return _FakeResp({"name": "README.md"})
            return _FakeResp(api_items)

        repos, changed = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=fake_urlopen,
        )
        self.assertTrue(changed)
        by_name = {r["name"]: r for r in repos}
        self.assertEqual(by_name["repo-agpl"]["license_status"], "verified_agpl")
        self.assertEqual(by_name["repo-unlicensed"]["license"], "Licença não identificada")
        self.assertEqual(by_name["repo-unlicensed"]["license_status"], "unidentified")
        self.assertEqual(by_name["repo-unlicensed"]["category"], "other")
        self.assertEqual(by_name["repo-unlicensed"]["category_label"], "Outros projetos")
        self.assertIsNone(by_name["repo-unlicensed"]["docs_url"])
        self.assertEqual(by_name["repo-apache"]["license"], "Apache-2.0")
        self.assertEqual(by_name["repo-apache"]["license_status"], "verified_other")
        self.assertIsNone(by_name["repo-apache"]["specific_action"])

        html_out = index_file.read_text(encoding="utf-8")
        self.assertNotIn("javascript:alert", html_out)
        self.assertNotIn("<script>alert(1)</script>", html_out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_out)
        self.assertIn("Sem README", html_out)
        self.assertIn("3 projetos disponíveis", html_out)
        self.assertIn("1 de 3 repositórios públicos verificados", html_out)
        self.assertIn("Outros projetos (2)", html_out)

        _, changed_again = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=fake_urlopen,
        )
        self.assertFalse(changed_again)

        # --render-only mode must render without network calls
        repos_ro, changed_ro = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            render_only=True,
        )
        self.assertEqual(len(repos_ro), 3)
        self.assertFalse(changed_ro)

    def test_pagination_and_api_failure_preservation(self):
        tmp, data_file, index_file = self._make_env(
            [
                {
                    "name": "repo-1",
                    "title": "Repo 1",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Desc 1",
                }
            ]
        )
        self.addCleanup(tmp.cleanup)

        def paged_urlopen(req, timeout=20):
            url = req.full_url
            if "/readme" in url:
                return _FakeResp({"name": "README.md"})
            if "page=1" in url:
                return _FakeResp(
                    [{"name": "repo-1", "private": False, "license": {"spdx_id": "AGPL-3.0"}, "html_url": "https://github.com/ProjectNox-org/repo-1"}],
                    link='<https://api.github.com/orgs/ProjectNox-org/repos?page=2>; rel="next"',
                )
            return _FakeResp(
                [{"name": "repo-2", "private": False, "license": {"spdx_id": "AGPL-3.0"}, "html_url": "https://github.com/ProjectNox-org/repo-2"}]
            )

        repos, _ = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=paged_urlopen,
        )
        self.assertEqual(len(repos), 2)

        before_json = data_file.read_text(encoding="utf-8")
        with self.assertRaises(RuntimeError):
            sync_repos.sync_repositories(
                data_file=data_file,
                index_file=index_file,
                urlopen_fn=lambda req, timeout=20: _FakeResp([], status=503),
            )
        self.assertEqual(data_file.read_text(encoding="utf-8"), before_json)

    def test_check_readme_exists_statuses(self):
        self.assertEqual(
            sync_repos.check_readme_exists("ProjectNox-org", "ok", urlopen_fn=lambda req, timeout=10: _FakeResp({}, status=200)),
            "confirmed",
        )

        def raise_404(req, timeout=10):
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

        def raise_403(req, timeout=10):
            raise urllib.error.HTTPError(req.full_url, 403, "Rate Limit", {}, None)

        def raise_timeout(req, timeout=10):
            raise TimeoutError("timed out")

        def raise_url_err(req, timeout=10):
            raise urllib.error.URLError("dns error")

        self.assertEqual(sync_repos.check_readme_exists("ProjectNox-org", "missing", urlopen_fn=raise_404), "missing")
        self.assertEqual(sync_repos.check_readme_exists("ProjectNox-org", "ratelimit", urlopen_fn=raise_403), "unavailable")
        self.assertEqual(sync_repos.check_readme_exists("ProjectNox-org", "timeout", urlopen_fn=raise_timeout), "unavailable")
        self.assertEqual(sync_repos.check_readme_exists("ProjectNox-org", "neterr", urlopen_fn=raise_url_err), "unavailable")

    def test_existing_repo_readme_added_removed_and_transient_unavailable(self):
        tmp, data_file, index_file = self._make_env(
            [
                {
                    "name": "repo-gains-readme",
                    "title": "Gains",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Gains README.",
                    "source_url": "https://github.com/ProjectNox-org/repo-gains-readme",
                    "docs_url": None,
                },
                {
                    "name": "repo-loses-readme",
                    "title": "Loses",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Loses README.",
                    "source_url": "https://github.com/ProjectNox-org/repo-loses-readme",
                    "docs_url": "https://github.com/ProjectNox-org/repo-loses-readme#readme",
                },
                {
                    "name": "repo-curated-docs",
                    "title": "Curated",
                    "category": "docs",
                    "category_label": "Documentação & Comunidade",
                    "description": "Curated docs.",
                    "source_url": "https://github.com/ProjectNox-org/repo-curated-docs",
                    "docs_url": "https://github.com/ProjectNox-org/repo-curated-docs/blob/main/CONTRIBUTING.md",
                },
                {
                    "name": "repo-transient-keep",
                    "title": "Keep",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Transient keep.",
                    "source_url": "https://github.com/ProjectNox-org/repo-transient-keep",
                    "docs_url": "https://github.com/ProjectNox-org/repo-transient-keep#readme",
                },
                {
                    "name": "repo-transient-null",
                    "title": "Null",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Transient null.",
                    "source_url": "https://github.com/ProjectNox-org/repo-transient-null",
                    "docs_url": None,
                },
            ]
        )
        self.addCleanup(tmp.cleanup)

        names = [
            "repo-gains-readme",
            "repo-loses-readme",
            "repo-curated-docs",
            "repo-transient-keep",
            "repo-transient-null",
            "repo-new-unavailable",
        ]
        api_items = [
            {
                "name": n,
                "private": False,
                "default_branch": "main",
                "license": {"spdx_id": "AGPL-3.0"},
                "html_url": f"https://github.com/ProjectNox-org/{n}",
            }
            for n in names
        ]

        def fake_urlopen(req, timeout=20):
            url = req.full_url
            if "/readme" in url:
                if "repo-gains-readme" in url:
                    return _FakeResp({"name": "README.md"}, status=200)
                if "repo-loses-readme" in url or "repo-curated-docs" in url:
                    raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
                if "repo-transient-keep" in url or "repo-new-unavailable" in url:
                    raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
                raise TimeoutError("network timeout")
            return _FakeResp(api_items)

        repos, changed = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=fake_urlopen,
        )
        self.assertTrue(changed)
        by_name = {r["name"]: r for r in repos}
        self.assertEqual(by_name["repo-gains-readme"]["docs_url"], "https://github.com/ProjectNox-org/repo-gains-readme#readme")
        self.assertIsNone(by_name["repo-loses-readme"]["docs_url"])
        self.assertEqual(
            by_name["repo-curated-docs"]["docs_url"],
            "https://github.com/ProjectNox-org/repo-curated-docs/blob/main/CONTRIBUTING.md",
        )
        self.assertEqual(by_name["repo-transient-keep"]["docs_url"], "https://github.com/ProjectNox-org/repo-transient-keep#readme")
        self.assertIsNone(by_name["repo-transient-null"]["docs_url"])
        self.assertIsNone(by_name["repo-new-unavailable"]["docs_url"])

    def test_catalog_scaling_and_over_100_paginated_repos(self):
        for count in (1, 2, 4, 11, 12, 20, 50):
            tmp, _, index_file = self._make_env([])
            sample = [
                {
                    "name": f"repo-{i}",
                    "title": f"Repo {i}",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": f"Desc {i}",
                    "license": "AGPL-3.0",
                    "license_status": "verified_agpl",
                    "source_url": f"https://github.com/ProjectNox-org/repo-{i}",
                    "docs_url": f"https://github.com/ProjectNox-org/repo-{i}#readme",
                    "status_note": "Nota de status" if i == 0 else None,
                }
                for i in range(count)
            ]
            sync_repos.update_index_html(sample, index_file)
            rendered = index_file.read_text(encoding="utf-8")
            tmp.cleanup()
            self.assertEqual(rendered.count('<article class="card repo-card"'), count)
            expected_label = "1 projeto disponível" if count == 1 else f"{count} projetos disponíveis"
            self.assertIn(expected_label, rendered)
            self.assertIn('<p class="repo-status-note">Nota de status</p>', rendered)

        # >100 repos paginated across 2 API pages
        tmp, data_file, index_file = self._make_env([])
        self.addCleanup(tmp.cleanup)
        page1 = [
            {
                "name": f"org-repo-{i:03d}",
                "private": False,
                "default_branch": "main",
                "license": {"spdx_id": "AGPL-3.0"},
                "html_url": f"https://github.com/ProjectNox-org/org-repo-{i:03d}",
            }
            for i in range(100)
        ]
        page2 = [
            {
                "name": f"org-repo-{i:03d}",
                "private": False,
                "default_branch": "main",
                "license": {"spdx_id": "AGPL-3.0"},
                "html_url": f"https://github.com/ProjectNox-org/org-repo-{i:03d}",
            }
            for i in range(100, 105)
        ]

        def many_urlopen(req, timeout=20):
            url = req.full_url
            if "/readme" in url:
                return _FakeResp({"name": "README.md"}, status=200)
            if "page=1" in url:
                return _FakeResp(page1, link='<https://api.github.com/orgs/ProjectNox-org/repos?page=2>; rel="next"')
            return _FakeResp(page2)

        repos, changed = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=many_urlopen,
        )
        self.assertTrue(changed)
        self.assertEqual(len(repos), 105)
        html_out = index_file.read_text(encoding="utf-8")
        self.assertEqual(html_out.count('<article class="card repo-card"'), 105)
        self.assertIn("105 projetos disponíveis", html_out)

    def test_backslashes_atomic_permissions_private_rename_and_branch_license_updates(self):
        tmp, data_file, index_file = self._make_env(
            [
                {
                    "name": "repo-existing",
                    "title": "Existing",
                    "category": "unknown_cat",
                    "category_label": "Categoria Custom",
                    "description": r"Windows path C:\Users\test\1 and \g<0>",
                    "default_branch": "master",
                    "license": "MIT",
                    "license_status": "verified_other",
                    "source_url": "https://github.com/ProjectNox-org/old-url",
                    "docs_url": "https://github.com/ProjectNox-org/repo-existing#readme",
                },
                {
                    "name": "repo-turned-private",
                    "title": "Private",
                    "category": "tools",
                    "category_label": "Ferramentas & IA",
                    "description": "Will become private.",
                },
            ]
        )
        self.addCleanup(tmp.cleanup)

        api_items = [
            {
                "name": "repo-existing",
                "private": False,
                "default_branch": "main",
                "license": {"spdx_id": "AGPL-3.0"},
                "html_url": "https://github.com/ProjectNox-org/repo-existing",
            },
            {
                "name": "repo-turned-private",
                "private": True,
                "default_branch": "main",
                "license": {"spdx_id": "AGPL-3.0"},
                "html_url": "https://github.com/ProjectNox-org/repo-turned-private",
            },
            {
                "name": "repo-renamed-new",
                "private": False,
                "default_branch": "develop",
                "license": {"spdx_id": "AGPL-3.0"},
                "description": r"Regex escape \1 \n \u1234",
                "homepage": None,
                "html_url": "https://github.com/ProjectNox-org/repo-renamed-new",
            },
        ]

        def fake_urlopen(req, timeout=20):
            if "/readme" in req.full_url:
                return _FakeResp({"name": "README.md"}, status=200)
            return _FakeResp(api_items)

        repos, changed = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=fake_urlopen,
        )
        self.assertTrue(changed)
        by_name = {r["name"]: r for r in repos}
        self.assertNotIn("repo-turned-private", by_name)
        self.assertIn("repo-renamed-new", by_name)
        self.assertEqual(by_name["repo-existing"]["default_branch"], "main")
        self.assertEqual(by_name["repo-existing"]["license"], "AGPL-3.0")
        self.assertEqual(by_name["repo-existing"]["source_url"], "https://github.com/ProjectNox-org/repo-existing")
        self.assertEqual(by_name["repo-renamed-new"]["category"], "other")

        html_out = index_file.read_text(encoding="utf-8")
        self.assertIn(r"C:\Users\test\1 and \g&lt;0&gt;", html_out)
        self.assertIn(r"Regex escape \1 \n \u1234", html_out)
        self.assertEqual(data_file.stat().st_mode & 0o777, 0o644)
        self.assertEqual(index_file.stat().st_mode & 0o777, 0o644)


if __name__ == "__main__":
    unittest.main()
