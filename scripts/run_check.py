#!/usr/bin/env python3
"""独立运行脚本 —— 不安装也能跑 shipcheck。

Usage:
    python scripts/run_check.py <path>
    python scripts/run_check.py <path> --format json
    python scripts/run_check.py <path> --fix --apply
"""

import sys
from pathlib import Path

# Allow running from project root without installation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shipcheck.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
