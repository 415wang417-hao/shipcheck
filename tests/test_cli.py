"""CLI 端到端测试（子进程运行 python -m shipcheck）。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

from .helpers import good_repo_files, make_repo


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "shipcheck", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


class TestCliEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_help_exits_zero(self):
        proc = run_cli("--help", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("shipcheck", proc.stdout)

    def test_version_flag(self):
        proc = run_cli("--version", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("shipcheck", proc.stdout)

    def test_list_rules(self):
        proc = run_cli("--list-rules", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("RQ01", proc.stdout)
        self.assertIn("总分 100", proc.stdout)

    def test_good_repo_exit_zero_with_text_report(self):
        root = make_repo(self.tmp, good_repo_files())
        proc = run_cli(str(root), cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("100/100", proc.stdout)

    def test_bad_repo_exit_one_and_required_failures_listed(self):
        root = make_repo(self.tmp, {"main.py": "x = 1\n"})
        proc = run_cli(str(root), cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("RQ01", proc.stdout)  # README 缺失是必需项

    def test_json_output_is_parseable(self):
        root = make_repo(self.tmp, good_repo_files())
        proc = run_cli(str(root), "--format", "json", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], "shipcheck.report/1")
        self.assertEqual(payload["score"], 100)
        self.assertEqual(len(payload["findings"]), 31)
        self.assertEqual(payload["exit_code"], 0)

    def test_markdown_output_written_to_file(self):
        root = make_repo(self.tmp, good_repo_files())
        out = self.tmp / "REPORT.md"
        proc = run_cli(str(root), "-f", "markdown", "-o", str(out), cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("体检报告", content)
        self.assertIn("总分", content)

    def test_missing_path_exit_three(self):
        proc = run_cli(str(self.tmp / "nope"), cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 3)

    def test_fix_dry_run_lists_plan_json(self):
        root = make_repo(self.tmp, {"main.py": "x = 1\n"})
        proc = run_cli(str(root), "--fix", "--format", "json", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], "shipcheck.fixplan/1")
        self.assertIn("LICENSE", [item["path"] for item in payload["items"]])

    def test_fix_apply_creates_files_then_reports(self):
        root = make_repo(self.tmp, {"main.py": "x = 1\n"})
        proc = run_cli(str(root), "--fix", "--apply", cwd=REPO_ROOT)
        self.assertIn("已创建", proc.stdout)
        self.assertTrue((root / "LICENSE").exists())
        self.assertTrue((root / ".github" / "workflows" / "ci.yml").exists())
        # 骨架未填充 → 必需项仍失败 → 退出码 1
        self.assertEqual(proc.returncode, 1)

    def test_apply_requires_fix(self):
        proc = run_cli("--apply", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 3)


class TestSelfAudit(unittest.TestCase):
    """Dogfood：shipcheck 给自己体检，应该是满分。"""

    def test_self_audit_scores_100(self):
        proc = run_cli(str(REPO_ROOT), cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("100/100", proc.stdout)
        self.assertIn("A", proc.stdout)

    def test_self_audit_json_required_all_pass(self):
        proc = run_cli(str(REPO_ROOT), "--format", "json", cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["score"], 100)
        self.assertEqual(payload["required_passed"], payload["required_total"])
        failed = [f["id"] for f in payload["findings"] if not f["passed"]]
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
