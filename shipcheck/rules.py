"""The shipcheck rule set: 33 checks across the five rubric dimensions.

Each rule is a pure function ``Facts -> CheckResult`` plus metadata (weight,
severity, remediation hint).  Keeping rules declarative has two payoffs:

* the ``--list-rules`` output and ``docs/RULES.md`` can be generated from the
  same source of truth, and
* tests can drive single rules against tiny synthetic repositories.

Weights sum to the C5 rubric: 仓库质量 25 / 社区要素 20 / 产物完整性 15 /
AI 使用质量 20 / 复盘质量 20 = 100.

反作弊说明
----------
``--fix`` 生成的骨架充满 ``TODO`` 标记；体检会识别“仍是脚手架”的
AI_LOG / ATTRIBUTION 并判为不通过——骨架能补结构分，但不能伪造过程分。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import md
from .facts import Facts

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    detail: str

    @classmethod
    def ok(cls, detail: str) -> "CheckResult":
        return cls(True, detail)

    @classmethod
    def fail(cls, detail: str) -> "CheckResult":
        return cls(False, detail)


Check = Callable[[Facts], CheckResult]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    dimension: str
    weight: int
    severity: str  # "required" | "recommended"
    hint: str
    check: Check

    @property
    def is_required(self) -> bool:
        return self.severity == "required"


@dataclass(frozen=True)
class Finding:
    rule: Rule
    result: CheckResult

    @property
    def passed(self) -> bool:
        return self.result.passed

    @property
    def id(self) -> str:
        return self.rule.id


# --------------------------------------------------------------------------- #
# Shared vocabularies
# --------------------------------------------------------------------------- #

INSTALL_KEYWORDS = (
    "安装",
    "快速开始",
    "开始使用",
    "上手",
    "install",
    "installation",
    "quick start",
    "quickstart",
    "getting started",
    "setup",
)
EXAMPLE_KEYWORDS = (
    "示例",
    "例子",
    "用法",
    "使用",
    "输入输出",
    "example",
    "usage",
    "demo",
    "tutorial",
)
STRUCTURE_KEYWORDS = (
    "项目结构",
    "目录结构",
    "文件结构",
    "仓库结构",
    "structure",
    "layout",
    "directory",
)
STACK_KEYWORDS = (
    "技术栈",
    "技术选型",
    "环境要求",
    "依赖",
    "stack",
    "technologies",
    "requirements",
)

LICENSE_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("MIT", r"\bMIT\s+License\b"),
    ("Apache-2.0", r"Apache\s+License"),
    ("GPL", r"GNU\s+General\s+Public\s+License"),
    ("AGPL", r"GNU\s+Affero\s+General\s+Public\s+License"),
    ("LGPL", r"GNU\s+Lesser\s+General\s+Public\s+License"),
    ("BSD", r"Redistribution and use in source and binary forms"),
    ("MPL", r"Mozilla\s+Public\s+License"),
    ("Unlicense", r"free and unencumbered software released into the public domain"),
    ("ISC", r"ISC\s+License"),
    ("CC0", r"Creative\s+Commons\s+Zero"),
)

CODE_SUFFIXES = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".java",
    ".rs", ".c", ".h", ".cpp", ".hpp", ".r", ".m", ".jl", ".kt", ".swift",
    ".php", ".rb", ".sh", ".ps1", ".sql", ".ipynb",
}

DEPENDENCY_MANIFESTS = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "package.json",
    "environment.yml",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
    "pom.xml",
    "build.gradle",
    "DESCRIPTION",
)

AI_LOG_NAMES = (
    "AI_LOG.md",
    "docs/AI_LOG.md",
    "AI-USAGE.md",
    "docs/AI-USAGE.md",
    "AI_LOG.txt",
    "docs/AI_LOG.txt",
    "AI_LOG.zh.md",
)

STAGE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "初始化/骨架": ("初始化", "骨架", "scaffold", "bootstrap", "项目结构", "目录结构"),
    "代码编写": ("代码", "编写", "实现", "函数", "模块", "coding", "implementation"),
    "文档撰写": ("文档", "readme", "说明", "写作", "documentation"),
    "审查/评审": ("审查", "评审", "review", "静态检查"),
    "测试/调试": ("测试", "test", "调试", "debug", "unittest", "断言"),
    "发布/版本": ("发布", "release", "changelog", "版本", "commit", "部署", "deploy"),
}

AAR_GROUPS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("预期", ("预期", "期望", "目标", "expect", "objective")),
    ("实际", ("实际", "结果", "actual", "result")),
    ("差异", ("差异", "偏差", "落差", "不一致", "gap")),
    ("改进", ("改进", "下一步", "行动", "措施", "action", "improve")),
)

_SCAFFOLD_MARKERS = re.compile(r"TODO|待填|占位|FIXME|<你的用户名>|YOUR NAME", re.I)


def _scaffold_count(text: str) -> int:
    return len(_SCAFFOLD_MARKERS.findall(text))


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def _suffix(path: str) -> str:
    return Path(path).suffix.lower()


def _file_nonempty_lines(facts: Facts, rel: str) -> int:
    text = facts.read(rel) or ""
    return md.count_nonempty_lines(text)


def _code_files(facts: Facts) -> List[str]:
    return [f for f in facts.files if _suffix(f) in CODE_SUFFIXES]


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    base = Path(lowered).name
    if base.startswith("test_") and base.endswith((".py", ".go", ".rs")):
        return True
    if base.endswith(("_test.py", "_test.go", ".test.js", ".test.ts", ".spec.js", ".spec.ts")):
        return True
    if lowered.startswith(("tests/", "test/", "spec/")) and _suffix(lowered) in CODE_SUFFIXES:
        return True
    return False


def _test_files(facts: Facts) -> List[str]:
    return [f for f in facts.files if _is_test_path(f)]


def _assertion_count(facts: Facts, rel: str) -> int:
    text = facts.read(rel) or ""
    patterns = (
        r"^\s*def\s+test_",
        r"^\s*(?:it|test)\s*\(",
        r"^\s*describe\s*\(",
        r"#\[test\]",
        r"@Test",
        r"\bassert",
    )
    hits = 0
    for line in text.splitlines():
        for pattern in patterns:
            if re.search(pattern, line):
                hits += 1
                break
    return hits


# --------------------------------------------------------------------------- #
# 仓库质量 repoQuality (25)
# --------------------------------------------------------------------------- #


def _rq01_readme_exists(facts: Facts) -> CheckResult:
    rel, text = facts.readme()
    if rel is None:
        return CheckResult.fail("未找到 README（支持 readme.md / README.markdown 等变体）")
    length = len(text or "")
    if length < 200:
        return CheckResult.fail(f"{rel} 仅 {length} 个字符，说明过于单薄（需 ≥200）")
    return CheckResult.ok(f"{rel}（{length} 字符，{md.count_nonempty_lines(text or '')} 行）")


MIN_TAGLINE_CHARS = 12


def _plain_text(line: str) -> str:
    """剥掉 Markdown 装饰（徽章 / 图片 / 链接 / HTML / 列表符），只留人类可读文字。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)  # 图片
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # 链接（保留可见文字）
    text = re.sub(r"<[^>]+>", "", text)  # HTML 标签 / 注释
    text = re.sub(r"^\s*#+\s*", "", text)  # 标题符号
    return text.strip(" \t|>*-_~`")


