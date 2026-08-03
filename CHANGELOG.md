# Changelog

## 0.2.0

- Added strict, ordered `disabled-rules` overlays for suppressing inherited
  rules by stable ID.
- Added fail-closed validation for unknown, future, repeated, self-disabled,
  and redefined rule IDs.
- Added suppression evidence to policy and scan JSON when an overlay is used.
- Added default-aware, multi-policy validation to `patternwright policy check`.
- Preserved existing schema-version 1 policies, four-argument `Policy`
  construction, finding serialization, default findings, and scan ordering.

## 0.1.1

- Relicensed Patternwright under the MIT License for its public source repository.
- Retained the package-index upload guard because Patternwright is not distributed through PyPI.

## 0.1.0

- Added strict local policy parsing and immutable source-span findings.
- Added string, stdin, and explicit-file scanning with text and JSON reports.
- Added conservative advisory defaults and project policy composition.
- Added neutral configurable prose measurements.
- Added offset-preserving Markdown exclusions.
- Added a Codex editing skill with felt-read, adjudication, revision, and rescan stages.
- Added a cross-domain calibration corpus with explicit confirmed and intentional rulings.
- Added controlled UTF-8 failures, complete zero-width validation, bounded report previews, and strict Markdown fence handling.
- Added a package-index upload guard and pinned release build backend.
- Added the initial standard-library regression suite.
