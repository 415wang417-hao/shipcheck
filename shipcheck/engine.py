"""Audit orchestration: facts -> findings -> score -> red flags -> exit code."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from . import __version__
from .facts import Facts
from .rules import Finding, run_rules
from .scoring import Score, evaluate


@dataclass
class Audit:
    root: Path
    facts: Facts
    findings: List[Finding] = field(default_factory=list)
    score: Score = field(default_factory=lambda: Score(0, 100, "F"))
    red_flags: List[str] = field(default_factory=list)
    generated_at: str = ""
    tool_version: str = __version__
    duration: float = 0.0

    @property
    def passed(self) -> List[Finding]:
        return [f for f in self.findings if f.passed]

    @property
    def failed(self) -> List[Finding]:
        return [f for f in self.findings if not f.passed]

    @property
    def failed_required(self) -> List[Finding]:
        return [f for f in self.failed if f.rule.is_required]

    @property
    def failed_recommended(self) -> List[Finding]:
        return [f for f in self.failed if not f.rule.is_required]


def _detect_red_flags(facts: Facts, score: Score) -> List[str]:
    flags: List[str] = []
    if facts.readme()[0] is None:
        flags.append("missing_readme：没有 README，别人无法理解这个仓库")
    if facts.license()[0] is None:
        flags.append("missing_license：没有 LICENSE，法律上别人不能安全地使用你的代码")
    empty = facts.empty_files()
    if empty:
        shown = "、".join(empty[:5]) + ("…" if len(empty) > 5 else "")
        flags.append(f"empty_files：{len(empty)} 个 0 字节文件（{shown}）")
    if score.total < 60:
        flags.append(f"low_score：总分 {score.total}/100，低于 60 分发布线")
    return flags


def audit(root: "str | Path") -> Audit:
    """Run the full rule set against *root* and return the packed audit."""
    started = time.perf_counter()
    facts = Facts.build(root)
    findings = run_rules(facts)
    score = evaluate(findings)
    result = Audit(
        root=facts.root,
        facts=facts,
        findings=findings,
        score=score,
        red_flags=_detect_red_flags(facts, score),
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        tool_version=__version__,
        duration=time.perf_counter() - started,
    )
    return result


def compute_exit_code(result: Audit, min_score: int = 80) -> int:
    """Exit codes: 0 pass · 1 required failures · 2 below min score · 3 usage."""
    if result.failed_required:
        return 1
    if result.score.total < min_score:
        return 2
    return 0
