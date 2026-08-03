import json
import unittest
from pathlib import Path

from patternwright import default_policy, scan_markdown


FIXTURES = Path(__file__).parent / "fixtures"


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
        cls.policy = default_policy()

    def test_cross_domain_fixture_findings_are_stable(self):
        for name, expected in self.expected.items():
            with self.subTest(name=name):
                raw = (FIXTURES / name).read_text(encoding="utf-8")
                findings = scan_markdown(raw, self.policy, source=name)
                actual = [
                    {
                        "rule_id": finding.rule_id,
                        "line": finding.location.line,
                        "column": finding.location.column,
                        "matched": raw[finding.location.start:finding.location.end],
                        "ruling": item["ruling"],
                    }
                    for finding, item in zip(findings, expected, strict=True)
                ]
                self.assertEqual(actual, expected)

    def test_baseline_policy_is_advisory(self):
        self.assertTrue(self.policy.rules)
        self.assertEqual({rule.severity for rule in self.policy.rules}, {"warning"})

    def test_calibration_records_clean_and_defended_uses(self):
        self.assertEqual(self.expected["fiction.md"], [])
        self.assertEqual(self.expected["technical.md"], [])
        self.assertEqual(self.expected["science.md"], [])
        self.assertEqual(self.expected["legal-policy.md"][0]["ruling"], "intentional")
        self.assertEqual(
            self.expected["journalism-memoir.md"][0]["ruling"], "intentional"
        )

    def test_dense_fixture_exercises_multiple_rule_families(self):
        findings = self.expected["promotional-aiish.md"]
        self.assertGreaterEqual(len(findings), 20)
        self.assertEqual({item["ruling"] for item in findings}, {"confirmed"})
        self.assertGreaterEqual(len({item["rule_id"] for item in findings}), 15)


if __name__ == "__main__":
    unittest.main()
