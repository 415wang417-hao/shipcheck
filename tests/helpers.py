"""tests.helpers —— 用临时目录搭出可复用的合成仓库。"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

MIT_LICENSE = """MIT License

Copyright (c) 2026 Test Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

GOOD_README = """# sample-project

输入一个数字列表，输出排序后的列表和统计摘要。

## 解决什么问题

演示用 README，包含体检要求的全部章节。

## 快速开始

### 安装

```bash
git clone https://github.com/example/sample-project.git
cd sample-project
```

### 使用

```bash
python main.py 3 1 2
```

## 示例

输入：

> 3 1 2

输出：

> [1, 2, 3]

## 项目结构

```text
sample-project/
├── README.md
├── LICENSE
├── main.py
└── tests/
```

## 技术栈

- 语言：Python 3.11
- 依赖：仅标准库

## License

MIT
"""

MAIN_PY = '''"""示例入口：排序 + 统计。"""


def run(nums):
    """排序并返回。"""
    return sorted(nums)


def summary(nums):
    """返回最小值、最大值与均值。"""
    if not nums:
        return None
    return {"min": min(nums), "max": max(nums), "avg": sum(nums) / len(nums)}


def cli(argv):
    """命令行入口。"""
    nums = [int(a) for a in argv]
    print(run(nums))
    print(summary(nums))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(["3", "1", "2"]))
'''

UTILS_PY = '''"""示例工具模块。"""


def parse(line):
    """把一行空格分隔的数字解析成列表。"""
    return [int(tok) for tok in line.split()]


def render(nums):
    """渲染成 Markdown 列表。"""
    return "\\n".join(f"- {n}" for n in nums)
'''

TEST_MAIN_PY = '''"""main.run / main.summary 的单元测试。"""

import unittest

from main import run, summary


class TestRun(unittest.TestCase):
    def test_sorted(self):
        self.assertEqual(run([2, 1]), [1, 2])

    def test_empty(self):
        self.assertEqual(run([]), [])


class TestSummary(unittest.TestCase):
    def test_summary(self):
        self.assertEqual(summary([1, 2, 3])["avg"], 2)

    def test_empty_returns_none(self):
        self.assertIsNone(summary([]))
'''

TEST_UTILS_PY = '''"""utils 模块的单元测试。"""

import unittest

from utils import parse, render


class TestUtils(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse("3 1 2"), [3, 1, 2])

    def test_render(self):
        self.assertEqual(render([1]), "- 1")
'''


