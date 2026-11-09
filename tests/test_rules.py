"""规则引擎（shipcheck.rules）针对合成仓库的单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shipcheck import rules
from shipcheck.facts import Facts

from .helpers import good_repo_files, make_repo


def audit_of(root: Path):
    facts = Facts.build(root)
    return {f.rule.id: f for f in rules.run_rules(facts)}


class RuleTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)


class TestGoodRepo(RuleTestCase):
    def test_all_rules_pass_on_good_repo(self):
        root = make_repo(self.tmp, good_repo_files())
        results = audit_of(root)
        failed = [fid for fid, f in results.items() if not f.passed]
        self.assertEqual(failed, [], msg=f"合成达标仓库不应有失败项: {failed}")

    def test_registry_dimensions_and_weights(self):
        from shipcheck.scoring import DIMENSIONS, TOTAL_MAX

        expected = {dim_id: points for dim_id, _label, points in DIMENSIONS}
        actual = {}
        for rule in rules.RULES:
            actual[rule.dimension] = actual.get(rule.dimension, 0) + rule.weight
        self.assertEqual(actual, expected)
        self.assertEqual(sum(actual.values()), TOTAL_MAX)
        self.assertEqual(len(rules.RULES), 31)


class TestReadmeRules(RuleTestCase):
    def test_rq01_fails_without_readme(self):
        root = make_repo(self.tmp, {"LICENSE": "MIT License\n"})
        self.assertFalse(audit_of(root)["RQ01"].passed)

    def test_rq01_fails_on_thin_readme(self):
        root = make_repo(self.tmp, {"README.md": "# too short\n"})
        self.assertFalse(audit_of(root)["RQ01"].passed)

    def test_rq02_requires_tagline(self):
        root = make_repo(self.tmp, {"README.md": "# Project\n\n[![badge](x)](y)\n\n正文很短也很短。\n"})
        self.assertFalse(audit_of(root)["RQ02"].passed)

    def test_rq03_requires_install_heading(self):
        files = good_repo_files()
        files["README.md"] = "# P\n\n描述一下这个项目。\n\n## 使用\n\n```bash\nrun\n```\n"
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["RQ03"].passed)

    def test_rq07_detects_license_type(self):
        root = make_repo(self.tmp, good_repo_files())
        finding = audit_of(root)["RQ07"]
        self.assertTrue(finding.passed)
        self.assertIn("MIT", finding.result.detail)

    def test_rq07_fails_on_unrecognized_license(self):
        files = good_repo_files()
        files["LICENSE"] = "随便写的协议文本\n"
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["RQ07"].passed)

    def test_rq08_requires_effective_rules(self):
        files = good_repo_files()
        files[".gitignore"] = "# only comments\n\n# nothing else\n"
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["RQ08"].passed)


class TestCommunityRules(RuleTestCase):
    def test_cm02_requires_issue_templates(self):
        files = good_repo_files()
        del files[".github/ISSUE_TEMPLATE/bug_report.md"]
        del files[".github/ISSUE_TEMPLATE/feature_request.md"]
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["CM02"].passed)

    def test_cm04_changelog_needs_version(self):
        files = good_repo_files()
        files["CHANGELOG.md"] = "# Changelog\n\n只是记录，没有版本号。\n"
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["CM04"].passed)


class TestArtifactRules(RuleTestCase):
    def test_ac01_fails_on_empty_repo(self):
        root = make_repo(self.tmp, {"README.md": "x" * 300})
        self.assertFalse(audit_of(root)["AC01"].passed)

    def test_ac02_requires_assertions(self):
        files = good_repo_files()
        # 清掉所有带断言的测试文件，只留一个无断言的占位测试
        for path in [p for p in files if p.rsplit("/", 1)[-1].startswith("test_") and p.endswith(".py")]:
            del files[path]
        files["tests/test_main.py"] = "# no tests here\nprint('placeholder')\n"
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["AC02"].passed)


    def test_ac04_entry_via_dunder_main(self):
        root = make_repo(self.tmp, good_repo_files())
        self.assertTrue(audit_of(root)["AC04"].passed)


class TestAiUsageRules(RuleTestCase):
    def test_ai01_fails_on_scaffold_log(self):
        files = good_repo_files()
        files["AI_LOG.md"] = (
            "# AI 使用日志\n\nTODO 填充。\n\nTODO 更多内容。TODO 另一处。TODO 又一处。TODO 结尾。\n"
        )
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["AI01"].passed)

    def test_ai03_requires_prompt_evidence(self):
        files = good_repo_files()
        # 一份完全没有 prompt 原文的日志：无代码块、无「Prompt：」标记
        files["AI_LOG.md"] = (
            "# AI 使用日志\n\n"
            "初始化、代码、文档、测试、审查各阶段都有记录。\n\n"
            "v0.5 → v1.0 迭代了两次，修正了若干问题。\n\n"
            "## 迭代记录\n\n- v0.5 → v1.0：重写了 `main.py` 的入口。\n\n"
            "## 失败与踩坑\n\n- 第一版 README 忘了写安装章节，报错后重写。\n"
        )
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["AI03"].passed)


    def test_ai05_requires_real_file_references(self):
        files = good_repo_files()
        files["AI_LOG.md"] = (
            "# AI 使用日志\n\n"
            "初始化、代码、文档、测试、审查各阶段都有记录。\n\n"
            "v0.5 → v1.0 迭代了两次，修正了若干问题。\n\n"
            "## 失败与踩坑\n\n- 失败一次。\n\n"
            "## AAR\n\n预期、实际、差异、改进都写了。\n\n"
            "## 改进\n\n- [ ] 改进一\n- [ ] 改进二\n\n"
            "没有引用任何仓库文件路径。\n"
        )
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["AI05"].passed)

    def test_ac06_fails_on_scaffold_attribution(self):
        files = good_repo_files()
        files["ATTRIBUTION.md"] = (
            "# 拿来说明\n\nTODO 来源一。TODO 来源二。TODO 来源三。\n" + "填充说明文字。" * 20 + "\n"
        )
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["AC06"].passed)


class TestReflectionRules(RuleTestCase):
    def test_rf02_requires_failure_section(self):
        files = good_repo_files()
        files["AI_LOG.md"] = files["AI_LOG.md"].replace("## 失败与踩坑", "## 历程记录")
        root = make_repo(self.tmp, files)
        # 日志内仍有 ≥3 处失败相关词汇，应通过
        self.assertTrue(audit_of(root)["RF02"].passed)

    def test_rf03_requires_actionable_items(self):
        files = good_repo_files()
        log = files["AI_LOG.md"]
        # 把真正的「改进与下一步」章节降级成一句话；AAR 里的要点清单不算改进方案
        marker = "## 改进与下一步"
        self.assertIn(marker, log)
        files["AI_LOG.md"] = log.split(marker)[0] + marker + "\n\n一句话带过。\n"
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["RF03"].passed)



class TestRedFlagSensitiveRules(RuleTestCase):
    def test_ac07_flags_empty_core_file(self):
        files = good_repo_files()
        files["LICENSE"] = ""
        root = make_repo(self.tmp, files)
        self.assertFalse(audit_of(root)["AC07"].passed)


if __name__ == "__main__":
    unittest.main()