def _rq02_tagline(facts: Facts) -> CheckResult:
    rel, text = facts.readme()
    if rel is None or not text:
        return CheckResult.fail("没有 README，无法检查一句话描述")
    body = md.strip_code(text)
    line = ""
    seen = 0
    for raw in body.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        seen += 1
        if seen > 40:
            break
        plain = _plain_text(stripped)
        if len(plain) < 2:
            continue  # 徽章 / 图片 / 分割线，不是项目描述
        line = plain
        break
    if not line:
        return CheckResult.fail("README 开头 40 个正文行内没有找到一句话描述（H1 下方的正文首行）")
    if len(line) < MIN_TAGLINE_CHARS:
        return CheckResult.fail(
            f"一句话描述过短（{len(line)} 字符，需 ≥{MIN_TAGLINE_CHARS}）：“{line[:40]}”"
            "——需要说清这个项目做什么，而不是残句或徽章"
        )
    has_io = ("输入" in body and "输出" in body) or (
        "input" in body.lower() and "output" in body.lower()
    )
    suffix = "" if has_io else "；建议补上『输入____，输出____』句式"
    return CheckResult.ok(f"“{line[:60]}”{suffix}")


def _rq03_install(facts: Facts) -> CheckResult:
    rel, text = facts.readme()
    if rel is None or not text:
        return CheckResult.fail("没有 README，无法检查安装说明")
    title = md.find_heading(text, INSTALL_KEYWORDS)
    if not title:
        return CheckResult.fail("README 缺少『安装 / 快速开始』章节")
    blocks = [b for b in md.fenced_blocks(text) if b.strip()]
    if not blocks:
        return CheckResult.fail(f"找到『{title}』章节，但整个 README 没有可复制的命令代码块")
    return CheckResult.ok(f"『{title}』章节 + README 内 {len(blocks)} 个命令代码块")


