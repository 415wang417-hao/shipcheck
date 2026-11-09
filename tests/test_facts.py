"""Facts 采集层（shipcheck.facts）的单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shipcheck.facts import Facts

from .helpers import make_repo


class TestFactsBasics(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_case_insensitive_lookup(self):
        root = make_repo(self.tmp, {"README.MD": "# hi\n", "src/lib.py": "x = 1\n"})
        facts = Facts.build(root)
        self.assertTrue(facts.has("readme.md"))
        self.assertIsNotNone(facts.read("README.MD"))

    def test_skip_dirs_excluded(self):
        root = make_repo(
            self.tmp,
            {
                ".git/config": "[core]\n",
                "node_modules/pkg.js": "x\n",
                "src/app.py": "y = 2\n",
            },
        )
        facts = Facts.build(root)
        self.assertFalse(any(f.startswith(".git/") for f in facts.files))
        self.assertFalse(any(f.startswith("node_modules/") for f in facts.files))
        self.assertIn("src/app.py", facts.files)

    def test_readme_and_license_accessors(self):
        root = make_repo(self.tmp, {"readme.md": "# hello\n", "LICENSE": "MIT License\n"})
        facts = Facts.build(root)
        rel, text = facts.readme()
        self.assertIsNotNone(rel)
        self.assertIn("hello", text)
        rel, text = facts.license()
        self.assertIn("MIT", text)

    def test_glob_matches_paths_and_basenames(self):
        root = make_repo(
            self.tmp,
            {
                ".github/ISSUE_TEMPLATE/bug_report.md": "x\n",
                ".github/ISSUE_TEMPLATE/feature_request.md": "y\n",
            },
        )
        facts = Facts.build(root)
        hits = facts.glob(".github/issue_template/*")
        self.assertEqual(len(hits), 2)

    def test_empty_files_reported(self):
        root = make_repo(self.tmp, {"README.md": "", "ok.py": "x = 1\n"})
        facts = Facts.build(root)
        self.assertEqual(facts.empty_files(), ["README.md"])

    def test_search_finds_matches_with_lineno(self):
        root = make_repo(self.tmp, {"app.py": "VERSION = \"1.0.0\"\nx = 2\n"})
        facts = Facts.build(root)
        hits = facts.search(r"VERSION\s*=")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][1], 1)

    def test_build_rejects_missing_path(self):
        with self.assertRaises(FileNotFoundError):
            Facts.build(self.tmp / "does-not-exist")


if __name__ == "__main__":
    unittest.main()
