"""``python -m shipcheck`` entry point (delegates to :mod:`shipcheck.cli`)."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
