"""Collect file-system facts about a repository once, for the rule engine.

The rule engine must be a pure function of the repository content: it reads
facts, never the disk directly.  Everything the rules need (file list,
directory list, sizes, decoded text) is gathered here exactly once, which also
keeps the whole audit to a single directory walk.

Design notes
------------
* Path lookup is case-insensitive because Windows and macOS are, and because
  ``README.MD`` must not be punished for its capitalisation.
* Only files smaller than :data:`MAX_TEXT_BYTES` are decoded, so scanning a
  repository that accidentally contains a 200 MB CSV stays fast.
* Text decoding falls back from UTF-8 to GB18030 (Chinese Windows default) and
  finally to Latin-1, so a stray GBK README does not crash the audit.
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

#: Directories that are never part of the project source.
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".tox",
    ".eggs",
    "site-packages",
    "dist",
    "build",
    ".next",
    "target",
}

#: Files larger than this are not decoded (they are almost never documentation).
MAX_TEXT_BYTES = 512 * 1024

#: Extensions that are known to be text; used to avoid decoding binaries.
TEXT_SUFFIXES = {
    ".md", ".markdown", ".rst", ".txt", ".py", ".js", ".mjs", ".cjs", ".ts",
    ".tsx", ".jsx", ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".sh",
    ".ps1", ".bat", ".sql", ".html", ".htm", ".css", ".java", ".go", ".rs",
    ".c", ".h", ".cpp", ".hpp", ".r", ".m", ".jl", ".kt", ".swift", ".php",
    ".rb", ".ipynb", ".csv", ".tex", ".bib", ".gitignore", ".gitattributes",
    ".editorconfig", ".env", ".example", "",
}

README_NAMES = ("readme.md", "readme.markdown", "readme.rst", "readme.txt", "readme")
LICENSE_NAMES = (
    "license",
    "license.md",
    "license.txt",
    "licence",
    "licence.md",
    "licence.txt",
    "copying",
    "copying.txt",
    "unlicense",
)

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}


def decode_bytes(raw: bytes) -> str:
    """Decode file bytes trying the encodings a real repository may use."""
    if raw.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
        raw = raw[3:]
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


@dataclass
class Facts:
    """Immutable-ish snapshot of one repository tree."""

    root: Path
    files: List[str] = field(default_factory=list)
    dirs: List[str] = field(default_factory=list)
    sizes: Dict[str, int] = field(default_factory=dict)
    _text: Dict[str, str] = field(default_factory=dict, repr=False)
    _by_lower: Dict[str, str] = field(default_factory=dict, repr=False)
    _by_name: Dict[str, List[str]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------ build
    @classmethod
    def build(cls, root: "str | Path") -> "Facts":
        """Walk *root* and return the populated snapshot."""
        root_path = Path(root)
        if not root_path.exists():
            raise FileNotFoundError(f"路径不存在: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"不是一个目录: {root_path}")
        root_path = root_path.resolve()

        facts = cls(root=root_path)
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Prune first so os.walk never descends into .git / node_modules.
            dirnames[:] = sorted(
                d for d in dirnames if d.lower() not in SKIP_DIRS and (not d.startswith(".git") or d.lower() == ".github")
            )
            rel_dir = Path(dirpath).relative_to(root_path)
            for name in dirnames:
                facts.dirs.append((rel_dir / name).as_posix())
            for name in sorted(filenames):
                if name.lower() in (".ds_store", "thumbs.db", "desktop.ini"):
                    continue
                path = Path(dirpath) / name
                rel = (rel_dir / name).as_posix()
                try:
                    size = path.stat().st_size
                except OSError:
                    size = -1
                facts.files.append(rel)
                facts.sizes[rel] = size
                lowered = rel.lower()
                facts._by_lower[lowered] = rel
                facts._by_name.setdefault(Path(rel).name.lower(), []).append(rel)
        return facts

    # -------------------------------------------------------------- lookup
    def resolve(self, rel: str) -> Optional[str]:
        """Return the real relative path for *rel*, or ``None`` if absent."""
        key = rel.replace("\\", "/").strip("/").lower()
        if key in self._by_lower:
            return self._by_lower[key]
        if "/" not in key:
            matches = self._by_name.get(key)
            if matches:
                return sorted(matches, key=len)[0]
        return None

    def has(self, rel: str) -> bool:
        return self.resolve(rel) is not None

    def has_any(self, *names: str) -> bool:
        return any(self.has(name) for name in names)

    def has_dir(self, name: str) -> bool:
        target = name.lower().strip("/")
        for directory in self.dirs:
            if directory.lower() == target or Path(directory).name.lower() == target:
                return True
        return False

    def files_named(self, *names: str) -> List[str]:
        """All files whose basename matches any of *names* (any depth)."""
        hits: List[str] = []
        for name in names:
            hits.extend(self._by_name.get(name.lower(), []))
        return sorted(set(hits))

    def glob(self, pattern: str) -> List[str]:
        """Case-insensitive glob over relative paths and basenames."""
        pattern = pattern.lower()
        hits: List[str] = []
        for lowered, rel in self._by_lower.items():
            if fnmatch.fnmatch(lowered, pattern) or fnmatch.fnmatch(Path(lowered).name, pattern):
                hits.append(rel)
        return sorted(hits)

    def files_under(self, directory: str) -> List[str]:
        prefix = directory.lower().strip("/") + "/"
        return [f for f in self.files if f.lower().startswith(prefix)]

    # ------------------------------------------------------------ text access
    def read(self, rel: str) -> Optional[str]:
        """Return decoded text of *rel* (``None`` when missing or too large)."""
        real = self.resolve(rel)
        if real is None:
            return None
        if real in self._text:
            return self._text[real]
        if self.sizes.get(real, 0) > MAX_TEXT_BYTES:
            return None
        try:
            raw = (self.root / real).read_bytes()
        except OSError:
            return None
        text = decode_bytes(raw)
        self._text[real] = text
        return text

    def read_first(self, names: Sequence[str]) -> Tuple[Optional[str], Optional[str]]:
        """First (path, text) pair among *names* that exists."""
        for name in names:
            real = self.resolve(name)
            if real is None:
                continue
            text = self.read(real)
            if text is not None:
                return real, text
        return None, None

    def readme(self) -> Tuple[Optional[str], Optional[str]]:
        return self.read_first(README_NAMES)

    def license(self) -> Tuple[Optional[str], Optional[str]]:
        return self.read_first(LICENSE_NAMES)

    def empty_files(self) -> List[str]:
        return [f for f in self.files if self.sizes.get(f) == 0]

    def images(self) -> List[str]:
        return [f for f in self.files if Path(f).suffix.lower() in _IMAGE_SUFFIXES]

    def search(
        self,
        pattern: str,
        *,
        files: Optional[Iterable[str]] = None,
        flags: int = re.IGNORECASE,
    ) -> List[Tuple[str, int, str]]:
        """Regex search across text files; returns ``(path, lineno, line)``."""
        regex = re.compile(pattern, flags)
        hits: List[Tuple[str, int, str]] = []
        for rel in files if files is not None else self.files:
            suffix = Path(rel).suffix.lower()
            if suffix not in TEXT_SUFFIXES and Path(rel).name.lower() not in (
                "license",
                "makefile",
                "dockerfile",
                "jenkinsfile",
            ):
                continue
            text = self.read(rel)
            if not text:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    hits.append((rel, lineno, line.strip()))
        return hits

    def text_length(self, rel: str) -> int:
        text = self.read(rel)
        return len(text) if text else 0


def looks_like_text(rel: str) -> bool:
    suffix = Path(rel).suffix.lower()
    return suffix in TEXT_SUFFIXES
