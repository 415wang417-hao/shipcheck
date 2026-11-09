"""修复器（shipcheck.fixer）的单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shipcheck import fixer
from shipcheck.facts import Facts

from .helpers import make_repo


class TestFixerPlan(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_plan_lists_all_missing_files_on_bare_repo(self):
        root = make_repo(self.tmp, {"main.py": "print('hi')\n"})
        facts = Facts.build(root)
        plan_items = fixer.plan(facts)
        paths = {item.path for item in plan_items}
        self.assertIn("LICENSE", paths)
        self.assertIn(".gitignore", paths)
        self.assertIn("AI_LOG.md", paths)
        self.assertIn("ATTRIBUTION.md", paths)
        self.assertIn("CONTRIBUTING.md", paths)
        self.assertIn("CHANGELOG.md", paths)
        self.assertIn(".github/ISSUE_TEMPLATE/bug_report.md", paths)
        self.assertIn(".github/workflows/ci.yml", paths)
        self.assertIn("README.md", paths)

    def test_plan_skips_existing_files(self):
        root = make_repo(self.tmp, {"LICENSE": "MIT License\n", ".gitignore": "a\nb\nc\n"})
        facts = Facts.build(root)
        paths = {item.path for item in fixer.plan(facts)}
        self.assertNotIn("LICENSE", paths)
        self.assertNotIn(".gitignore", paths)

    def test_apply_creates_and_never_overwrites(self):
        root = make_repo(self.tmp, {"LICENSE": "原有内容，不能被覆盖\n"})
        facts = Facts.build(root)
        plan_items = fixer.plan(facts)
        # plan() 已排除已存在文件：已存在的 LICENSE 不会排进计划
        self.assertNotIn("LICENSE", {item.path for item in plan_items})
        created, _skipped = fixer.apply(plan_items, facts.root)
        self.assertNotIn("LICENSE", created)
        self.assertEqual((root / "LICENSE").read_text(encoding="utf-8"), "原有内容，不能被覆盖\n")
        # 即便调用方硬塞一个已存在的目标，apply() 也只会记入 skipped，绝不覆盖
        _created2, skipped2 = fixer.apply(
            [fixer.FixItem("RQ07", "LICENSE", "新的内容\n")], facts.root
        )
        self.assertEqual(skipped2, ["LICENSE"])
        self.assertEqual((root / "LICENSE").read_text(encoding="utf-8"), "原有内容，不能被覆盖\n")
        for path in created:
            self.assertTrue((root / path).exists())

    def test_generated_templates_are_filled_with_context(self):
        root = make_repo(self.tmp, {})
        facts = Facts.build(root)
        plan_items = fixer.plan(facts)
        by_path = {item.path: item.content for item in plan_items}
        self.assertIn(f"Copyright (c)", by_path["LICENSE"])
        # 生成的 README 使用项目目录名
        self.assertIn(f"# {facts.root.name}", by_path["README.md"])


class TestFixerRoundTrip(unittest.TestCase):
    """--fix --apply 之后重新体检：结构分提升，但 AI 分不应被伪造。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_scaffold_ai_log_is_flagged_as_unfilled(self):
        from shipcheck import rules

        root = make_repo(self.tmp, {"main.py": "x = 1\n"})
        facts = Facts.build(root)
        plan_items = fixer.plan(facts)
        fixer.apply(plan_items, facts.root)
        after = Facts.build(facts.root)
        findings = {f.rule.id: f for f in rules.run_rules(after)}
        # 结构项通过
        self.assertTrue(findings["RQ07"].passed)  # LICENSE
        self.assertTrue(findings["CM01"].passed)  # CONTRIBUTING
        # 但未填充的 AI_LOG / ATTRIBUTION 必须被识别为骨架
        self.assertFalse(findings["AI01"].passed)
        self.assertFalse(findings["AC06"].passed)


if __name__ == "__main__":
    unittest.main()