def _rq04_example(facts: Facts) -> CheckResult:
    rel, text = facts.readme()
    if rel is None or not text:
        return CheckResult.fail("没有 README，无法检查使用示例")
    title = md.find_heading(text, EXAMPLE_KEYWORDS)
    if not title:
        return CheckResult.fail("README 缺少『使用 / 示例』章节")
    has_io = "输入" in text and "输出" in text
    has_fence = any(b.strip() for b in md.fenced_blocks(text))
    has_image = bool(re.search(r"!\[[^\]]*\]\([^)]+\.(?:png|gif|jpe?g|webp|svg)\)", text, re.I))
    evidence = []
    if has_io:
        evidence.append("输入/输出示例")
    if has_fence:
        evidence.append("代码块")
    if has_image:
        evidence.append("截图")
    if not evidence:
        return CheckResult.fail(f"找到『{title}』章节，但没有任何输入/输出、代码块或截图")
    return CheckResult.ok(f"『{title}』章节（{'、'.join(evidence)}）")


def _rq05_structure(facts: Facts) -> CheckResult:
    rel, text = facts.readme()
    if rel is None or not text:
        return CheckResult.fail("没有 README，无法检查项目结构说明")
    title = md.find_heading(text, STRUCTURE_KEYWORDS)
    tree_blocks = [b for b in md.fenced_blocks(text) if ("├" in b or "└" in b or "|--" in b)]
    if not title and not tree_blocks:
        return CheckResult.fail("README 缺少『项目结构』章节（或目录树代码块）")
    where = f"章节『{title}』" if title else "目录树代码块"
    return CheckResult.ok(f"{where}，含 {len(tree_blocks)} 个目录树")


def _rq06_stack(facts: Facts) -> CheckResult:
    rel, text = facts.readme()
    if rel is None or not text:
        return CheckResult.fail("没有 README，无法检查技术栈说明")
    title = md.find_heading(text, STACK_KEYWORDS)
    versioned = re.search(r"(python|node|node\.js|java|golang|rust|go)\s*3?\.\d+", text, re.I)
    if not title and not versioned:
        return CheckResult.fail("README 缺少『技术栈 / 环境要求』章节")
    where = f"章节『{title}』" if title else f"版本说明（{versioned.group(0) if versioned else ''}）"  # type: ignore[union-attr]
    return CheckResult.ok(where)


def _rq07_license(facts: Facts) -> CheckResult:
    rel, text = facts.license()
    if rel is None or not text:
        return CheckResult.fail("未找到 LICENSE 文件（推荐 MIT 或 Apache-2.0）")
    found = [name for name, pattern in LICENSE_PATTERNS if re.search(pattern, text, re.I)]
    if not found:
        return CheckResult.fail(f"{rel} 存在，但未识别出标准开源协议文本")
    return CheckResult.ok(f"{rel} → {' / '.join(found)}")


