# Patternwright

Patternwright reports configured prose patterns for human-led editing. It combines a deterministic, standard-library Python linter with an optional Codex editing skill. It does not infer whether a human or machine wrote the text, and it never sends text to a model or network service.

Patternwright is open source under the MIT License. Install it from a local checkout or GitHub. It is intentionally not distributed through PyPI.

## What it provides

- Literal string, stdin, and explicit UTF-8 file inputs.
- Strict local TOML policies with stable rule IDs.
- Ordered project overlays that can suppress inherited rules by stable ID.
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

For another project, install directly from a checkout:

```sh
python3 -m pip install /path/to/patternwright
```

Or install from the public Git repository:

```sh
python3 -m pip install git+https://github.com/josephneumann/patternwright.git
```

No package index is required. The `Private :: Do Not Upload` package classifier is retained specifically to guard against accidental PyPI publication; it does not make the GitHub repository private.

## Companion Codex skill

The companion skill lives at `skills/patternwright-edit`. Install it for personal Codex use by copying that directory into the personal skills directory:

```sh
mkdir -p ~/.codex/skills
cp -R skills/patternwright-edit ~/.codex/skills/
```

Invoke the installed skill as `$patternwright-edit`. It reads prose before scanning, runs Patternwright for exact evidence, adjudicates legitimate uses, and revises only when authorized.

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

Disable a bundled rule for one domain without changing the shared baseline:

```toml
schema-version = 1
name = "domain-exceptions"
description = "Baseline findings this domain intentionally permits."
disabled-rules = ["PW014"]
```

```sh
patternwright policy check --with-default-policy domain-exceptions.toml
patternwright scan draft.md --policy domain-exceptions.toml
```

Suppression is deliberately rule-level rather than a global vocabulary
allowlist. Terms that no active rule targets are already allowed. Invalid,
unknown, future, repeated, or redefined IDs fail instead of silently changing
the scan. The baseline does not target `vital`, so expected medical vocabulary
such as `vital signs` is clean without an exception.

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

`scan()` treats its input as plain text. Use the shared Markdown path when a
document may contain frontmatter, comments, code, or URLs:

```python
from patternwright import default_policy, scan_markdown

markdown = "Use `pivotal` in code, not as prose."
findings = scan_markdown(markdown, default_policy(), source="memo.md")
```

`scan_markdown()` preserves raw source offsets and finding text, masks non-prose
regions, and rejects matches that would bridge masked content. The CLI uses the
same function for Markdown files and `--input-format markdown`.

For composed policies, load each source and resolve it explicitly:

```python
from patternwright import default_policy, load_policy, merge_policies, scan

policy = merge_policies(default_policy(), load_policy("domain-exceptions.toml"))
findings = scan(text, policy, source="memo.txt")
```

The stable public boundaries are policy source to `Policy`, text plus `Policy` to immutable findings, and text to neutral metrics. See [the policy format](docs/policy-format.md) for project overlays.

## Editorial boundary

Patternwright distinguishes measurement from judgment:

- The package identifies configured surfaces and reports distributions.
- The companion `patternwright-edit` skill performs a felt read, adjudicates findings, protects legitimate uses, proposes edits, and rescans.
- Neither layer emits an authorship probability or generic quality score.

The bundled policy is deliberately conservative and advisory. Domain vocabulary, factual contrasts, repetition, punctuation, and technical register can all be legitimate. A finding means “inspect this span,” not “a machine wrote this sentence.”

## Security and privacy

Patternwright runs locally and performs no network or model calls. JSON reports include excerpts, bounded match previews, and supplied source and policy paths, so handle them with the same care as the source document. Exact offsets identify the full source span even when a match preview is truncated.

Policy files are trusted local configuration. Python's standard regular-expression engine has no timeout, so do not run regex policies from untrusted sources.

## Development verification

The regression suite uses only the standard library:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The cross-domain calibration corpus in `tests/fixtures` covers clean fiction, technical documentation, scientific reporting, legal language, quoted rhetoric, and deliberately formulaic promotional prose. Expected matches include explicit editorial rulings so a legitimate phrase cannot silently become a conviction.
