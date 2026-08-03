"""Line- and offset-preserving preparation for prose-bearing Markdown."""

from __future__ import annotations

import re


URL = re.compile(r"https?://[^\s)>\]}]+", re.IGNORECASE)
INLINE_CODE = re.compile(r"(`+)([^\n]*?)\1")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
OBSIDIAN_COMMENT = re.compile(r"%%.*?%%", re.DOTALL)


def _blank(text: str) -> str:
    return "".join("\n" if character == "\n" else " " for character in text)


def _sub_blank(pattern: re.Pattern[str], text: str) -> str:
    return pattern.sub(lambda match: _blank(match.group(0)), text)


def _blank_frontmatter(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(_blank(line) for line in lines[:index + 1]) + "".join(
                lines[index + 1:]
            )
    return text


def _blank_fences(text: str) -> str:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    marker: str | None = None
    for line in lines:
        stripped = line.lstrip()
        if marker is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            marker = stripped[:3]
            output.append(_blank(line))
            continue
        if marker is not None:
            output.append(_blank(line))
            if stripped.startswith(marker):
                marker = None
            continue
        output.append(line)
    return "".join(output)


def prepare_markdown(text: str) -> str:
    """Mask non-prose Markdown regions without changing offsets or line count."""
    prepared = _blank_frontmatter(text)
    prepared = _blank_fences(prepared)
    prepared = _sub_blank(HTML_COMMENT, prepared)
    prepared = _sub_blank(OBSIDIAN_COMMENT, prepared)
    prepared = _sub_blank(INLINE_CODE, prepared)
    prepared = _sub_blank(URL, prepared)
    if len(prepared) != len(text):
        raise AssertionError("Markdown preparation changed source length")
    return prepared

