"""Unit tests for scripts/sync-repos.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
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

    def test_agpl_unlicensed_other_and_new_repo(self):
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
                "license": {"spdx_id": "AGPL-3.0"},
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
                "description": "Special <script>alert(1)</script> & \"quotes\"",
                "language": "Python",
                "homepage": "https://example.com",
                "html_url": "https://github.com/ProjectNox-org/repo-apache",
            },
        ]

        repos, changed = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=lambda req, timeout=20: _FakeResp(api_items),
        )
        self.assertTrue(changed)
        names = [r["name"] for r in repos]
        self.assertEqual(names, ["repo-agpl", "repo-apache", "repo-unlicensed"])

        by_name = {r["name"]: r for r in repos}
        self.assertEqual(by_name["repo-agpl"]["license_status"], "verified_agpl")
        self.assertEqual(by_name["repo-unlicensed"]["license"], "Licença não identificada")
        self.assertEqual(by_name["repo-unlicensed"]["license_status"], "unidentified")
        self.assertEqual(by_name["repo-apache"]["license"], "Apache-2.0")
        self.assertEqual(by_name["repo-apache"]["license_status"], "verified_other")

        html_out = index_file.read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)</script>", html_out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_out)
        self.assertIn("3 projetos disponíveis", html_out)
        self.assertIn("1 de 3 repositórios públicos verificados", html_out)
        self.assertIn("Todos (3)", html_out)

        # Idempotency check: second run with identical data makes zero changes
        _, changed_again = sync_repos.sync_repositories(
            data_file=data_file,
            index_file=index_file,
            urlopen_fn=lambda req, timeout=20: _FakeResp(api_items),
        )
        self.assertFalse(changed_again)

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

        # API failure must raise and preserve existing catalog intact
        before_json = data_file.read_text(encoding="utf-8")
        with self.assertRaises(RuntimeError):
            sync_repos.sync_repositories(
                data_file=data_file,
                index_file=index_file,
                urlopen_fn=lambda req, timeout=20: _FakeResp([], status=503),
            )
        self.assertEqual(data_file.read_text(encoding="utf-8"), before_json)


if __name__ == "__main__":
    unittest.main()
