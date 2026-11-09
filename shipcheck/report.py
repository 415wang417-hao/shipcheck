"""Render an :class:`~shipcheck.engine.Audit` as terminal text, Markdown or JSON."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, List, Optional

from .engine import Audit
from .scoring import DIMENSIONS

_MARK = {"ok": "✔", "fail": "✘", "warn": "▲"}


class Palette:
    """ANSI palette that degrades to plain text on demand."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def green(self, text: str) -> str:
        return self._wrap("32", text)

    def red(self, text: str) -> str:
        return self._wrap("31", text)

    def yellow(self, text: str) -> str:
        return self._wrap("33", text)

    def cyan(self, text: str) -> str:
        return self._wrap("36", text)

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def dim(self, text: str) -> str:
        return self._wrap("2", text)


def _bar(ratio: float, width: int = 10) -> str:
    filled = max(0, min(width, round(ratio * width)))
    return "#" * filled + "." * (width - filled)


def _grade_color(palette: Palette, grade: str, text: str) -> str:
    if grade in ("A", "B"):
        return palette.green(text)
    if grade == "C":
        return palette.yellow(text)
    return palette.red(text)


def render_text(result: Audit, palette: Optional[Palette] = None, verbose: bool = False) -> str:
    """Human-friendly terminal report (ANSI colours optional)."""
    palette = palette or Palette(enabled=False)
    score = result.score
    lines: List[str] = []
    rule_line = "─" * 56
    lines.append(rule_line)
    lines.append(f" shipcheck v{result.tool_version}  ·  仓库体检报告")
    lines.append(f" 目标：{result.root}")
    lines.append(f" 时间：{result.generated_at}  ·  耗时 {result.duration:.2f}s")
    lines.append(rule_line)
    grade = _grade_color(palette, score.grade, score.grade)
    lines.append(
        f" 总分   {palette.bold(f'{score.total}/{score.max_total}')}  {grade}"
        f"   ·   必需项 {score.required_passed}/{score.required_total} 通过"
    )
    lines.append("")
    for dim in score.dimensions:
        bar = _bar(dim.ratio)
        colored = palette.green(bar) if dim.ratio >= 0.8 else (
            palette.yellow(bar) if dim.ratio >= 0.5 else palette.red(bar)
        )
        lines.append(f" {dim.label:<8}{dim.score:>4}/{dim.max_points:<4}{colored} {dim.percent:>3}%")
    lines.append("")

    if result.red_flags:
        lines.append(palette.red(" 红旗（red flags）"))
        for flag in result.red_flags:
            lines.append(f"   {palette.red('!')} {flag}")
        lines.append("")

    if result.failed_required:
        lines.append(palette.red(f" 必须修复（{len(result.failed_required)} 项，阻塞发布）"))
        for finding in result.failed_required:
            lines.append(
                f"   {_MARK['fail']} {palette.bold(finding.rule.id)} {finding.rule.title}"
                f" — {finding.result.detail}"
            )
            lines.append(palette.dim(f"      ↳ {finding.rule.hint}"))
        lines.append("")

    if result.failed_recommended:
        lines.append(palette.yellow(f" 建议补齐（{len(result.failed_recommended)} 项，影响得分）"))
        for finding in result.failed_recommended:
            lines.append(
                f"   {palette.yellow('-')} {finding.rule.id} {finding.rule.title}"
                f" — {finding.result.detail}"
            )
            lines.append(palette.dim(f"     ↳ {finding.rule.hint}"))
        lines.append("")

    passed = result.passed
    if verbose and passed:
        lines.append(palette.green(f" 已通过（{len(passed)} 项）"))
        for finding in passed:
            lines.append(
                f"   {_MARK['ok']} {finding.rule.id} {finding.rule.title} — {finding.result.detail}"
            )
        lines.append("")
    elif passed:
        lines.append(palette.dim(f" ✔ {len(passed)} 项检查通过（加 --verbose 查看明细）"))
        lines.append("")

    if result.failed:
        lines.append(palette.cyan(" 下一步"))
        lines.append(palette.cyan("   python -m shipcheck . --fix          # 查看缺失文件清单（干跑）"))
        lines.append(palette.cyan("   python -m shipcheck . --fix --apply  # 生成骨架文件后重新体检"))
    lines.append(rule_line)
    return "\n".join(lines)


