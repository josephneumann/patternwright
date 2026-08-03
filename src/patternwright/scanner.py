"""Pure deterministic matching over supplied text and policy records."""

from __future__ import annotations

from dataclasses import replace

from .models import Finding, Location, Policy, Rule
from .policy import PolicyError
from .preprocess import prepare_markdown


def _location(text: str, start: int, end: int) -> Location:
    line = text.count("\n", 0, start) + 1
    line_start = text.rfind("\n", 0, start) + 1
    end_line = text.count("\n", 0, end) + 1
    end_line_start = text.rfind("\n", 0, end) + 1
    return Location(
        start=start,
        end=end,
        line=line,
        column=start - line_start + 1,
        end_line=end_line,
        end_column=end - end_line_start + 1,
    )


def _excerpt(text: str, start: int, end: int, radius: int = 60) -> str:
    before = max(0, start - radius)
    after = min(len(text), end + radius)
    excerpt = " ".join(text[before:after].split())
    return excerpt[:180]


def _normalized_with_offsets(text: str) -> tuple[str, list[int]]:
    characters: list[str] = []
    offsets: list[int] = []
    index = 0
    while index < len(text):
        if not text[index].isspace():
            characters.append(text[index])
            offsets.append(index)
            index += 1
            continue
        start = index
        newlines = 0
        while index < len(text) and text[index].isspace():
            if text[index] == "\n":
                newlines += 1
            index += 1
        characters.append("\0" if newlines >= 2 else " ")
        offsets.append(start)
    return "".join(characters), offsets


def _finding(text: str, source: str, rule: Rule, start: int, end: int) -> Finding:
    return Finding(
        source=source,
        rule_id=rule.id,
        severity=rule.severity,
        category=rule.category,
        message=rule.message,
        matched=text[start:end],
        excerpt=_excerpt(text, start, end),
        location=_location(text, start, end),
        policy_source=rule.source,
        policy_line=rule.policy_line,
    )


def scan(text: str, policy: Policy, *, source: str = "<text>") -> tuple[Finding, ...]:
    """Return deterministic, position-bearing findings for one text string."""
    if not policy.composition_complete:
        raise PolicyError(
            "policy has unresolved disabled-rules; compose it with merge_policies"
        )
    overlap = set(policy.disabled_rules) & {rule.id for rule in policy.rules}
    if overlap:
        raise PolicyError(
            "policy contains active disabled rule ids: %s"
            % ", ".join(sorted(overlap))
        )
    findings: list[tuple[int, int, Finding]] = []
    normalized: str | None = None
    offsets: list[int] | None = None
    for rule in policy.rules:
        if rule.kind in {"regex", "word"}:
            for match in rule._compiled.finditer(text):
                if match.start() == match.end():
                    raise PolicyError(
                        "%s:%d: rule %s produced a zero-width match"
                        % (rule.source, rule.policy_line, rule.id)
                    )
                finding = _finding(text, source, rule, match.start(), match.end())
                findings.append((match.start(), rule.order, finding))
            continue
        if normalized is None or offsets is None:
            normalized, offsets = _normalized_with_offsets(text)
        for match in rule._compiled.finditer(normalized):
            start = offsets[match.start()]
            end = offsets[match.end() - 1] + 1
            finding = _finding(text, source, rule, start, end)
            findings.append((start, rule.order, finding))
    findings.sort(key=lambda item: (item[0], item[1], item[2].location.end))
    return tuple(item[2] for item in findings)


def _overlaps_mask(finding: Finding, raw: str, prepared: str) -> bool:
    return any(
        raw[index] != prepared[index]
        for index in range(finding.location.start, finding.location.end)
    )


def _restore_raw_finding(finding: Finding, raw: str) -> Finding:
    start, end = finding.location.start, finding.location.end
    line_start = raw.rfind("\n", 0, start) + 1
    line_end = raw.find("\n", end)
    if line_end < 0:
        line_end = len(raw)
    return replace(
        finding,
        matched=raw[start:end],
        excerpt=" ".join(raw[line_start:line_end].split())[:180],
    )


def scan_markdown(
    text: str, policy: Policy, *, source: str = "<text>"
) -> tuple[Finding, ...]:
    """Scan Markdown prose while excluding masked syntax and non-prose regions."""
    prepared = prepare_markdown(text)
    return tuple(
        _restore_raw_finding(finding, text)
        for finding in scan(prepared, policy, source=source)
        if not _overlaps_mask(finding, text, prepared)
    )
