# Patternwright

Patternwright reports configured prose patterns for human-led editing. It combines a deterministic, standard-library Python linter with an optional Codex editing skill. It does not infer whether a human or machine wrote the text, and it never sends text to a model or network service.

This repository is private and proprietary. It is designed for installation from a local checkout or a private Git repository, not publication to PyPI.

## What it provides

- Literal string, stdin, and explicit UTF-8 file inputs.
- Strict local TOML policies with stable rule IDs.
- Regex, whole-word, and whitespace-normalized phrase rules.
- Exact offsets, lines, columns, excerpts, categories, and severities.
- Versioned JSON for scripts and agent workflows.
- Neutral sentence, punctuation, negation, long-word, and opening measurements.
- Markdown preparation that excludes frontmatter, comments, code, and URLs without shifting source positions.
- No runtime dependencies beyond Python 3.11 or newer.

## Local installation

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

## CLI

Scan a file with the bundled advisory policy:

```sh
patternwright scan draft.md
```

Scan stdin or a literal string:

```sh
printf 'Needless to say, this is pivotal.' | patternwright scan -
patternwright scan --text "It's not complexity but opportunity."
```

Request structured output or display neutral metrics:

```sh
patternwright scan draft.md --format json
patternwright scan draft.md --metrics
```

Add a project policy or use only project rules:

```sh
patternwright scan draft.md --policy project-policy.toml
patternwright scan draft.md --no-default-policy --policy project-policy.toml
patternwright policy check project-policy.toml
```

Bundled findings are warnings, so they do not fail by default. Projects choose enforcement explicitly:

```sh
patternwright scan draft.md --fail-on warning
patternwright scan draft.md --fail-on never
```

Exit codes are `0` for an admitted report, `1` when the selected finding threshold is met, and `2` for policy, usage, decoding, or I/O failure.

## Python API

```python
from patternwright import default_policy, measure, scan

text = "Needless to say, this is pivotal."
findings = scan(text, default_policy(), source="memo.txt")
metrics = measure(text)
```

The stable public boundaries are policy source to `Policy`, text plus `Policy` to immutable findings, and text to neutral metrics. See [the policy format](docs/policy-format.md) for project overlays.

## Editorial boundary

Patternwright distinguishes measurement from judgment:

- The package identifies configured surfaces and reports distributions.
- The companion `patternwright-edit` skill performs a felt read, adjudicates findings, protects legitimate uses, proposes edits, and rescans.
- Neither layer emits an authorship probability or generic quality score.

The bundled policy is deliberately conservative and advisory. Domain vocabulary, factual contrasts, repetition, punctuation, and technical register can all be legitimate. A finding means “inspect this span,” not “a machine wrote this sentence.”

## Security and privacy

Patternwright runs locally and performs no network or model calls. JSON reports include excerpts from the supplied text, so handle them with the same care as the source document.

Policy files are trusted local configuration. Python's standard regular-expression engine has no timeout, so do not run regex policies from untrusted sources.

