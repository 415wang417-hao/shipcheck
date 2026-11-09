"""Small markdown parsing helpers used by the rule engine.

Only the subset of Markdown that matters for auditing is implemented:
headings, sections, fenced code blocks, list items and a "meaningful first
line" heuristic for taglines.

All queries run against code-stripped text (see :func:`strip_code`) so that a
README which *quotes* Markdown inside example blocks cannot satisfy a check by
accident.
"""

from __future__ import annotations

import re
from typing import Iterable, List, NamedTuple, Optional, Sequence, Tuple

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LIST_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d{1,3}[.)])\s+(?!\[ \])\S")
TASK_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d{1,3}[.)])\s+\[[ xX]\]")

_NOISE_PREFIXES = (
    "#",
    ">",
    "|",
    "![",
    "[![",
    "<",
    "---",
    "***",
    "===",
    "```",
    "~~~",
    ":",
)


class Section(NamedTuple):
    level: int
    title: str
    body: str


def _split_lines(text: str) -> List[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def strip_code(text: str) -> str:
    """Remove fenced code blocks and HTML comments from *text*."""
    out: List[str] = []
    in_fence = False
    in_comment = False
    for line in _split_lines(text):
        if in_comment:
            if "-->" in line:
                in_comment = False
                line = line.split("-->", 1)[1]
            else:
                continue
        if not in_fence and "<!--" in line:
            head, _, tail = line.partition("<!--")
            if "-->" in tail:
                line = head + tail.split("-->", 1)[1]
            else:
                out.append(head)
                in_comment = True
                continue
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def headings(text: str) -> List[Tuple[int, str]]:
    """Return ``(level, title)`` for every ATX heading in *text*."""
    result: List[Tuple[int, str]] = []
    for line in _split_lines(text):
        match = HEADING_RE.match(line)
        if match:
            result.append((len(match.group(1)), match.group(2).strip()))
    return result


def normalize_title(title: str) -> str:
    """Lowercase and drop Markdown decoration so matching is forgiving."""
    lowered = title.lower()
    lowered = re.sub(r"[`*_~\[\]()#>!:\"'“”—\-–.,;:!?]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def find_heading(text: str, keywords: Sequence[str]) -> Optional[str]:
    """Return the first heading containing any of *keywords*."""
    wanted = [normalize_title(k) for k in keywords]
    for _level, title in headings(strip_code(text)):
        normalized = normalize_title(title)
        if any(k and k in normalized for k in wanted):
            return title
    return None


def sections(text: str) -> List[Section]:
    """Split *text* into :class:`Section` chunks (heading plus its body)."""
    result: List[Section] = []
    current: Optional[Tuple[int, str, List[str]]] = None
    for line in _split_lines(strip_code(text)):
        match = HEADING_RE.match(line)
        if match:
            if current is not None:
                result.append(Section(current[0], current[1], "\n".join(current[2])))
            current = (len(match.group(1)), match.group(2).strip(), [])
        elif current is not None:
            current[2].append(line)
    if current is not None:
        result.append(Section(current[0], current[1], "\n".join(current[2])))
    return result


def find_section(text: str, keywords: Sequence[str]) -> Optional[Section]:
    """Return the first section whose heading contains any of *keywords*."""
    wanted = [normalize_title(k) for k in keywords]
    for section in sections(text):
        normalized = normalize_title(section.title)
        if any(k and k in normalized for k in wanted):
            return section
    return None


def fenced_blocks(text: str) -> List[str]:
    """Return the raw content of every fenced code block in *text*."""
    blocks: List[str] = []
    current: Optional[List[str]] = None
    for line in _split_lines(text):
        if FENCE_RE.match(line):
            if current is None:
                current = []
            else:
                blocks.append("\n".join(current))
                current = None
            continue
        if current is not None:
            current.append(line)
    return blocks


def first_meaningful_line(text: str, max_lines: int = 40) -> Optional[str]:
    """First line that plausibly carries the project tagline.

    Skips headings, badges, images, tables, HTML and horizontal rules.  A
    blockquote right after the H1 is accepted, because ``> one-liner`` is a
    common tagline style.
    """
    quoted_fallback: Optional[str] = None
    seen = 0
    for line in _split_lines(text):
        stripped = line.strip()
        if not stripped:
            continue
        seen += 1
        if seen > max_lines:
            break
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("![", "[![")):
            continue
        if quoted_fallback is None and stripped.startswith(">"):
            inner = stripped.lstrip("> ").strip()
            if len(inner) >= 8:
                quoted_fallback = inner
                break
            continue
        if stripped.startswith(_NOISE_PREFIXES):
            continue
        if len(stripped) < 8:
            continue
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", stripped)
        cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
        return cleaned.strip()
    if quoted_fallback:
        cleaned = quoted_fallback.replace("**", "").replace("`", "")
        return cleaned.strip()
    return None


def list_items(text: str, include_tasks: bool = False) -> List[str]:
    """Return Markdown list items found in *text*."""
    items: List[str] = []
    for line in _split_lines(text):
        if TASK_ITEM_RE.match(line):
            if include_tasks:
                items.append(line.strip())
            continue
        if LIST_ITEM_RE.match(line):
            items.append(line.strip())
    return items


def count_nonempty_lines(text: str) -> int:
    return sum(1 for line in _split_lines(text) if line.strip())


def contains_any(text: str, words: Iterable[str]) -> List[str]:
    """Return the subset of *words* that occurs in *text* (case-insensitive)."""
    lowered = text.lower()
    return [word for word in words if word.lower() in lowered]
