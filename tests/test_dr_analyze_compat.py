import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "daily-report" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import dr_analyze


class AnalyzeConfigCompatibilityTests(unittest.TestCase):
    def test_normalize_repository_adds_git_user_for_legacy_config(self):
        with patch.object(dr_analyze, "git_config_user", return_value={"name": "Ned", "email": "ned@example.com", "source": "local"}):
            repo = dr_analyze.normalize_repository({"name": "legacy", "path": "/tmp/legacy", "group": "ability"})

        self.assertEqual(repo["git_user"], {"name": "Ned", "email": "ned@example.com"})
        self.assertEqual(repo["git_user_source"], "local")
        self.assertEqual(repo["group"], "ability")

    def test_normalize_repositories_preserves_existing_git_user(self):
        repos = dr_analyze.normalize_repositories([
            {"name": "modern", "path": "/tmp/modern", "git_user": {"name": "A", "email": "a@example.com"}}
        ])

        self.assertEqual(repos[0]["git_user"]["email"], "a@example.com")


class AnalyzeAllRefsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        self._git("init", "-b", "main")
        self._git("config", "user.name", "Ned")
        self._git("config", "user.email", "ned@example.com")

        (self.repo_path / "README.md").write_text("base\n", encoding="utf-8")
        self._git("add", "README.md")
        self._commit("chore: base", "2026-07-01T10:00:00-0700")

        self._git("switch", "-c", "feature/tracking")
        (self.repo_path / "tracking.kt").write_text("val tracked = true\n", encoding="utf-8")
        self._git("add", "tracking.kt")
        self._commit("feat(crm): add tracking", "2026-07-14T10:00:00-0700")
        self._git("switch", "main")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _git(self, *args, env=None):
        subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def _commit(self, message, commit_date):
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = commit_date
        env["GIT_COMMITTER_DATE"] = commit_date
        self._git("commit", "-m", message, env=env)

    def test_activity_verification_includes_non_current_branches(self):
        self.assertTrue(
            dr_analyze.verify_repo_activity(
                self.repo_path,
                "ned@example.com",
                "2026-07-13",
                "2026-07-20",
            )
        )

    def test_commit_collection_includes_non_current_branches(self):
        commits = dr_analyze.get_commits(
            self.repo_path,
            "ned@example.com",
            "2026-07-13",
            "2026-07-20",
        )

        self.assertEqual([commit["message"] for commit in commits], ["feat(crm): add tracking"])

    def test_diff_stats_include_non_current_branches(self):
        stats = dr_analyze.get_diff_stats(
            self.repo_path,
            "ned@example.com",
            "2026-07-13",
            "2026-07-20",
        )

        self.assertEqual(stats["files_changed"], 1)
        self.assertEqual(stats["insertions"], 1)
        self.assertEqual(stats["deletions"], 0)
        self.assertEqual(stats["by_type"][".kt"]["files"], 1)

    def test_diff_content_includes_non_current_branches(self):
        content = dr_analyze.get_diff_content(
            self.repo_path,
            "ned@example.com",
            "2026-07-13",
            "2026-07-20",
            [],
        )

        self.assertIn("feat(crm): add tracking", content)
        self.assertIn("tracking.kt", content)


if __name__ == "__main__":
    unittest.main()

class AnalyzeNewRepoCompatibilityTests(unittest.TestCase):
    def test_workspace_root_supports_legacy_workspace_key(self):
        self.assertEqual(
            dr_analyze.config_workspace_root({"workspace": "/tmp/old", "workspace_root": ""}),
            "/tmp/old",
        )

    def test_detect_new_repos_returns_repo_objects_for_legacy_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(dr_analyze, "scan_workspace_repos", return_value=[
                {"name": "known", "path": f"{temp_dir}/known", "group": ""},
                {"name": "new-api", "path": f"{temp_dir}/new-api", "group": "backend"},
            ]):
                repos = dr_analyze.detect_new_repos_in_workspace({
                    "workspace": temp_dir,
                    "repositories": [{"name": "known", "path": f"{temp_dir}/known"}],
                })

        self.assertEqual(repos, [{"name": "new-api", "path": f"{temp_dir}/new-api", "group": "backend"}])


class AnalyzeRepositorySelectionTests(unittest.TestCase):
    def test_analysis_repositories_include_new_repos(self):
        with patch.object(dr_analyze, "detect_new_repos_in_workspace", return_value=[
            {"name": "new-module", "path": "/workspace/new-module", "group": "im"}
        ]), patch.object(dr_analyze, "git_config_user", return_value={"name": "Ned", "email": "ned@example.com", "source": "local"}):
            repos, new_repos = dr_analyze.analysis_repositories(
                {"repositories": [{"name": "known", "path": "/workspace/known", "git_user": {"name": "Ned", "email": "ned@example.com"}}]},
                [{"name": "known", "path": "/workspace/known", "git_user": {"name": "Ned", "email": "ned@example.com"}}],
            )

        self.assertEqual([repo["name"] for repo in repos], ["known", "new-module"])
        self.assertEqual(new_repos[0]["name"], "new-module")
