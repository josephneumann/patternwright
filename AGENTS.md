# Patternwright project instructions

- Patternwright reports configured prose patterns. It never infers whether a human or machine wrote text.
- Keep the runtime dependency-free on Python 3.11 and newer. Prefer the standard library throughout.
- Preserve the pure boundaries: policy source to `Policy`, text plus `Policy` to findings, text to neutral metrics.
- Treat findings and measurements as evidence for editorial judgment, never quality verdicts.
- Default policies remain advisory. Project policies may choose blocking severities explicitly.
- Reject ambiguous policies, invalid regular expressions, empty expressions, duplicate rule IDs, and zero-width matches.
- Preserve exact source offsets and deterministic report ordering.
- Treat regular-expression policy files as trusted local configuration. Python's standard `re` engine cannot safely execute hostile expressions.
- Add focused regressions for every bug and every adopted baseline rule. Test protected legitimate uses alongside positive cases.
- Do not add network calls, model calls, authorship scores, hidden configuration discovery, or automatic rewriting to the deterministic package.
- Keep agent-directed analysis in the companion skill, not in the Python package.
- Do not integrate Patternwright into Scribewright or Our Revels without explicit author approval and a compatibility plan.

