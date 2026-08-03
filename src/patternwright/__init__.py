"""Patternwright: deterministic prose-pattern evidence for human-led editing."""

from .metrics import MetricConfig, TextMetrics, measure
from .models import Finding, Location, Policy, Rule
from .policy import PolicyError, default_policy, load_policy, merge_policies, parse_policy
from .scanner import scan

__all__ = [
    "Finding",
    "Location",
    "MetricConfig",
    "Policy",
    "PolicyError",
    "Rule",
    "TextMetrics",
    "default_policy",
    "load_policy",
    "measure",
    "merge_policies",
    "parse_policy",
    "scan",
]

__version__ = "0.1.0"