def _rq08_gitignore(facts: Facts) -> CheckResult:
    rel = facts.resolve(".gitignore") or (facts.files_named(".gitignore") or [None])[0]  # type: ignore[list-item]
    if rel is None:
        return CheckResult.fail("未找到 .gitignore")
    text = facts.read(rel) or ""
    effective = [
        line
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if len(effective) < 3:
        return CheckResult.fail(f"{rel} 只有 {len(effective)} 条有效规则（需 ≥3）")
    return CheckResult.ok(f"{rel}（{len(effective)} 条规则）")


# --------------------------------------------------------------------------- #
# 社区要素 community (20)
# --------------------------------------------------------------------------- #


def _cm01_contributing(facts: Facts) -> CheckResult:
    candidates = (
        facts.files_named("contributing.md", "contributing.rst")
        + facts.glob(".github/contributing*")
        + facts.glob("docs/contributing*")
    )
    if facts.has_dir("contributing") and facts.files_under("contributing"):
        candidates.append(facts.files_under("contributing")[0])
    if not candidates:
        return CheckResult.fail("未找到 CONTRIBUTING.md（贡献指南）")
    rel = sorted(candidates)[0]
    length = facts.text_length(rel)
    if length < 300:
        return CheckResult.fail(f"{rel} 只有 {length} 字符，贡献指南过于单薄")
    return CheckResult.ok(f"{rel}（{length} 字符）")


def _cm02_issue_templates(facts: Facts) -> CheckResult:
    templates = facts.glob(".github/issue_template/*") + facts.glob(".github/issue_template*")
    templates = [t for t in templates if _suffix(t) in {".md", ".yml", ".yaml"}]
    if not templates:
        return CheckResult.fail("未找到 .github/ISSUE_TEMPLATE/ 模板（.md 或 .yml）")
    return CheckResult.ok(
        f"{len(templates)} 个模板：" + "、".join(Path(t).name for t in templates[:4])
    )


def _cm03_pr_template(facts: Facts) -> CheckResult:
    templates = (
        facts.glob(".github/pull_request_template*")
        + facts.glob(".github/pull_request_template/*")
        + facts.glob("pull_request_template*")
        + facts.glob("docs/pull_request_template*")
    )
    if not templates:
        return CheckResult.fail("未找到 .github/PULL_REQUEST_TEMPLATE.md")
    return CheckResult.ok(sorted(templates)[0])


def _cm04_changelog(facts: Facts) -> CheckResult:
    candidates = facts.files_named(
        "changelog.md", "changelog.rst", "history.md", "changes.md", "news.md"
    ) + facts.glob(".github/changelog*")
    if not candidates:
        return CheckResult.fail("未找到 CHANGELOG.md")
    rel = sorted(candidates)[0]
    text = facts.read(rel) or ""
    has_version = re.search(r"v?\d+\.\d+(\.\d+)?", text) is not None
    if not has_version or md.count_nonempty_lines(text) < 8:
        return CheckResult.fail(f"{rel} 缺少版本号条目或内容过短")
    versions = sorted(set(re.findall(r"v?\d+\.\d+(\.\d+)?", text)))
    return CheckResult.ok(f"{rel}（{len(versions)} 个版本条目）")


def _cm05_coc(facts: Facts) -> CheckResult:
    candidates = (
        facts.files_named("code_of_conduct.md", "code-of-conduct.md")
        + facts.glob(".github/code_of_conduct*")
        + facts.glob(".github/code-of-conduct*")
        + facts.glob("docs/code_of_conduct*")
    )
    if not candidates:
        return CheckResult.fail("未找到 CODE_OF_CONDUCT.md")
    return CheckResult.ok(sorted(candidates)[0])


def _cm06_ci(facts: Facts) -> CheckResult:
    patterns = (
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        ".gitlab-ci.yml",
        ".travis.yml",
        ".circleci/config.yml",
        "azure-pipelines.yml",
        "appveyor.yml",
        "bitbucket-pipelines.yml",
        "jenkinsfile",
    )
    for pattern in patterns:
        hits = facts.glob(pattern)
        if hits:
            return CheckResult.ok(sorted(hits)[0])
    return CheckResult.fail("未找到 CI 配置（.github/workflows/、GitLab CI 等）")


def _cm07_version(facts: Facts) -> CheckResult:
    if facts.has("pyproject.toml"):
        text = facts.read("pyproject.toml") or ""
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.M)
        if match:
            return CheckResult.ok(f"pyproject.toml → {match.group(1)}")
    if facts.has("package.json"):
        text = facts.read("package.json") or ""
        match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        if match:
            return CheckResult.ok(f"package.json → {match.group(1)}")
    for name in ("VERSION", "version.txt"):
        if facts.has(name):
            value = (facts.read(name) or "").strip()
            if value:
                return CheckResult.ok(f"{name} → {value[:20]}")
    hits = facts.search(r"__version__\s*=\s*['\"][^'\"]+['\"]")
    if hits:
        return CheckResult.ok(f"{hits[0][0]} → {hits[0][2][:40]}")
    if facts.has("CHANGELOG.md"):
        return CheckResult.ok("CHANGELOG.md 提供版本记录")
    return CheckResult.fail("未找到版本标识（pyproject/package.json/VERSION/__version__）")


# --------------------------------------------------------------------------- #
# 产物完整性 artifactCompleteness (15)
# --------------------------------------------------------------------------- #


