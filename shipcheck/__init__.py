"""shipcheck —— 开源仓库发布体检工具。

输入一个本地项目目录，输出一份 100 分制的“能不能发布到 GitHub”体检报告：
五个维度（仓库质量/社区要素/产物完整性/AI 使用质量/复盘质量）逐条检查，
给出缺口、修复建议，并可用 ``--fix --apply`` 生成缺失社区文件的骨架。

零第三方依赖，Python ≥ 3.9，标准库实现。

快速使用::

    python -m shipcheck .                # 体检当前目录
    python -m shipcheck . --fix          # 查看可自动补齐的文件（干跑）
    python -m shipcheck . -f markdown -o REPORT.md
"""

__version__ = "1.0.0"

__all__ = ["__version__"]
