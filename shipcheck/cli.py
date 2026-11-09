"""Command line interface.

Exit codes
----------
0  all required rules pass and the score is at/above ``--min-score``
1  at least one *required* rule failed (blocking)
2  score below ``--min-score``
3  usage error (path missing, bad flags, ...)

The CLI forces UTF-8 on stdout/stderr so Chinese output survives the default
GBK code page on Chinese Windows.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from . import engine, fixer, report
from .facts import Facts
from .report import Palette
from .rules import RULES


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError, OSError):
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shipcheck",
        description="shipcheck —— 开源仓库发布体检：输入一个项目目录，输出 100 分制体检报告与修复清单。",
        epilog="示例：python -m shipcheck . --fix --apply -f markdown -o REPORT.md",
    )
    parser.add_argument("path", nargs="?", default=".", help="要体检的仓库目录（默认当前目录）")
    parser.add_argument(
        "-f", "--format", choices=("text", "markdown", "json"), default="text",
        help="输出格式（默认 text）",
    )
    parser.add_argument("-o", "--output", metavar="FILE", help="写入文件而不是标准输出")
    parser.add_argument(
        "--min-score", type=int, default=80, metavar="N",
        help="CI 门槛分，低于该分数退出码为 2（默认 80）",
    )
    parser.add_argument("--fix", action="store_true", help="列出可自动补齐的骨架文件（干跑）")
    parser.add_argument("--apply", action="store_true", help="与 --fix 连用：真正写入骨架文件")
    parser.add_argument("--list-rules", action="store_true", help="打印全部规则与权重")
    parser.add_argument("--no-color", action="store_true", help="禁用 ANSI 颜色")
    parser.add_argument("-v", "--verbose", action="store_true", help="text 格式下列出已通过项")
    parser.add_argument(
        "-V", "--version", action="version", version=f"shipcheck {__version__}"
    )
    return parser


def _emit(text: str, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"已写入 {output}")
    else:
        print(text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _force_utf8()
    args = build_parser().parse_args(argv)

    if args.list_rules:
        palette = Palette(enabled=not args.no_color and sys.stdout.isatty())
        _emit(report.rules_table(RULES, palette=palette), args.output)
        return 0

    if args.apply and not args.fix:
        print("错误：--apply 需要与 --fix 一起使用", file=sys.stderr)
        return 3

    try:
        facts = Facts.build(args.path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3

    if args.fix:
        plan_items = fixer.plan(facts)
        if not args.apply:
            if args.format == "json":
                payload = {
                    "schema": "shipcheck.fixplan/1",
                    "root": str(facts.root),
                    "items": [{"rule": i.rule_id, "path": i.path} for i in plan_items],
                }
                import json

                _emit(json.dumps(payload, ensure_ascii=False, indent=2), args.output)
            else:
                _emit(fixer.render_plan(plan_items), args.output)
            return 0
        created, skipped = fixer.apply(plan_items, facts.root)
        if args.format == "text":
            if created:
                print(f"已创建 {len(created)} 个骨架文件：")
                for path in created:
                    print(f"  + {path}")
            else:
                print("没有需要创建的骨架文件。")
            if skipped:
                print(f"跳过已存在的 {len(skipped)} 个文件（从不覆盖）")
            print()

    result = engine.audit(facts.root)
    exit_code = engine.compute_exit_code(result, args.min_score)

    if args.format == "text":
        palette = Palette(enabled=not args.no_color and sys.stdout.isatty() and not args.output)
        text = report.render_text(result, palette=palette, verbose=args.verbose)
    elif args.format == "markdown":
        text = report.render_markdown(result)
    else:
        text = report.render_json(result, args.min_score, exit_code)
    _emit(text, args.output)
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