def _ac01_content(facts: Facts) -> CheckResult:
    code = _code_files(facts)
    total_lines = 0
    for rel in code[:60]:
        total_lines += _file_nonempty_lines(facts, rel)
    if code and (total_lines >= 40 or len(code) >= 3):
        return CheckResult.ok(f"{len(code)} 个源码文件，约 {total_lines} 行非空代码")
    content = [
        f
        for f in facts.files
        if f.lower().startswith(("docs/", "prompts/", "data/", "content/", "notes/"))
        and _suffix(f) in {".md", ".csv", ".json", ".txt"}
    ]
    if len(content) >= 3:
        return CheckResult.ok(f"内容型项目：{len(content)} 个 docs/prompts/data 文件")
    return CheckResult.fail(
        "既没有可运行的源码（≥40 行或 ≥3 个文件），也没有成体系的内容文件（docs/ prompts/ data/）"
    )


def _ac02_tests(facts: Facts) -> CheckResult:
    tests = _test_files(facts)
    if not tests:
        return CheckResult.fail("未找到测试文件（tests/ 或 test_*.py 等）")
    with_assertions = 0
    assertions = 0
    for rel in tests:
        count = _assertion_count(facts, rel)
        assertions += count
        if count:
            with_assertions += 1
    if not with_assertions:
        return CheckResult.fail(f"找到 {len(tests)} 个测试文件，但没有断言（def test / it() / assert）")
    return CheckResult.ok(f"{len(tests)} 个测试文件，{assertions} 处断言")


def _ac03_examples(facts: Facts) -> CheckResult:
    for directory in ("examples", "example", "demo", "samples"):
        if facts.has_dir(directory) and facts.files_under(directory):
            count = len(facts.files_under(directory))
            return CheckResult.ok(f"{directory}/（{count} 个文件）")
    images = facts.images()
    if images:
        return CheckResult.ok(f"{len(images)} 张图片（如 {Path(images[0]).name}）")
    _rel, text = facts.readme()
    if text and re.search(r"!\[[^\]]*\]\([^)]+\.(?:png|gif|jpe?g|webp|svg)\)", text, re.I):
        return CheckResult.ok("README 内嵌截图/GIF")
    return CheckResult.fail("未找到示例目录（examples/ demo/）或截图")


def _ac04_entry(facts: Facts) -> CheckResult:
    if facts.has("pyproject.toml"):
        text = facts.read("pyproject.toml") or ""
        if "[project.scripts]" in text or "console_scripts" in text:
            return CheckResult.ok("pyproject.toml 声明了命令行入口")
    if facts.has("package.json"):
        text = facts.read("package.json") or ""
        if '"scripts"' in text:
            return CheckResult.ok("package.json 声明了 scripts")
    hits = facts.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]")
    if hits:
        return CheckResult.ok(f"{hits[0][0]} 提供 __main__ 入口")
    for name in ("main.py", "app.py", "cli.py", "index.js", "index.ts", "main.go"):
        if facts.has(name):
            return CheckResult.ok(name)
    if facts.has("Makefile"):
        text = facts.read("Makefile") or ""
        if re.search(r"^run\s*:", text, re.M):
            return CheckResult.ok("Makefile 提供 run 目标")
    return CheckResult.fail("未找到可运行入口（__main__ / cli / scripts / Makefile run）")


def _ac05_dependencies(facts: Facts) -> CheckResult:
    for manifest in DEPENDENCY_MANIFESTS:
        if facts.has(manifest):
            return CheckResult.ok(manifest)
    _rel, text = facts.readme()
    if text:
        lowered = text.lower()
        for phrase in (
            "零依赖",
            "无第三方依赖",
            "仅标准库",
            "no dependencies",
            "no external dependencies",
            "standard library only",
        ):
            if phrase in lowered:
                return CheckResult.ok(f"README 声明：{phrase}")
    return CheckResult.fail(
        "未找到依赖声明（pyproject.toml / requirements.txt / package.json 等）"
    )


def _ac06_attribution(facts: Facts) -> CheckResult:
    candidates = facts.files_named(
        "attribution.md", "credits.md", "notice.md", "notice", "acknowledgements.md", "拿来说明.md"
    ) + facts.glob("docs/attribution*")
    if not candidates:
        return CheckResult.fail("未找到 ATTRIBUTION.md（拿来说明 / 借鉴来源）")
    rel = sorted(candidates)[0]
    text = facts.read(rel) or ""
    length = len(text)
    if length < 200:
        return CheckResult.fail(f"{rel} 只有 {length} 字符，需写明具体借鉴来源")
    todos = _scaffold_count(text)
    if todos >= 3:
        return CheckResult.fail(f"{rel} 仍是未填充的骨架（{todos} 处 TODO/占位标记），请写明真实来源")
    return CheckResult.ok(f"{rel}（{length} 字符）")


