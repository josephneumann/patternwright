"""Strict TOML policy parsing and explicit policy composition."""

from __future__ import annotations

import importlib.resources
import re
import tomllib
from dataclasses import replace
from pathlib import Path
from re import _parser as re_parser

from .models import Policy, Rule


SCHEMA_VERSION = 1
KINDS = frozenset({"regex", "word", "phrase"})
SEVERITIES = frozenset({"error", "warning"})
TOP_LEVEL_KEYS = frozenset({
    "schema-version", "name", "description", "disabled-rules", "rules"
})
RULE_KEYS = frozenset({
    "id", "kind", "severity", "category", "expression", "message"
})
RULE_ID = re.compile(r"^[A-Z][A-Z0-9]{1,15}$")
CATEGORY = re.compile(r"^[a-z][a-z0-9-]*$")


class PolicyError(ValueError):
    """A policy is malformed, ambiguous, or unsafe to execute."""


def _rule_lines(source: str) -> list[int]:
    return [
        number for number, line in enumerate(source.splitlines(), 1)
        if line.strip() == "[[rules]]"
    ]


def _require_string(value: object, label: str, source_name: str, line: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyError(
            "%s:%d: %s must be a nonempty string" % (source_name, line, label)
        )
    return value.strip()


def _compile(kind: str, expression: str, source_name: str, line: int):
    try:
        if kind == "regex":
            compiled = re.compile(expression, re.IGNORECASE | re.MULTILINE)
            minimum_width, _maximum_width = re_parser.parse(
                expression, re.IGNORECASE | re.MULTILINE
            ).getwidth()
            if minimum_width == 0:
                raise PolicyError(
                    "%s:%d: regex rules must consume at least one character"
                    % (source_name, line)
                )
        elif kind == "word":
            if any(character.isspace() for character in expression):
                raise PolicyError(
                    "%s:%d: word expressions cannot contain whitespace"
                    % (source_name, line)
                )
            compiled = re.compile(
                r"(?<!\w)" + re.escape(expression) + r"(?!\w)",
                re.IGNORECASE,
            )
        else:
            prefix = r"(?<!\w)" if expression[0].isalnum() else ""
            suffix = r"(?!\w)" if expression[-1].isalnum() else ""
            compiled = re.compile(
                prefix + re.escape(expression) + suffix,
                re.IGNORECASE,
            )
    except re.error as error:
        raise PolicyError(
            "%s:%d: invalid regex: %s" % (source_name, line, error)
        ) from error

    return compiled


def parse_policy(source: str, *, source_name: str = "<policy>") -> Policy:
    """Parse one strict schema-v1 policy from TOML source text."""
    try:
        data = tomllib.loads(source)
    except tomllib.TOMLDecodeError as error:
        raise PolicyError("%s: %s" % (source_name, error)) from error
    if not isinstance(data, dict):
        raise PolicyError("%s: policy root must be a table" % source_name)
    unknown = set(data) - TOP_LEVEL_KEYS
    if unknown:
        raise PolicyError(
            "%s: unknown top-level keys: %s"
            % (source_name, ", ".join(sorted(unknown)))
        )
    if type(data.get("schema-version")) is not int or data.get("schema-version") != SCHEMA_VERSION:
        raise PolicyError(
            "%s: schema-version must be %d" % (source_name, SCHEMA_VERSION)
        )
    name = _require_string(data.get("name"), "name", source_name, 1)
    description = _require_string(
        data.get("description"), "description", source_name, 1
    )
    raw_disabled = data.get("disabled-rules", [])
    if not isinstance(raw_disabled, list):
        raise PolicyError("%s: disabled-rules must be an array" % source_name)
    disabled_rules: list[str] = []
    seen_disabled: set[str] = set()
    for index, value in enumerate(raw_disabled, 1):
        if not isinstance(value, str) or not RULE_ID.fullmatch(value):
            raise PolicyError(
                "%s: disabled-rules item %d must match %s"
                % (source_name, index, RULE_ID.pattern)
            )
        if value in seen_disabled:
            raise PolicyError(
                "%s: duplicate disabled rule id %s" % (source_name, value)
            )
        seen_disabled.add(value)
        disabled_rules.append(value)

    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        raise PolicyError("%s: rules must be an array of tables" % source_name)
    if not raw_rules and not disabled_rules:
        raise PolicyError(
            "%s: policy must contain rules or disabled-rules" % source_name
        )
    lines = _rule_lines(source)
    if len(lines) != len(raw_rules):
        raise PolicyError("%s: could not locate every [[rules]] table" % source_name)

    rules: list[Rule] = []
    seen: set[str] = set()
    for order, (raw, line) in enumerate(zip(raw_rules, lines)):
        if not isinstance(raw, dict):
            raise PolicyError("%s:%d: rule must be a table" % (source_name, line))
        unknown = set(raw) - RULE_KEYS
        missing = RULE_KEYS - set(raw)
        if unknown or missing:
            details = []
            if missing:
                details.append("missing %s" % ", ".join(sorted(missing)))
            if unknown:
                details.append("unknown %s" % ", ".join(sorted(unknown)))
            raise PolicyError("%s:%d: %s" % (source_name, line, "; ".join(details)))
        rule_id = _require_string(raw["id"], "id", source_name, line)
        if not RULE_ID.fullmatch(rule_id):
            raise PolicyError(
                "%s:%d: id must match %s" % (source_name, line, RULE_ID.pattern)
            )
        if rule_id in seen:
            raise PolicyError("%s:%d: duplicate rule id %s" % (source_name, line, rule_id))
        seen.add(rule_id)
        kind = _require_string(raw["kind"], "kind", source_name, line)
        severity = _require_string(raw["severity"], "severity", source_name, line)
        category = _require_string(raw["category"], "category", source_name, line)
        expression = _require_string(raw["expression"], "expression", source_name, line)
        message = _require_string(raw["message"], "message", source_name, line)
        if kind not in KINDS:
            raise PolicyError(
                "%s:%d: kind must be one of %s"
                % (source_name, line, ", ".join(sorted(KINDS)))
            )
        if severity not in SEVERITIES:
            raise PolicyError(
                "%s:%d: severity must be one of %s"
                % (source_name, line, ", ".join(sorted(SEVERITIES)))
            )
        if not CATEGORY.fullmatch(category):
            raise PolicyError(
                "%s:%d: category must match %s"
                % (source_name, line, CATEGORY.pattern)
            )
        if kind == "phrase":
            expression = " ".join(expression.split())
        compiled = _compile(kind, expression, source_name, line)
        rules.append(Rule(
            id=rule_id,
            kind=kind,
            severity=severity,
            category=category,
            expression=expression,
            message=message,
            source=source_name,
            policy_line=line,
            order=order,
            _compiled=compiled,
        ))
    self_disabled = seen & seen_disabled
    if self_disabled:
        raise PolicyError(
            "%s: a policy cannot define and disable the same rule id: %s"
            % (source_name, ", ".join(sorted(self_disabled)))
        )
    return Policy(
        name=name,
        description=description,
        rules=tuple(rules),
        sources=(source_name,),
        disabled_rules=tuple(disabled_rules),
        composition_complete=not disabled_rules,
    )


def load_policy(path: str | Path) -> Policy:
    policy_path = Path(path)
    try:
        source = policy_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise PolicyError("%s: %s" % (policy_path, error)) from error
    return parse_policy(source, source_name=str(policy_path))


def merge_policies(*policies: Policy) -> Policy:
    if not policies:
        raise PolicyError("at least one policy is required")
    rules: list[Rule] = []
    seen: dict[str, str] = {}
    disabled_rules: list[str] = []
    for policy in policies:
        if policy.composition_complete:
            for rule_id in policy.disabled_rules:
                if rule_id in seen:
                    raise PolicyError(
                        "duplicate rule id %s in %s and %s"
                        % (rule_id, seen[rule_id], policy.name)
                    )
                seen[rule_id] = policy.name
                disabled_rules.append(rule_id)
        for rule in policy.rules:
            if rule.id in seen:
                raise PolicyError(
                    "duplicate rule id %s in %s and %s"
                    % (rule.id, seen[rule.id], rule.source)
                )
            seen[rule.id] = rule.source
            rules.append(replace(rule, order=len(rules)))
        if not policy.composition_complete:
            active = {rule.id: index for index, rule in enumerate(rules)}
            for rule_id in policy.disabled_rules:
                if rule_id in disabled_rules:
                    raise PolicyError("rule id %s is disabled more than once" % rule_id)
                if rule_id not in active:
                    raise PolicyError(
                        "disabled rule id %s has no active earlier rule" % rule_id
                    )
                del rules[active[rule_id]]
                rules = [replace(rule, order=index) for index, rule in enumerate(rules)]
                disabled_rules.append(rule_id)
                active = {rule.id: index for index, rule in enumerate(rules)}
    return Policy(
        name=" + ".join(policy.name for policy in policies),
        description="Combined policy set.",
        rules=tuple(rules),
        sources=tuple(source for policy in policies for source in policy.sources),
        disabled_rules=tuple(disabled_rules),
        composition_complete=True,
    )


def default_policy() -> Policy:
    resource = importlib.resources.files("patternwright").joinpath(
        "policies/editorial.toml"
    )
    source = resource.read_text(encoding="utf-8")
    return parse_policy(source, source_name="patternwright:editorial")
