---
name: patternwright-edit
description: Audit or revise prose for formulaic, synthetic, AI-like, or house-style patterns using Patternwright's deterministic evidence plus directed editorial judgment. Use when a user asks to detect AI writing patterns, de-slop text, inspect prose that feels generated, lint one or more text or Markdown files, calibrate a prose-pattern policy, or revise confirmed problems without making an authorship claim.
---

# Patternwright Edit

Use Patternwright as an evidence layer for human-led editing. Report configured textual surfaces, then decide what they mean in context. Never claim that a person or model authored the text, and never turn findings or metrics into an AI probability or quality score.

## Establish the task boundary

1. Determine whether the user authorized an audit only, proposed edits, or direct file edits.
2. Preserve facts, technical terms, quotations, citations, formatting, and intentional voice.
3. Read the nearest governing project instructions and any Patternwright policy files the user or project explicitly names. Do not search outside the project root, auto-discover hidden policy, or invent project law. Report exactly which policy files you pass to Patternwright.
4. If semantic judgment or revision is requested, read [references/editorial-lenses.md](references/editorial-lenses.md) before evaluating the text.

## Inspect before scanning

Read the text once without Patternwright output. Record the precise places where attention, trust, rhythm, meaning, or voice falters. This felt pass remains independent evidence; do not let a rule match manufacture a criticism.

## Run the deterministic pass

Prefer an installed command:

```bash
patternwright scan PATH --format json --metrics
```

For multiple files, pass them in the intended order. For literal text, use `--text`. For piped content, use `-`. Add a project policy with `--policy PATH`; repeat the option when several policies apply. Use `--no-default-policy` only when the project policy is intended to replace the bundled advisory policy.

When working inside the Patternwright repository without an installed command, use:

```bash
PYTHONPATH=src python3 -m patternwright scan PATH --format json --metrics
```

If Patternwright is unavailable, perform the felt and editorial passes manually and state that the deterministic scan was unavailable. Do not simulate matches, counts, or locations.

Treat rule files as trusted code because regular expressions can consume substantial resources. Do not scan untrusted policy files without review.

## Adjudicate every candidate

Classify each deterministic match and each felt-pass concern as one of:

- **Confirmed:** the surface weakens this passage for a stated contextual reason.
- **Intentional:** the named surface is present, but it earns its place through voice, domain meaning, quotation, rhythm, or structure.
- **False positive:** the text match is not actually an instance of the rule's named category in context.

For a confirmed issue, identify the smallest change that repairs the problem and the quality that change must preserve. A replacement should improve a named defect, not merely make the prose different.

Cover every candidate in the internal adjudication. The user-facing report may group overlapping findings that share one editorial cause, but it must preserve every materially distinct ruling.

Metrics describe the sample. Use them to compare passages or revisions, not as universal targets. Never infer authorship, quality, sincerity, or intent from a rate.

## Revise only when authorized

1. Change confirmed problems only.
2. Prefer deletion, specificity, reordered emphasis, or restored causality over synonym swapping.
3. Keep domain language when it is exact, even if it resembles a stock phrase out of context.
4. Do not flatten deliberate repetition, parallelism, cadence, or genre voice.
5. Re-read the revised passage without the findings in view.
6. Rerun with the same policies, input format, and reporting options, then examine both removed and newly introduced matches. For proposal-only work, scan the proposed text with `--text` or stdin instead of changing the source file.

## Report the result

Lead with the editorial conclusion, not a warning count. Include:

1. The scope and policy used.
2. Confirmed problems with exact evidence and reasoning.
3. Intentional uses or false positives that materially affect the result.
4. Edits made or proposed, plus what each preserves.
5. Remaining warnings and why they remain.
6. A clear statement that Patternwright reports configured prose evidence and does not determine authorship.

Do not produce an overall AI score, pass probability, verdict such as “human-written,” or unsupported claim that eliminating warnings makes prose natural.
