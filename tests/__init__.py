"""tests 包 —— 全部使用标准库 unittest，零第三方依赖。"""

import sys
from pathlib import Path

# 让 tests 可以在未安装包的情况下从仓库根目录直接运行
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
