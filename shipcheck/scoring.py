"""Aggregation of rule findings into dimension and total scores.

The five dimensions mirror the C5 review rubric (README/structure quality,
community, artifact completeness, AI-usage quality, reflection quality) so a
shipcheck score can be read directly against that rubric.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from .rules import Finding

#: Ordered dimension registry: id -> (label, maximum points).
DIMENSIONS: Tuple[Tuple[str, str, int], ...] = (
    ("repoQuality", "仓库质量", 25),
    ("community", "社区要素", 20),
    ("artifactCompleteness", "产物完整性", 15),
    ("aiUsage", "AI 使用质量", 20),
    ("reflectionQuality", "复盘质量", 20),
)
DIMENSION_IDS = tuple(d[0] for d in DIMENSIONS)
TOTAL_MAX = sum(d[2] for d in DIMENSIONS)

#: Score bands used for the letter grade.
GRADE_BANDS: Tuple[Tuple[int, str], ...] = (
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
)


@dataclass
class DimensionScore:
    id: str
    label: str
    score: int
    max_points: int

    @property
    def ratio(self) -> float:
        return self.score / self.max_points if self.max_points else 1.0

    @property
    def percent(self) -> int:
        return round(self.ratio * 100)


@dataclass
class Score:
    total: int
    max_total: int
    grade: str
    dimensions: List[DimensionScore] = field(default_factory=list)
    required_passed: int = 0
    required_total: int = 0
    failed_required_ids: Tuple[str, ...] = ()

    @property
    def percent(self) -> int:
        return round(self.total / self.max_total * 100) if self.max_total else 0

    def dimension(self, dim_id: str) -> DimensionScore:
        for item in self.dimensions:
            if item.id == dim_id:
                return item
        raise KeyError(dim_id)


def grade_for(score: int, max_total: int = TOTAL_MAX) -> str:
    percent = score / max_total if max_total else 0.0
    for threshold, letter in GRADE_BANDS:
        if percent * 100 >= threshold:
            return letter
    return "F"


def evaluate(findings: Sequence[Finding]) -> Score:
    """Sum rule weights into dimension scores, grades and required stats."""
    per_dimension: Dict[str, int] = {dim_id: 0 for dim_id in DIMENSION_IDS}
    per_dimension_max: Dict[str, int] = {dim_id: 0 for dim_id in DIMENSION_IDS}

    required_total = 0
    required_passed = 0
    failed_required: List[str] = []

    for finding in findings:
        rule = finding.rule
        if rule.dimension not in per_dimension:
            # Unknown dimension would indicate a programming error upstream.
            raise ValueError(f"规则 {rule.id} 使用了未注册的维度 {rule.dimension!r}")
        per_dimension_max[rule.dimension] += rule.weight
        if finding.passed:
            per_dimension[rule.dimension] += rule.weight
        if rule.severity == "required":
            required_total += 1
            if finding.passed:
                required_passed += 1
            else:
                failed_required.append(rule.id)

    dimensions = [
        DimensionScore(dim_id, label, per_dimension[dim_id], per_dimension_max[dim_id])
        for dim_id, label, _max in DIMENSIONS
    ]
    total = sum(item.score for item in dimensions)
    return Score(
        total=total,
        max_total=TOTAL_MAX,
        grade=grade_for(total),
        dimensions=dimensions,
        required_passed=required_passed,
        required_total=required_total,
        failed_required_ids=tuple(failed_required),
    )
