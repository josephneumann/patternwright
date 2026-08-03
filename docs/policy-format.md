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

The optional top-level `disabled-rules` array suppresses active rules inherited
from an earlier policy by stable ID:

```toml
schema-version = 1
name = "project-exceptions"
description = "Baseline findings this domain does not use."
disabled-rules = ["PW014"]
```

An overlay may contain only `disabled-rules`; it does not need a dummy rule.
This is rule suppression, not a word allowlist. For example, `PW014` is the
bundled rule that reports `pivotal`, so disabling it allows that configured
surface wherever the overlay is used. A term that no active rule targets is
already allowed. For example, the bundled policy does not target `vital`, so
medical phrases such as `vital signs` need no exception and produce no finding.

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

Composition is ordered. A policy may disable only a currently active rule from
an earlier policy. Unknown IDs, forward references, self-suppression, repeated
suppression, and attempts to redefine a suppressed ID fail closed. Remaining
rules keep their relative order and receive dense effective order values.

Validate a standalone policy or a real default-plus-overlay composition with:

```sh
patternwright policy check project-policy.toml
patternwright policy check --with-default-policy project-exceptions.toml
```

A suppression-only overlay cannot be validated or scanned alone because its
target is unresolved. `Policy.disabled_rules` and JSON reports preserve the
ordered applied IDs as audit evidence. Policies loaded through the Python API
must be passed through `merge_policies` before scanning when they declare
suppressions.

Use warnings for surfaces that require context. Reserve errors for explicit project law with known escape conditions and protected legitimate examples.

## Trust boundary

Policies are executable matching configuration. The standard-library regex engine cannot time out catastrophic expressions. Review policies before use and never accept arbitrary regex policies from untrusted users.