def render_markdown(result: Audit) -> str:
    """GitHub-flavoured Markdown report."""
    score = result.score
    lines: List[str] = []
    lines.append("# shipcheck 体检报告")
    lines.append("")
    lines.append(
        f"> 仓库：`{result.root}` · 工具 v{result.tool_version} · "
        f"生成时间 {result.generated_at} · 耗时 {result.duration:.2f}s"
    )
    lines.append("")
    lines.append(f"## 总分：{score.total} / {score.max_total}（{score.grade}）")
    lines.append("")
    lines.append(f"必需项通过：**{score.required_passed}/{score.required_total}**")
    lines.append("")
    lines.append("| 维度 | 得分 | 满分 | 完成度 |")
    lines.append("| --- | ---: | ---: | --- |")
    for dim in score.dimensions:
        lines.append(
            f"| {dim.label} | {dim.score} | {dim.max_points} | `{_bar(dim.ratio)}` {dim.percent}% |"
        )
    lines.append("")

    if result.red_flags:
        lines.append("## 🚩 红旗")
        lines.append("")
        for flag in result.red_flags:
            lines.append(f"- {flag}")
        lines.append("")

    if result.failed_required:
        lines.append(f"## ❌ 必须修复（{len(result.failed_required)} 项）")
        lines.append("")
        lines.append("| 规则 | 检查结果 | 修复建议 |")
        lines.append("| --- | --- | --- |")
        for finding in result.failed_required:
            lines.append(
                f"| **{finding.rule.id}** {finding.rule.title} "
                f"| {finding.result.detail} | {finding.rule.hint} |"
            )
        lines.append("")

    if result.failed_recommended:
        lines.append(f"## ⚠️ 建议补齐（{len(result.failed_recommended)} 项）")
        lines.append("")
        lines.append("| 规则 | 检查结果 | 修复建议 |")
        lines.append("| --- | --- | --- |")
        for finding in result.failed_recommended:
            lines.append(
                f"| {finding.rule.id} {finding.rule.title} "
                f"| {finding.result.detail} | {finding.rule.hint} |"
            )
        lines.append("")

    lines.append(f"## ✅ 已通过（{len(result.passed)} 项）")
    lines.append("")
    for finding in result.passed:
        lines.append(f"- `{finding.rule.id}` {finding.rule.title} — {finding.result.detail}")
    lines.append("")
    return "\n".join(lines)


def to_dict(result: Audit, min_score: int = 80, exit_code: int = 0) -> Dict:
    """Machine-readable view (also the documented JSON schema)."""
    from .engine import compute_exit_code

    return {
        "schema": "shipcheck.report/1",
        "tool_version": result.tool_version,
        "root": str(result.root),
        "generated_at": result.generated_at,
        "duration_seconds": round(result.duration, 3),
        "score": result.score.total,
        "max_score": result.score.max_total,
        "grade": result.score.grade,
        "min_score": min_score,
        "exit_code": exit_code if exit_code else compute_exit_code(result, min_score),
        "required_passed": result.score.required_passed,
        "required_total": result.score.required_total,
        "red_flags": result.red_flags,
        "dimensions": [
            {
                "id": dim.id,
                "label": dim.label,
                "score": dim.score,
                "max_points": dim.max_points,
                "percent": dim.percent,
            }
            for dim in result.score.dimensions
        ],
        "findings": [
            {
                "id": finding.rule.id,
                "title": finding.rule.title,
                "dimension": finding.rule.dimension,
                "weight": finding.rule.weight,
                "severity": finding.rule.severity,
                "passed": finding.passed,
                "detail": finding.result.detail,
                "hint": finding.rule.hint,
            }
            for finding in result.findings
        ],
    }


def render_json(result: Audit, min_score: int = 80, exit_code: int = 0) -> str:
    return json.dumps(to_dict(result, min_score, exit_code), ensure_ascii=False, indent=2)


def rules_table(rules, palette: Optional[Palette] = None) -> str:
    """``--list-rules`` output generated from the registry itself."""
    palette = palette or Palette(enabled=False)
    lines = [f"共 {len(rules)} 条规则：", ""]
    lines.append(f"{'ID':<6}{'维度':<20}{'权重':>4}  {'级别':<12}规则")
    lines.append("-" * 76)
    for rule in rules:
        dimension = next(label for rid, label, _ in DIMENSIONS if rid == rule.dimension)
        severity = "必需" if rule.is_required else "建议"
        weight = f"{rule.weight:>4}"
        lines.append(f"{rule.id:<6}{dimension:<20}{weight}  {severity:<12}{rule.title}")
    lines.append("-" * 76)
    total_by_dim: Dict[str, int] = {}
    for rule in rules:
        total_by_dim[rule.dimension] = total_by_dim.get(rule.dimension, 0) + rule.weight
    lines.append(
        "  ".join(
            f"{label} {total_by_dim.get(rid, 0)}"
            for rid, label, _max in DIMENSIONS
        )
        + f"  ·  总分 {sum(total_by_dim.values())}"
    )
    return "\n".join(lines)
