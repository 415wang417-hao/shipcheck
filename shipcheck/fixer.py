"""Scaffold missing community files (``--fix`` / ``--fix --apply``).

The fixer never overwrites an existing file and never invents content: it
creates clearly marked skeletons (with ``TODO`` markers) that a human must
fill in.  The rule engine deliberately fails on logs that are still full of
TODOs, so scaffolding can bump structure scores but never fake AI-usage or
attribution scores.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from .facts import Facts

# --------------------------------------------------------------------------- #
# Template context
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Context:
    project: str
    year: int
    holder: str


def _context(facts: Facts) -> Context:
    holder = "YOUR NAME"
    return Context(
        project=facts.root.name,
        year=_dt.date.today().year,
        holder=holder,
    )


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #


def _t_readme(ctx: Context) -> str:
    return f"""# {ctx.project}

TODO（一句话描述）：输入____，输出____。

## 解决什么问题

TODO：为什么需要这个项目？没有它之前怎么做？有了它之后怎么做？

## 快速开始

### 安装

```bash
git clone https://github.com/<你的用户名>/{ctx.project}.git
cd {ctx.project}
# TODO：安装依赖的命令（若零依赖，写明“仅标准库，无需安装”）
```

### 使用

```bash
# TODO：最简单的使用命令
```

## 示例

输入：

> TODO（示例输入）

输出：

> TODO（示例输出）

## 项目结构

```text
{ctx.project}/
├── README.md
├── LICENSE
├── src/           （源码）
├── docs/          （文档）
├── examples/      （示例）
└── tests/         （测试）
```

## 技术栈

- 语言：TODO（如 Python 3.11）
- 框架：TODO
- AI 集成：TODO

## AI 生成说明

本项目使用 AI 辅助开发，详见 [AI_LOG.md](./AI_LOG.md)。

## 借鉴来源

本项目参考了以下来源，详见 [ATTRIBUTION.md](./ATTRIBUTION.md)。

## License

MIT
"""


def _t_license(ctx: Context) -> str:
    return f"""MIT License