def _ac07_no_empty_core(facts: Facts) -> CheckResult:
    core_names = (
        "README.md",
        ".gitignore",
        "LICENSE",
        "LICENSE.md",
        "AI_LOG.md",
        "ATTRIBUTION.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
    )
    empty = [name for name in core_names if facts.has(name) and facts.text_length(name) == 0]
    empty += [
        rel
        for rel in facts.files_named(".gitignore", "license", "license.md")
        if facts.sizes.get(rel) == 0 and rel not in empty
    ]
    if empty:
        return CheckResult.fail("空文件：" + "、".join(sorted(set(empty))))
    return CheckResult.ok("核心文件均非空")


# --------------------------------------------------------------------------- #
# AI 使用质量 aiUsage (20)
# --------------------------------------------------------------------------- #


def _ai_log(facts: Facts) -> Tuple[Optional[str], str]:
    rel, text = facts.read_first(AI_LOG_NAMES)
    return rel, text or ""


def _ai01_ai_log(facts: Facts) -> CheckResult:
    rel, text = _ai_log(facts)
    if rel is None:
        return CheckResult.fail("未找到 AI_LOG.md（AI 使用日志）")
    if len(text) < 200:
        return CheckResult.fail(f"{rel} 只有 {len(text)} 字符，需记录具体使用过程")
    todos = _scaffold_count(text)
    if todos >= 5:
        return CheckResult.fail(
            f"{rel} 仍是未填充的骨架（{todos} 处 TODO/占位标记），请用真实过程替换"
        )
    return CheckResult.ok(f"{rel}（{len(text)} 字符）")