def make_repo(tmp: Path, files: Dict[str, str]) -> Path:
    """在 *tmp* 下按 ``{相对路径: 内容}`` 写出一个小型仓库。"""
    root = tmp / "repo"
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def good_repo_files() -> Dict[str, str]:
    """一个五脏俱全的合成仓库（用于验证各规则在达标时通过）。"""
    return {
        "README.md": GOOD_README,
        "LICENSE": MIT_LICENSE,
        ".gitignore": "__pycache__/\n*.pyc\n.env\n",
        "main.py": MAIN_PY,
        "utils.py": UTILS_PY,
        "tests/test_main.py": TEST_MAIN_PY,
        "tests/test_utils.py": TEST_UTILS_PY,
        "examples/input.txt": "3 1 2\n",
        "pyproject.toml": '[project]\nname = "sample"\nversion = "1.0.0"\n\n[project.scripts]\nsample = "main:cli"\n',
        "CHANGELOG.md": (
            "# 更新日志\n\n"
            "本文件记录项目的所有重要变更，格式参考 Keep a Changelog。\n\n"
            "## [1.0.0] - 2026-01-01\n\n"
            "### Added\n\n"
            "- 初始版本：`run()` 排序入口。\n"
            "- 增加 `summary()` 统计。\n"
            "- 增加 `utils.parse()` 解析。\n\n"
            "## [0.5.0] - 2025-12-01\n\n"
            "### Added\n\n"
            "- 项目雏形（内部试用）。\n"
        ),
        "CONTRIBUTING.md": (
            "# 贡献指南\n\n"
            "感谢你愿意为 sample-project 做贡献！\n\n"
            "## 如何报告问题\n\n"
            "先搜索已有 Issue，没有的话用 Bug 模板新建，附上复现步骤。\n\n"
            "## 如何提交改动\n\n"
            "1. Fork 并创建分支 `feat/你的改动`；\n"
            "2. 跑通测试（见下）；\n"
            "3. 提交 PR，按模板填写做了什么 / 为什么 / 怎么验证。\n\n"
            "## 开发环境\n\n"
            "```bash\n"
            "python -m unittest discover -s tests -t . -v\n"
            "```\n\n"
            "## 提交信息规范\n\n"
            "- `feat:` 新功能 · `fix:` 修复 · `docs:` 文档 · `test:` 测试\n"
        ),
        "CODE_OF_CONDUCT.md": (
            "# Code of Conduct\n\n保持友善与尊重。\n\n我们的承诺：开放友好的环境。\n\n"
            "不可接受行为：骚扰、人身攻击。\n"
        ),
        ".github/ISSUE_TEMPLATE/bug_report.md": "---\nname: Bug\ntitle: '[Bug] '\n---\n\n**问题描述**\n",
        ".github/ISSUE_TEMPLATE/feature_request.md": "---\nname: Feature\n---\n\n**功能描述**\n",
        ".github/PULL_REQUEST_TEMPLATE.md": "## 做了什么\n\n## 如何验证\n\n- [ ] 测试通过\n",
        ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
        "AI_LOG.md": (
            "# AI 使用日志\n\n"
            "## 阶段总览\n\n"
            "| 阶段 | 工具 | 用途 |\n| --- | --- | --- |\n"
            "| 初始化 | AI | 项目骨架 |\n"
            "| 代码编写 | AI | 实现函数 |\n"
            "| 文档撰写 | AI | README 初稿 |\n"
            "| 审查 | AI | 代码 review |\n"
            "| 测试 | AI | 编写 test |\n\n"
            "## Prompt 记录\n\n"
            "```text\n"
            "Prompt：帮我写一个排序函数和一个统计函数，"
            "放到 main.py 里，再配一组单元测试放在 tests/ 下。\n"
            "```\n\n"
            "产出：`main.py` 与 `tests/test_main.py`。\n\n"
            "## 迭代记录\n\n"
            "- v0.5 → v1.0：重写了 `main.py` 的入口，修正了边界情况。\n"
            "- 第 1 轮 review 后迭代了文档。\n\n"
            "## 失败与踩坑\n\n"
            "- 第一版 README 忘了写安装章节，报错后重写。\n"
            "- 第一版测试漏了空列表输入，失败后补上。\n\n"
            "## AAR 复盘\n\n"
            "- **预期**：一次成型。\n"
            "- **实际**：返工两次。\n"
            "- **差异**：低估了文档工作量。\n"
            "- **改进**：\n"
            "  - [ ] 下次先写 README 再写代码\n"
            "  - [ ] 每轮结束跑一次 `tests/`\n\n"
            "## 改进与下一步\n\n"
            "复盘结论已落地：更新了 `CHANGELOG.md` 和 `CONTRIBUTING.md`，"
            "并补充 `utils.py` 的解析函数。\n\n"
            "- [ ] 增加命令行参数解析\n"
            "- [ ] 输出支持 JSON 格式\n"
        ),
        "ATTRIBUTION.md": (
            "# 拿来说明\n\n"
            "## 来源清单\n\n"
            "| 来源 | 类型 | 借鉴内容 | 使用方式 |\n| --- | --- | --- | --- |\n"
            "| Python pathlib 官方文档 | 文档 | 目录遍历写法 | 直接采用 |\n"
            "| Keep a Changelog | 模板 | CHANGELOG 结构 | 采用其章节划分 |\n"
            "| GitHub Docs | 文档 | Issue 模板格式 | 参考实现 |\n\n"
            "## 逐条说明\n\n"
            "### Python pathlib 文档\n\n"
            "- 原文：docs.python.org/3/library/pathlib.html\n"
            "- 拿了什么：`Path.rglob` 的遍历方式\n"
            "- 为什么拿：标准库自带，避免第三方依赖\n"
            "- 改动：无，直接采用\n\n"
            "## 声明\n\n"
            "原创部分以 MIT 协议开源；若来源标注有遗漏请提 Issue 指正。\n"
        ),
    }
