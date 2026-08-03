"""Unix-like command line interface for explicit text and file inputs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from . import __version__
from .metrics import measure
from .policy import PolicyError, default_policy, load_policy, merge_policies
from .preprocess import prepare_markdown
from .report import combined_report, document_report
from .scanner import scan


class CliError(ValueError):
    pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patternwright",
        description=(
            "Report configured prose patterns without inferring authorship."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan text, stdin, or files")
    scan_parser.add_argument("inputs", nargs="*", metavar="FILE")
    scan_parser.add_argument("--text", help="scan one literal string")
    scan_parser.add_argument(
        "--policy", action="append", default=[], metavar="FILE",
        help="add a policy file; may be repeated",
    )
    scan_parser.add_argument(
        "--no-default-policy", action="store_true",
        help="omit the bundled advisory policy",
    )
    scan_parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="report format",
    )
    scan_parser.add_argument(
        "--input-format", choices=("auto", "plain", "markdown"), default="auto",
        help="input preparation mode",
    )
    scan_parser.add_argument(
        "--fail-on", choices=("error", "warning", "never"), default="error",
        help="finding level that returns exit 1",
    )
    scan_parser.add_argument(
        "--metrics", action="store_true",
        help="print neutral metrics in text reports; JSON always includes them",
    )

    policy_parser = subparsers.add_parser("policy", help="validate policy files")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command", required=True)
    check_parser = policy_subparsers.add_parser("check", help="validate one policy")
    check_parser.add_argument("path")
    check_parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _load_policies(paths: list[str], omit_default: bool):
    policies = [] if omit_default else [default_policy()]
    policies.extend(load_policy(path) for path in paths)
    if not policies:
        raise CliError("no policy selected; provide --policy or omit --no-default-policy")
    return merge_policies(*policies) if len(policies) > 1 else policies[0]


def _validated_utf8(source: str, raw: str) -> str:
    try:
        raw.encode("utf-8")
    except UnicodeError as error:
        raise CliError("%s is not valid UTF-8: %s" % (source, error)) from error
    return raw


def _read_inputs(inputs: list[str], literal: str | None) -> list[tuple[str, str, str]]:
    if literal is not None:
        if inputs:
            raise CliError("--text cannot be combined with file inputs")
        return [("<text>", _validated_utf8("<text>", literal), "plain")]
    selected = inputs or ["-"]
    if selected.count("-") > 1:
        raise CliError("stdin may be selected only once")
    documents = []
    for value in selected:
        if value == "-":
            try:
                raw = sys.stdin.read()
            except (OSError, UnicodeError) as error:
                raise CliError("<stdin>: %s" % error) from error
            documents.append(("<stdin>", _validated_utf8("<stdin>", raw), "plain"))
            continue
        path = Path(value)
        if not path.exists():
            raise CliError("input does not exist: %s" % path)
        if not path.is_file():
            raise CliError("input is not a regular file: %s" % path)
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise CliError("%s: %s" % (path, error)) from error
        inferred = "markdown" if path.suffix.lower() in {".md", ".markdown"} else "plain"
        documents.append((str(path), raw, inferred))
    return documents


def _masked(raw: str, requested: str, inferred: str) -> str:
    mode = inferred if requested == "auto" else requested
    return prepare_markdown(raw) if mode == "markdown" else raw


def _overlaps_mask(finding, raw: str, masked: str) -> bool:
    return any(
        raw[index] != masked[index]
        for index in range(finding.location.start, finding.location.end)
    )


def _raw_finding(finding, raw: str):
    start, end = finding.location.start, finding.location.end
    line_start = raw.rfind("\n", 0, start) + 1
    line_end = raw.find("\n", end)
    if line_end < 0:
        line_end = len(raw)
    return replace(
        finding,
        matched=raw[start:end],
        excerpt=" ".join(raw[line_start:line_end].split())[:180],
    )


def _print_text(report: dict[str, object], show_metrics: bool) -> None:
    for document in report["documents"]:
        for finding in document["findings"]:
            location = finding["location"]
            matched = " ".join(finding["matched"].split())[:80]
            print(
                "%s:%d:%d: [%s %s %s] %s: %r"
                % (
                    document["source"],
                    location["line"],
                    location["column"],
                    finding["severity"].upper(),
                    finding["rule_id"],
                    finding["category"],
                    finding["message"],
                    matched,
                )
            )
        if show_metrics:
            metrics = document["metrics"]
            sentence_words = metrics["sentence_words"]
            rates = metrics["rates_per_1000_words"]
            print(
                "%s: [METRICS] %d words, %d sentences, %.1f mean words/sentence, "
                "%.1f comma-and, %.1f semicolons, %.1f colons, %.1f negations per 1,000"
                % (
                    document["source"], metrics["words"], metrics["sentences"],
                    sentence_words["mean"], rates["comma_and"], rates["semicolons"],
                    rates["colons"], rates["negations"],
                )
            )
    summary = report["summary"]
    print(
        "%d errors, %d warnings, %d documents scanned"
        % (summary["errors"], summary["warnings"], summary["documents"])
    )


def _scan_command(args) -> int:
    policy = _load_policies(args.policy, args.no_default_policy)
    inputs = _read_inputs(args.inputs, args.text)
    documents = []
    for source, raw, inferred in inputs:
        masked = _masked(raw, args.input_format, inferred)
        findings = tuple(
            _raw_finding(finding, raw)
            for finding in scan(masked, policy, source=source)
            if not _overlaps_mask(finding, raw, masked)
        )
        documents.append(document_report(source, raw, findings, measure(masked)))
    report = combined_report(policy, documents)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        _print_text(report, args.metrics)
    summary = report["summary"]
    if args.fail_on == "never":
        return 0
    if args.fail_on == "warning":
        return 1 if summary["errors"] or summary["warnings"] else 0
    return 1 if summary["errors"] else 0


def _policy_command(args) -> int:
    policy = load_policy(args.path)
    if args.format == "json":
        print(json.dumps(policy.to_dict(), ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("Policy %s is valid: %d rules." % (policy.name, len(policy.rules)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "scan":
            return _scan_command(args)
        return _policy_command(args)
    except (CliError, PolicyError) as error:
        print("patternwright: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
