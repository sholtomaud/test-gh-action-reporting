"""Composable helpers for generating GitHub-flavoured Markdown.

Every helper returns a *block*: a string with no trailing newline. Blocks are
joined by :meth:`Document.render` with a blank line between them, which is what
GitHub's Markdown parser expects between structural elements.

Nothing here is GitHub Actions specific -- see :mod:`src.report` for the code
that turns these blocks into a job summary.
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

ALERT_TYPES = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")

ALIGNMENTS = {"left": ":---", "center": ":---:", "right": "---:"}


class Raw(str):
    """A string that is already Markdown/HTML and must not be escaped."""


def escape(value: Any) -> str:
    """Escape an arbitrary value so it is rendered as *data*, not markup.

    Table cells are the dangerous spot: an unescaped ``|`` silently shifts every
    following column, and GitHub renders inline HTML inside cells. Values
    wrapped in :class:`Raw` are passed through untouched.
    """
    if isinstance(value, Raw):
        return str(value)
    text = str(value)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    return text


def heading(text: str, level: int = 1) -> str:
    if not 1 <= level <= 6:
        raise ValueError(f"heading level must be 1-6, got {level}")
    return f"{'#' * level} {text}"


def paragraph(text: str) -> str:
    return " ".join(text.split())


def blockquote(text: str) -> str:
    return "\n".join(f"> {line}".rstrip() for line in text.strip().splitlines())


def alert(kind: str, body: str) -> str:
    """A GitHub alert callout (``> [!NOTE]`` and friends)."""
    kind = kind.upper()
    if kind not in ALERT_TYPES:
        raise ValueError(f"unknown alert type {kind!r}; expected one of {ALERT_TYPES}")
    lines = [f"> [!{kind}]"]
    lines.extend(f"> {line}".rstrip() for line in body.strip().splitlines())
    return "\n".join(lines)


def table(
    headers: Sequence[Any],
    rows: Iterable[Sequence[Any]],
    align: Sequence[str] | None = None,
) -> str:
    headers = list(headers)
    align = list(align or ["left"] * len(headers))
    if len(align) != len(headers):
        raise ValueError("align must have one entry per column")
    lines = [
        "| " + " | ".join(escape(h) for h in headers) + " |",
        "| " + " | ".join(ALIGNMENTS[a] for a in align) + " |",
    ]
    for row in rows:
        cells = list(row)
        if len(cells) != len(headers):
            raise ValueError(f"row has {len(cells)} cells, expected {len(headers)}")
        lines.append("| " + " | ".join(escape(c) for c in cells) + " |")
    return "\n".join(lines)


def key_values(mapping: Mapping[str, Any], headers: Sequence[str] = ("Key", "Value")) -> str:
    return table(headers, mapping.items())


def bullet_list(items: Iterable[Any]) -> str:
    return "\n".join(f"- {item}" for item in items)


def ordered_list(items: Iterable[Any]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def task_list(items: Iterable[tuple[bool, Any]]) -> str:
    return "\n".join(f"- [{'x' if done else ' '}] {text}" for done, text in items)


def code_block(code: str, lang: str = "") -> str:
    """A fenced code block; the fence grows if the body contains backticks."""
    longest = 0
    run = 0
    for char in code:
        run = run + 1 if char == "`" else 0
        longest = max(longest, run)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{lang}\n{code.rstrip()}\n{fence}"


def json_block(payload: Any) -> str:
    return code_block(json.dumps(payload, indent=2, sort_keys=False), "json")


def mermaid(diagram: str) -> str:
    """A Mermaid diagram. GitHub renders these natively in job summaries."""
    return code_block(textwrap.dedent(diagram).strip(), "mermaid")


def math_block(expression: str) -> str:
    return f"$$\n{expression.strip()}\n$$"


def details(summary: str, body: str, *, open: bool = False) -> str:
    tag = "<details open>" if open else "<details>"
    return f"{tag}\n<summary>{summary}</summary>\n\n{body.strip()}\n\n</details>"


def link(text: str, url: str) -> Raw:
    return Raw(f"[{text}]({url})")


def image(alt: str, url: str) -> Raw:
    return Raw(f"![{alt}]({url})")


def badge(label: str, message: str, colour: str = "blue") -> Raw:
    """A shields.io badge -- handy for a status strip at the top of a report."""
    def quote(part: str) -> str:
        # shields.io path syntax: -/_ are doubled, spaces become _, and any
        # remaining "/" must be percent-encoded or it splits the URL path.
        part = part.replace("-", "--").replace("_", "__").replace(" ", "_")
        return part.replace("/", "%2F")

    url = f"https://img.shields.io/badge/{quote(label)}-{quote(message)}-{colour}"
    return image(f"{label}: {message}", url)


def bar(fraction: float, width: int = 24, filled: str = "█", empty: str = "░") -> Raw:
    """A text progress bar. Renders identically everywhere, unlike an <img>."""
    fraction = min(max(fraction, 0.0), 1.0)
    count = round(fraction * width)
    return Raw(f"`{filled * count}{empty * (width - count)}` {fraction:.0%}")


def footnote_ref(name: str) -> Raw:
    return Raw(f"[^{name}]")


def footnotes(notes: Mapping[str, str]) -> str:
    return "\n\n".join(f"[^{name}]: {text}" for name, text in notes.items())


def rule() -> str:
    return "---"


@dataclass
class Document:
    """An ordered collection of Markdown blocks."""

    blocks: list[str] = field(default_factory=list)

    def add(self, *blocks: str) -> "Document":
        self.blocks.extend(b for b in blocks if b)
        return self

    def render(self) -> str:
        return "\n\n".join(block.strip("\n") for block in self.blocks) + "\n"

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.render()