Copyright (c) {ctx.year} {ctx.holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _t_gitignore(ctx: Context) -> str:
    return """# --- Python ---
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.tox/

# --- Node ---
node_modules/
npm-debug.log*

# --- 系统与编辑器 ---
.DS_Store
Thumbs.db
desktop.ini
.idea/
.vscode/
*.swp

# --- 本地敏感文件 ---
.env
.env.local
*.local
secrets/
"""


def _t_ai_log(ctx: Context) -> str:
    return f"""# AI 使用日志（AI_LOG）

> 记录本项目 AI 辅助开发的全过程：哪个阶段、用了什么 prompt、产出了什么、人工做了哪些修正。
> 本骨架由 `python -m shipcheck . --fix --apply` 生成，其中 TODO 需要用真实过程填充；
> 未填充的日志会被体检规则识别为脚手架。

## 1. 阶段总览

| 阶段 | AI 工具 | 用途 | 产出 |
| --- | --- | --- | --- |
| 初始化 | TODO | TODO | TODO |
| 代码编写 | TODO | TODO | TODO |
| 文档撰写 | TODO | TODO | TODO |
| 代码审查 | TODO | TODO | TODO |
| 测试/调试 | TODO | TODO | TODO |

## 2. Prompt 记录

### 初始化

```text
Prompt：TODO（粘贴当时的原话）
```

产出：TODO

### 代码编写

```text
Prompt：TODO
```

产出：TODO

## 3. 迭代记录

- v0.1 → v0.2：TODO（改了什么、为什么改）
- TODO

## 4. 失败与踩坑

- TODO：失败尝试 / 报错 / 返工过程

## 5. AAR 复盘

- **预期**：TODO
- **实际**：TODO
- **差异**：TODO
- **改进**：
  - [ ] TODO
  - [ ] TODO

## 6. 人工步骤说明（反向举证）

- TODO：哪一段是手写的，为什么不用 AI
"""


def _t_attribution(ctx: Context) -> str:
    return f"""# 拿来说明（ATTRIBUTION）

> 本项目站在别人的肩膀上。这里逐条写明：借鉴了什么、从哪里来、如何使用、做了什么改动。
> 本骨架由 `python -m shipcheck . --fix --apply` 生成，TODO 需要人工填充。

## 1. 来源清单

| 来源 | 类型 | 借鉴内容 | 使用方式 | 改动 |
| --- | --- | --- | --- | --- |
| TODO（链接/名称） | 文档/代码/模板 | TODO | TODO | TODO |

## 2. 逐条说明

### 来源一：TODO 名称

- 原文/原仓库：TODO
- 我们拿了什么：TODO
- 为什么拿：TODO
- 我们改了什么：TODO
- 许可证：TODO

## 3. 声明

- 本项目的原创部分以 LICENSE 声明的协议开源。
- 若来源标注有遗漏，请提 Issue 指正，我们会第一时间补齐。
"""


def _t_contributing(ctx: Context) -> str:
    return f"""# 贡献指南（CONTRIBUTING）

感谢你愿意为 {ctx.project} 做贡献！请花两分钟读完下面的流程。

## 如何报告问题

1. 先搜索 [Issues](../../issues) 里是否已有相同问题；
2. 没有的话，用 **Bug report** 模板新建 Issue，附上复现步骤与期望/实际输出。

## 如何提交改动

1. Fork 本仓库并创建分支：`git checkout -b feat/你的改动`；
2. 保持改动最小、聚焦一件事；
3. 跑通测试（见下）；
4. 提交 PR，按模板填写“做了什么 / 为什么 / 怎么验证”。

## 开发环境

```bash
git clone https://github.com/<你的用户名>/{ctx.project}.git
cd {ctx.project}
python -m unittest discover -s tests -v
```

## 提交信息规范

- `feat:` 新功能 · `fix:` 修复 · `docs:` 文档 · `test:` 测试 · `refactor:` 重构
- 一行说清楚“做了什么”，正文说“为什么”。

## 行为准则

参与本项目即表示你同意遵守 [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)。
"""


def _t_coc(ctx: Context) -> str:
    return """# 行为准则（Code of Conduct）

## 我们的承诺

为了营造一个开放友好的环境，无论身份背景，所有参与者都是受欢迎的。

## 我们的准则

- 保持尊重与耐心，对事不对人；
- 接受建设性批评，也乐于给出建设性批评；
- 关注对社区整体最有利的选择；
- 不容忍骚扰、人身攻击或任何形式的歧视言论。

## 不被接受的行为

- 性别、性向、残障、外貌、种族、宗教相关的攻击性言论；
- 公开或私下的骚扰；
- 未经许可发布他人隐私信息；
- 其他可被合理认定为不专业的行为。

## 执行

违反准则的行为，维护者可予以警告、删除内容乃至封禁。
举报请联系维护者邮箱（见 SECURITY.md），所有举报都会被认真处理。

## 致谢

本准则的思路参考 [Contributor Covenant](https://www.contributor-covenant.org/)（v2.1），
为适配本项目做了精简改写。
"""


def _t_changelog(ctx: Context) -> str:
    return f"""# 更新日志（CHANGELOG）

本项目的所有重要变更都记录在此，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Planned

- TODO

## [0.1.0] - {_dt.date.today().isoformat()}

### Added

- 项目初始版本（TODO：写明第一个版本包含什么）。
"""


def _t_issue_bug(ctx: Context) -> str:
    return """---
name: Bug 报告
about: 什么东西坏了、怎么复现
title: "[Bug] "
labels: bug
assignees: ''
---

**问题描述**

<!-- 一句话说清楚什么坏了 -->

**复现步骤**

1. 执行命令 `...`
2. 看到 `...`

**期望行为**

<!-- 你期望发生什么 -->

**实际输出 / 报错信息**

```text
粘贴完整报错或输出
```

**环境**

- 操作系统：
- Python / Node 版本：
- shipcheck 版本（`python -m shipcheck --version`）：

**补充信息**

<!-- 截图、日志等 -->
"""


def _t_issue_feature(ctx: Context) -> str:
    return """---
name: 功能建议
about: 你希望这个项目多做什么
title: "[Feature] "
labels: enhancement
assignees: ''
---

**要解决的问题**

<!-- 这个功能解决什么痛点？先说问题，再说方案 -->

**期望的方案**

<!-- 你希望它长什么样、怎么用 -->

**备选方案**

<!-- 其他可行的做法 -->

**其他**

<!-- 相关链接、截图等 -->
"""


def _t_issue_config(ctx: Context) -> str:
    return """blank_issues_enabled: false
contact_links:
  - name: 使用问题讨论
    url: https://github.com/<你的用户名>/<你的仓库>/discussions
    about: 使用上的疑问请到 Discussions 讨论
"""


def _t_pr_template(ctx: Context) -> str:
    return """## 这个 PR 做了什么

<!-- 一段话说清楚改动内容 -->

## 为什么这样改

<!-- 动机、背景、关联 Issue（写 “Closes #123”） -->

## 如何验证

- [ ] 本地跑过测试：`python -m unittest discover -s tests -v`
- [ ] 体检通过：`python -m shipcheck . --min-score 80`
- [ ] 更新了相关文档 / CHANGELOG

## 截图 / 输出（如适用）
"""


def _t_ci(ctx: Context) -> str:
    return """name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: 运行测试（零依赖，无需安装）
        run: python -m unittest discover -s tests -v
      - name: 仓库体检（shipcheck 自检）
        run: python -m shipcheck . --min-score 80
"""


def _t_test_smoke(ctx: Context) -> str:
    return '''"""最小冒烟测试（由 shipcheck --fix 生成）.

TODO：用真正的测试替换本文件，至少覆盖核心入口。
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestSmoke(unittest.TestCase):
    def test_repository_has_readme(self):
        readmes = list(REPO_ROOT.glob("README*"))
        self.assertTrue(readmes, "仓库缺少 README")


if __name__ == "__main__":
    unittest.main()
'''


TEMPLATES: Dict[str, Callable[[Context], str]] = {
    "readme": _t_readme,
    "license_mit": _t_license,
    "gitignore": _t_gitignore,
    "ai_log": _t_ai_log,
    "attribution": _t_attribution,
    "contributing": _t_contributing,
    "coc": _t_coc,
    "changelog": _t_changelog,
    "issue_bug": _t_issue_bug,
    "issue_feature": _t_issue_feature,
    "issue_config": _t_issue_config,
    "pr_template": _t_pr_template,
    "ci": _t_ci,
    "test_smoke": _t_test_smoke,
}

#: (rule_id, target_path, template_key) — order defines the dry-run listing.
FIX_TARGETS: Tuple[Tuple[str, str, str], ...] = (
    ("RQ01", "README.md", "readme"),
    ("RQ07", "LICENSE", "license_mit"),
    ("RQ08", ".gitignore", "gitignore"),
    ("AI01", "AI_LOG.md", "ai_log"),
    ("AC06", "ATTRIBUTION.md", "attribution"),
    ("CM01", "CONTRIBUTING.md", "contributing"),
    ("CM04", "CHANGELOG.md", "changelog"),
    ("CM05", "CODE_OF_CONDUCT.md", "coc"),
    ("CM02", ".github/ISSUE_TEMPLATE/bug_report.md", "issue_bug"),
    ("CM02", ".github/ISSUE_TEMPLATE/feature_request.md", "issue_feature"),
    ("CM02", ".github/ISSUE_TEMPLATE/config.yml", "issue_config"),
    ("CM03", ".github/PULL_REQUEST_TEMPLATE.md", "pr_template"),
    ("CM06", ".github/workflows/ci.yml", "ci"),
    ("AC02", "tests/test_smoke.py", "test_smoke"),
)


@dataclass(frozen=True)
class FixItem:
    rule_id: str
    path: str
    content: str


def plan(facts: Facts) -> List[FixItem]:
    """Missing skeleton files for this repository (never overwrites)."""
    ctx = _context(facts)
    items: List[FixItem] = []
    for rule_id, path, template_key in FIX_TARGETS:
        if path == "README.md":
            if facts.readme()[0] is not None:
                continue  # 已有 README：结构问题需要人工改，不覆盖
        elif facts.has(path):
            continue
        items.append(FixItem(rule_id, path, TEMPLATES[template_key](ctx)))
    return items


def apply(plan_items: List[FixItem], root: Path) -> Tuple[List[str], List[str]]:
    """Write every planned file; returns ``(created, skipped)``."""
    created: List[str] = []
    skipped: List[str] = []
    for item in plan_items:
        target = root / item.path
        if target.exists():
            skipped.append(item.path)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item.content, encoding="utf-8", newline="\n")
        created.append(item.path)
    return created, skipped


def render_plan(plan_items: List[FixItem]) -> str:
    lines = []
    if not plan_items:
        return "没有可自动补齐的文件——缺失项都需要人工编写，或仓库已经很完整。"
    lines.append(f"可自动补齐 {len(plan_items)} 个骨架文件（当前为干跑，未写入）：")
    lines.append("")
    for item in plan_items:
        lines.append(f"  [{item.rule_id}] {item.path}")
    lines.append("")
    lines.append("骨架内含 TODO 标记，必须人工填充；")
    lines.append("真正写入：python -m shipcheck . --fix --apply")
    return "\n".join(lines)
