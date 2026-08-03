# Policy format

A Patternwright policy is strict schema-version 1 TOML. Unknown keys, missing fields, duplicate IDs, invalid expressions, empty expressions, and zero-width matches fail closed.

```toml
schema-version = 1
name = "project-voice"
description = "Project-specific editorial surfaces."

[[rules]]
id = "PV001"
kind = "phrase"
severity = "warning"
category = "metadiscourse"
expression = "it should be noted"
message = "State the fact directly when the announcement adds nothing."

[[rules]]
id = "PV002"
kind = "regex"
severity = "error"
category = "house-style"
expression = '''\bvery\s+unique\b'''
message = "Use 'unique' or name the relevant degree."
```

Every rule requires exactly these fields:

| Field | Contract |
| --- | --- |
| `id` | Unique uppercase identifier matching `[A-Z][A-Z0-9]{1,15}`. |
| `kind` | `regex`, `word`, or `phrase`. |
| `severity` | `warning` or `error`. |
| `category` | Lowercase hyphenated label. |
| `expression` | Nonempty trusted local expression. |
| `message` | Editorial instruction explaining what to inspect. |

## Rule families

`regex` rules use Python `re.IGNORECASE | re.MULTILINE`. They may match across lines only when the expression says so. They may not produce zero-width findings.

`word` rules escape the expression and apply Unicode-aware word boundaries. They match `robust` but not `robustness`. A word expression cannot contain whitespace.

`phrase` rules match case-insensitively, normalize ordinary whitespace, and preserve original source positions. They may span one source newline but never a blank-line paragraph boundary. They do not match inside larger words.

## Composition

The bundled advisory policy loads first unless `--no-default-policy` is present. Every `--policy` file adds rules in command-line order. Rule IDs must remain unique across the complete set. Patternwright rejects duplicate IDs instead of silently overriding a rule.

Use warnings for surfaces that require context. Reserve errors for explicit project law with known escape conditions and protected legitimate examples.

## Trust boundary

Policies are executable matching configuration. The standard-library regex engine cannot time out catastrophic expressions. Review policies before use and never accept arbitrary regex policies from untrusted users.

