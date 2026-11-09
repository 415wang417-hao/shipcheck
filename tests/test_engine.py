"""评分聚合（shipcheck.scoring）与体检编排（shipcheck.engine）的单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shipcheck import engine, rules, scoring
from shipcheck.facts import Facts
from shipcheck.rules import CheckResult, Finding, Rule

from .helpers import good_repo_files, make_repo


def _finding(rule_id: str, dimension: str, weight: int, severity: str, passed: bool) -> Finding:
    rule = Rule(rule_id, rule_id, dimension, weight, severity, "", lambda f: CheckResult.ok(""))
    return Finding(rule, CheckResult.ok("") if passed else CheckResult.fail(""))


class TestScoring(unittest.TestCase):
    def test_full_marks(self):
        findings = [
            _finding("RQ01", "repoQuality", 5, "required", True),
            _finding("RQ02", "repoQuality", 3, "required", True),
            _finding("CM01", "community", 4, "recommended", True),
            _finding("AI01", "aiUsage", 6, "required", True),
        ]
        score = scoring.evaluate(findings)
        self.assertEqual(score.total, 18)
        self.assertEqual(score.required_passed, 3)
        self.assertEqual(score.required_total, 3)

    def test_zero_when_all_fail(self):
        findings = [
            _finding("RQ01", "repoQuality", 5, "required", False),
            _finding("CM01", "community", 4, "recommended", False),
        ]
        score = scoring.evaluate(findings)
        self.assertEqual(score.total, 0)
        self.assertEqual(score.grade, "F")
        self.assertIn("RQ01", score.failed_required_ids)

    def test_grade_bands(self):
        self.assertEqual(scoring.grade_for(95), "A")
        self.assertEqual(scoring.grade_for(90), "A")
        self.assertEqual(scoring.grade_for(89), "B")
        self.assertEqual(scoring.grade_for(80), "B")
        self.assertEqual(scoring.grade_for(79), "C")
        self.assertEqual(scoring.grade_for(59), "F")

    def test_unknown_dimension_raises(self):
        finding = _finding("XX01", "nonexistent", 1, "recommended", True)
        with self.assertRaises(ValueError):
            scoring.evaluate([finding])


class TestEngine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_audit_good_repo_scores_100(self):
        root = make_repo(self.tmp, good_repo_files())
        result = engine.audit(root)
        self.assertEqual(result.score.total, 100)
        self.assertEqual(result.score.grade, "A")
        self.assertEqual(result.red_flags, [])
        self.assertEqual(engine.compute_exit_code(result, 80), 0)

    def test_audit_broken_repo_flags_and_exit_codes(self):
        root = make_repo(self.tmp, {"main.py": "x = 1\n"})
        result = engine.audit(root)
        self.assertLess(result.score.total, 60)
        self.assertTrue(any("missing_readme" in flag for flag in result.red_flags))
        # 必需项失败 → 退出码 1
        self.assertEqual(engine.compute_exit_code(result, 80), 1)

    def test_exit_code_2_when_only_score_below_threshold(self):
        # 构造：必需项全过但总分低于门槛的场景，直接用 Score 对象验证逻辑
        score = scoring.Score(
            total=75,
            max_total=100,
            grade="C",
            dimensions=[],
            required_passed=10,
            required_total=10,
        )

        class _Stub(AuditStub):
            # Audit.failed_required 是只读 property，子类用同名属性覆盖才能构造场景
            failed_required: list = ()

        stub = _Stub()
        stub.score = score
        self.assertEqual(list(stub.failed_required), [])
        self.assertEqual(engine.compute_exit_code(stub, 80), 2)


class AuditStub(engine.Audit):
    """最小化的 Audit 替身（只为 exit code 逻辑）。"""

    def __init__(self):  # noqa: D107
        pass


if __name__ == "__main__":
    unittest.main()