def _ai02_stages(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法统计阶段覆盖")
    matched = [stage for stage, words in STAGE_KEYWORDS.items() if md.contains_any(text, words)]
    if len(matched) < 3:
        return CheckResult.fail(
            f"AI 日志只覆盖 {len(matched)} 个阶段（{'、'.join(matched) or '无'}），需 ≥3"
        )
    return CheckResult.ok("、".join(matched))


def _ai03_prompts(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查 prompt 记录")
    quoted_blocks = [b for b in md.fenced_blocks(text) if len(b.strip()) >= 30]
    markers = re.findall(r"^\s*(?:prompt|提示词|指令|用户输入)\s*[:：>]", text, re.I | re.M)
    if not quoted_blocks and len(markers) < 2:
        return CheckResult.fail("AI 日志没有引用任何 prompt 原文（代码块或『Prompt：』标记）")
    return CheckResult.ok(f"{len(quoted_blocks)} 段引用 + {len(markers)} 处 prompt 标记")


def _ai04_iterations(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查迭代记录")
    versions = sorted(set(re.findall(r"v(\d+\.\d+(?:\.\d+)?)", text)))
    rounds = re.findall(r"第\s*\d+\s*轮|round\s*\d+", text, re.I)
    iter_count = text.count("迭代")
    fix_count = text.count("修正") + text.count("重写") + text.count("返工")
    signals = 0
    if len(versions) >= 2:
        signals += 2
    if rounds:
        signals += 1
    if iter_count >= 3:
        signals += 1
    if fix_count >= 2:
        signals += 1
    if signals < 2:
        return CheckResult.fail(
            f"迭代证据不足（版本 {len(versions)} 个 / 轮次 {len(rounds)} 次 / 迭代 {iter_count} 次）"
        )
    return CheckResult.ok(
        f"版本 {len(versions)} 个（{'、'.join('v' + v for v in versions[:4])}），"
        f"轮次 {len(rounds)}，迭代 {iter_count} 次，修正 {fix_count} 次"
    )


def _ai05_cross_reference(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查与仓库的对应关系")
    tokens = set(re.findall(r"`([^`\n]{2,80})`", text))
    referenced: List[str] = []
    for token in sorted(tokens):
        cleaned = token.strip().lstrip("./").replace("\\", "/").split()[0] if token.strip() else ""
        cleaned = cleaned.rstrip("/")
        if not cleaned or " " in cleaned:
            continue
        if facts.has(cleaned):
            referenced.append(cleaned)
        else:
            base = Path(cleaned).name
            if base and (facts.files_named(base) or facts.has_dir(base)):
                referenced.append(cleaned)
    if len(referenced) < 3:
        return CheckResult.fail(f"AI 日志只引用了 {len(referenced)} 个仓库内真实文件（需 ≥3）")
    return CheckResult.ok(f"{len(referenced)} 个，如 " + "、".join(f"`{r}`" for r in referenced[:5]))


# --------------------------------------------------------------------------- #
# 复盘质量 reflectionQuality (20)
# --------------------------------------------------------------------------- #


def _rf01_aar(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查 AAR 结构")
    matched = [name for name, words in AAR_GROUPS if md.contains_any(text, words)]
    if len(matched) < 3:
        return CheckResult.fail(
            f"AAR 要素只覆盖 {len(matched)} 项（{'、'.join(matched) or '无'}），需 ≥3（预期/实际/差异/改进）"
        )
    return CheckResult.ok("覆盖：" + "、".join(matched))


def _rf02_failures(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查失败经验")
    heading = md.find_heading(
        text, ("失败", "问题", "踩坑", "坑", "教训", "lesson", "incident", "bug")
    )
    hits = re.findall(r"失败|踩坑|坑|bug|错误|报错|回滚|重来|推翻|问题|教训|返工", text, re.I)
    if not heading and len(hits) < 3:
        return CheckResult.fail("AI 日志没有记录失败/问题/踩坑经验")
    source = f"章节『{heading}』" if heading else f"{len(hits)} 处失败相关记录"
    return CheckResult.ok(source)


def _rf03_improvements(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if facts.has("ROADMAP.md"):
        roadmap = facts.read("ROADMAP.md") or ""
        if md.count_nonempty_lines(roadmap) >= 5:
            return CheckResult.ok("ROADMAP.md")
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查改进方案")
    section = md.find_section(text, ("改进", "下一步", "后续", "计划", "roadmap", "action", "todo"))
    if section:
        bullets = md.list_items(section.body, include_tasks=True)
        if len(bullets) >= 2 and len(section.body.strip()) >= 60:
            return CheckResult.ok(f"章节『{section.title}』（{len(bullets)} 条可执行项）")
    return CheckResult.fail("AI 日志缺少『改进 / 下一步』章节（≥2 条可执行项）")


def _rf04_landing(facts: Facts) -> CheckResult:
    _rel, text = _ai_log(facts)
    if not text:
        return CheckResult.fail("没有 AI 日志，无法检查落地证据")
    candidates = (
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "README.md",
        "docs/",
        ".github/",
        "tests/",
        "SKILL.md",
        "pyproject.toml",
        "examples/",
    )
    lowered = text.lower()
    landed = []
    for name in candidates:
        if name.lower() not in lowered:
            continue
        if name.endswith("/"):
            if facts.has_dir(name.rstrip("/")):
                landed.append(name)
        elif facts.has(name):
            landed.append(name)
    if len(landed) < 2:
        return CheckResult.fail(f"复盘结论只落到 {len(landed)} 个真实文件/目录（需 ≥2）")
    return CheckResult.ok("、".join(landed[:5]))


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

RULES: Tuple[Rule, ...] = (
    # 仓库质量 repoQuality (25)
    Rule("RQ01", "README 存在且非单薄", "repoQuality", 5, "required",
         "创建 README.md，包含项目说明（≥200 字符）", _rq01_readme_exists),
    Rule("RQ02", "README 一句话描述", "repoQuality", 3, "required",
         "在 H1 下方写一行『输入____，输出____』式描述", _rq02_tagline),
    Rule("RQ03", "README 安装/快速开始", "repoQuality", 3, "required",
         "增加『快速开始/安装』章节，附可复制的命令", _rq03_install),
    Rule("RQ04", "README 使用示例", "repoQuality", 3, "required",
         "增加『使用/示例』章节：输入、输出、代码块或截图", _rq04_example),
    Rule("RQ05", "README 项目结构", "repoQuality", 2, "recommended",
         "增加『项目结构』章节或目录树代码块", _rq05_structure),
    Rule("RQ06", "README 技术栈", "repoQuality", 2, "recommended",
         "增加『技术栈/环境要求』章节", _rq06_stack),
    Rule("RQ07", "LICENSE 开源协议", "repoQuality", 4, "required",
         "添加标准 LICENSE 文件（MIT / Apache-2.0 等）", _rq07_license),
    Rule("RQ08", ".gitignore", "repoQuality", 3, "required",
         "添加 .gitignore，至少 3 条有效规则", _rq08_gitignore),
    # 社区要素 community (20)
    Rule("CM01", "贡献指南 CONTRIBUTING", "community", 4, "recommended",
         "添加 CONTRIBUTING.md（如何跑测试、提交规范）", _cm01_contributing),
    Rule("CM02", "Issue 模板", "community", 4, "recommended",
         "添加 .github/ISSUE_TEMPLATE/*.md 或 *.yml", _cm02_issue_templates),
    Rule("CM03", "PR 模板", "community", 3, "recommended",
         "添加 .github/PULL_REQUEST_TEMPLATE.md", _cm03_pr_template),
    Rule("CM04", "CHANGELOG", "community", 3, "recommended",
         "添加 CHANGELOG.md，按版本记录变更", _cm04_changelog),
    Rule("CM05", "行为准则 CODE_OF_CONDUCT", "community", 2, "recommended",
         "添加 CODE_OF_CONDUCT.md（可用 Contributor Covenant）", _cm05_coc),
    Rule("CM06", "CI 自动化", "community", 3, "recommended",
         "添加 .github/workflows/ci.yml 跑测试", _cm06_ci),
    Rule("CM07", "版本标识", "community", 1, "recommended",
         "在 pyproject/package.json/VERSION 中声明版本号", _cm07_version),
    # 产物完整性 artifactCompleteness (15)
    Rule("AC01", "实际项目内容", "artifactCompleteness", 3, "required",
         "提交真实源码（≥40 行或 ≥3 个文件）或成体系的内容文件", _ac01_content),
    Rule("AC02", "自动化测试", "artifactCompleteness", 3, "recommended",
         "添加 tests/ 并写断言（unittest/pytest）", _ac02_tests),
    Rule("AC03", "示例/Demo", "artifactCompleteness", 2, "recommended",
         "提供 examples/ 目录或截图/GIF", _ac03_examples),
    Rule("AC04", "可运行入口", "artifactCompleteness", 2, "recommended",
         "提供 python -m / cli / scripts 入口", _ac04_entry),
    Rule("AC05", "依赖声明", "artifactCompleteness", 2, "recommended",
         "提供 pyproject.toml / requirements.txt，或在 README 声明零依赖", _ac05_dependencies),
    Rule("AC06", "拿来说明 ATTRIBUTION", "artifactCompleteness", 2, "required",
         "添加 ATTRIBUTION.md，写明借鉴来源与改动", _ac06_attribution),
    Rule("AC07", "核心文件非空", "artifactCompleteness", 1, "recommended",
         "清理 0 字节的占位文件", _ac07_no_empty_core),
    # AI 使用质量 aiUsage (20)
    Rule("AI01", "AI_LOG.md 存在", "aiUsage", 6, "required",
         "添加 AI_LOG.md，记录 AI 辅助开发过程", _ai01_ai_log),
    Rule("AI02", "阶段覆盖 ≥3", "aiUsage", 4, "recommended",
         "按初始化/编码/文档/审查/测试/发布分阶段记录", _ai02_stages),
    Rule("AI03", "prompt 原文留痕", "aiUsage", 4, "recommended",
         "引用关键 prompt 原文（代码块或『Prompt：』标记）", _ai03_prompts),
    Rule("AI04", "多轮迭代记录", "aiUsage", 3, "recommended",
         "记录版本迭代、轮次或返工修正", _ai04_iterations),
    Rule("AI05", "与仓库文件对应", "aiUsage", 3, "recommended",
         "日志中引用仓库内真实文件路径（反引号，≥3 个）", _ai05_cross_reference),
    # 复盘质量 reflectionQuality (20)
    Rule("RF01", "AAR 四要素", "reflectionQuality", 5, "recommended",
         "按 预期/实际/差异/改进 结构复盘（≥3 项）", _rf01_aar),
    Rule("RF02", "失败与踩坑记录", "reflectionQuality", 5, "recommended",
         "记录失败尝试、bug、返工过程", _rf02_failures),
    Rule("RF03", "可执行改进方案", "reflectionQuality", 5, "recommended",
         "『改进/下一步』章节列出 ≥2 条可执行项", _rf03_improvements),
    Rule("RF04", "复盘落地证据", "reflectionQuality", 5, "recommended",
         "复盘结论对应到仓库内真实文件（≥2 个）", _rf04_landing),
)

RULES_BY_ID: Dict[str, Rule] = {rule.id: rule for rule in RULES}


def run_rules(facts: Facts) -> List[Finding]:
    """Run every rule against *facts*, preserving registry order."""
    return [Finding(rule, rule.check(facts)) for rule in RULES]
