import json


def policy_source(rules, name="fixture", disabled_rules=()):
    lines = [
        "schema-version = 1",
        "name = %s" % json.dumps(name),
        'description = "Fixture policy."',
    ]
    if disabled_rules:
        lines.append("disabled-rules = %s" % json.dumps(list(disabled_rules)))
    for rule in rules:
        lines.extend([
            "",
            "[[rules]]",
            "id = %s" % json.dumps(rule["id"]),
            "kind = %s" % json.dumps(rule["kind"]),
            "severity = %s" % json.dumps(rule.get("severity", "warning")),
            "category = %s" % json.dumps(rule.get("category", "fixture")),
            "expression = %s" % json.dumps(rule["expression"]),
            "message = %s" % json.dumps(rule.get("message", "Inspect this surface.")),
        ])
    return "\n".join(lines) + "\n"


def one_rule(**overrides):
    rule = {
        "id": "FX001",
        "kind": "phrase",
        "severity": "warning",
        "category": "fixture",
        "expression": "stock phrase",
        "message": "Inspect this surface.",
    }
    rule.update(overrides)
    return rule
