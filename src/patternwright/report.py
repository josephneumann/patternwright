"""Versioned report construction for CLI and downstream agent consumers."""

from __future__ import annotations

import hashlib

from . import __version__
from .metrics import TextMetrics
from .models import Finding, Policy


REPORT_SCHEMA = "patternwright/report/v1"


def document_report(
    source: str,
    raw_text: str,
    findings: tuple[Finding, ...],
    metrics: TextMetrics,
) -> dict[str, object]:
    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)
    return {
        "source": source,
        "sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        "characters": len(raw_text),
        "findings": [finding.to_dict() for finding in findings],
        "counts": {"errors": errors, "warnings": warnings},
        "metrics": metrics.to_dict(),
    }


def combined_report(
    policy: Policy,
    documents: list[dict[str, object]],
) -> dict[str, object]:
    errors = sum(int(document["counts"]["errors"]) for document in documents)
    warnings = sum(int(document["counts"]["warnings"]) for document in documents)
    policy_report: dict[str, object] = {
        "name": policy.name,
        "sources": list(policy.sources),
        "rule_count": len(policy.rules),
    }
    if policy.disabled_rules:
        policy_report["disabled_rules"] = list(policy.disabled_rules)
    return {
        "schema": REPORT_SCHEMA,
        "tool": {"name": "patternwright", "version": __version__},
        "claim": "Configured prose-pattern evidence; no authorship inference.",
        "policy": policy_report,
        "documents": documents,
        "summary": {
            "documents": len(documents),
            "errors": errors,
            "warnings": warnings,
        },
    }
