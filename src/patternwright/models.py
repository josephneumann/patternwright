"""Frozen public records shared by the parser, scanner, and reporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    kind: str
    severity: str
    category: str
    expression: str
    message: str
    source: str
    policy_line: int
    order: int
    _compiled: Any = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "severity": self.severity,
            "category": self.category,
            "expression": self.expression,
            "message": self.message,
            "source": self.source,
            "policy_line": self.policy_line,
        }


@dataclass(frozen=True, slots=True)
class Policy:
    name: str
    description: str
    rules: tuple[Rule, ...]
    sources: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "sources": list(self.sources),
            "rules": [rule.to_dict() for rule in self.rules],
        }


@dataclass(frozen=True, slots=True)
class Location:
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int

    def to_dict(self) -> dict[str, int]:
        return {
            "start": self.start,
            "end": self.end,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }


@dataclass(frozen=True, slots=True)
class Finding:
    source: str
    rule_id: str
    severity: str
    category: str
    message: str
    matched: str
    excerpt: str
    location: Location
    policy_source: str
    policy_line: int

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "matched": self.matched,
            "excerpt": self.excerpt,
            "location": self.location.to_dict(),
            "policy_source": self.policy_source,
            "policy_line": self.policy_line,
        }

