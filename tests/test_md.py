"""Markdown 解析辅助（shipcheck.md）的单元测试。"""

from __future__ import annotations

import unittest

from shipcheck import md


class TestStripCode(unittest.TestCase):
    def test_removes_fenced_blocks(self):
        text = "# T\n\n```python\n## 这不是标题\n```\n\n## 这是标题\n"
        stripped = md.strip_code(text)
        self.assertNotIn("这不是标题", stripped)
        self.assertIn("这是标题", stripped)

    def test_tilde_fences(self):
        text = "~~~\n# fake\n~~~\n# real\n"
        self.assertNotIn("fake", md.strip_code(text))
        self.assertIn("real", md.strip_code(text))

    def test_html_comments_removed(self):
        text = "<!-- hidden heading: 安装 -->\n## 安装\n"
        stripped = md.strip_code(text)
        self.assertNotIn("hidden", stripped)
        self.assertIn("安装", stripped)


class TestHeadings(unittest.TestCase):
    def test_find_heading_bilingual(self):
        text = "# Project\n\n## 🚀 快速开始 Quick Start\n\ncontent\n"
        self.assertIsNotNone(md.find_heading(text, ("安装", "install", "quick start")))
        self.assertIsNone(md.find_heading(text, ("license",)))

    def test_ignores_headings_inside_code(self):
        text = "# T\n\n```markdown\n## 安装\n```\n"
        self.assertIsNone(md.find_heading(text, ("安装",)))


class TestSections(unittest.TestCase):
    def test_section_body(self):
        text = "# T\n\n## 改进\n\n- [ ] 第一条\n- [ ] 第二条\n\n## 其他\n\nx\n"
        section = md.find_section(text, ("改进", "下一步"))
        self.assertIsNotNone(section)
        self.assertEqual(len(md.list_items(section.body, include_tasks=True)), 2)


class TestFencedBlocks(unittest.TestCase):
    def test_collects_blocks(self):
        text = "```bash\npip install .\n```\n\ntext\n\n```python\nprint(1)\n```\n"
        blocks = md.fenced_blocks(text)
        self.assertEqual(len(blocks), 2)
        self.assertIn("pip install", blocks[0])


class TestFirstMeaningfulLine(unittest.TestCase):
    def test_skips_badges_and_headings(self):
        text = (
            "# Project\n"
            "\n"
            "[![CI](https://img.shields.io/badge/CI-passing)](x)\n"
            "![demo](demo.png)\n"
            "\n"
            "**Project** — 输入文件夹，输出清单。\n"
            "\n"
            "## 安装\n"
        )
        line = md.first_meaningful_line(text)
        self.assertIn("输入文件夹", line)

    def test_accepts_blockquote_tagline(self):
        text = "# Project\n\n> 输入 Markdown，输出结构化报告。\n\n## 安装\n"
        line = md.first_meaningful_line(text)
        self.assertEqual(line, "输入 Markdown，输出结构化报告。")

    def test_returns_none_when_only_noise(self):
        text = "# Project\n\n[![badge](x)](y)\n"
        self.assertIsNone(md.first_meaningful_line(text))


if __name__ == "__main__":
    unittest.main()
