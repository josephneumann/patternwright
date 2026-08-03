import unittest

from patternwright import default_policy, parse_policy, scan
from patternwright.preprocess import prepare_markdown

from tests.support import one_rule, policy_source


class ScannerTests(unittest.TestCase):
    def policy(self, rules):
        return parse_policy(policy_source(rules), source_name="fixture.toml")

    def test_regex_word_and_phrase_find_exact_spans(self):
        policy = self.policy([
            one_rule(id="FX001", kind="word", expression="robust"),
            one_rule(id="FX002", kind="phrase", expression="stock phrase"),
            one_rule(id="FX003", kind="regex", expression=r"\bthree\s+things\b"),
        ])
        text = "Robustness is distinct from robust.\nA stock\nphrase. Three things.\n"
        findings = scan(text, policy, source="sample.txt")
        self.assertEqual([finding.rule_id for finding in findings], ["FX001", "FX002", "FX003"])
        self.assertEqual([finding.matched for finding in findings], ["robust", "stock\nphrase", "Three things"])
        self.assertEqual(findings[0].location.line, 1)
        self.assertEqual(findings[0].location.column, 29)
        self.assertEqual(findings[1].location.line, 2)
        self.assertEqual(findings[1].location.end_line, 3)
        self.assertEqual(findings[2].source, "sample.txt")

    def test_phrase_does_not_cross_paragraph_or_word_boundaries(self):
        policy = self.policy([one_rule(expression="stock phrase")])
        text = "xstock phrasey\n\nstock\n\nphrase\n\nStock phrase."
        findings = scan(text, policy)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].matched, "Stock phrase")

    def test_phrase_matching_is_case_insensitive_and_nonoverlapping(self):
        policy = self.policy([one_rule(expression="ha ha")])
        findings = scan("HA ha ha ha", policy)
        self.assertEqual([finding.matched for finding in findings], ["HA ha", "ha ha"])

    def test_crlf_and_final_newline_coordinates_are_stable(self):
        policy = self.policy([one_rule(kind="word", expression="marker")])
        findings = scan("first\r\nmarker\r\n", policy)
        self.assertEqual(findings[0].location.to_dict(), {
            "start": 7,
            "end": 13,
            "line": 2,
            "column": 1,
            "end_line": 2,
            "end_column": 7,
        })

    def test_policy_order_breaks_same_position_ties(self):
        policy = self.policy([
            one_rule(id="FX002", kind="regex", expression="same"),
            one_rule(id="FX001", kind="word", expression="same"),
        ])
        self.assertEqual(
            [finding.rule_id for finding in scan("same", policy)],
            ["FX002", "FX001"],
        )

    def test_empty_input_is_clean(self):
        self.assertEqual(scan("", default_policy()), ())

    def test_default_false_contrast_is_advisory_and_deduplicated(self):
        policy = default_policy()
        factual = scan("The flag is not true but unknown.", policy)
        self.assertEqual(factual, ())
        synthetic = scan("It's not rust but shadow.", policy)
        self.assertEqual(len(synthetic), 1)
        self.assertEqual(synthetic[0].rule_id, "PW002")
        overlap = scan("It's not only rust but shadow.", policy)
        self.assertEqual(len(overlap), 1)
        self.assertEqual(overlap[0].rule_id, "PW001")
        self.assertEqual(overlap[0].severity, "warning")

    def test_markdown_preparation_masks_nonprose_and_preserves_offsets(self):
        raw = (
            "---\ntitle: Delve\n---\n"
            "<!-- a testament to -->\n"
            "%% needless to say %%\n"
            "```text\nIt's not code but prose.\n```\n"
            "Use `delve` and https://example.test/a-testament-to.\n\n"
            "Needless to say, this remains prose.\n"
        )
        prepared = prepare_markdown(raw)
        self.assertEqual(len(prepared), len(raw))
        self.assertEqual(prepared.count("\n"), raw.count("\n"))
        findings = scan(prepared, default_policy())
        self.assertEqual([(finding.rule_id, finding.location.line) for finding in findings], [("PW022", 11)])

    def test_markdown_fence_closers_match_character_and_minimum_length(self):
        raw = (
            "````text\n"
            "Needless to say, hidden.\n"
            "```\n"
            "A tapestry remains hidden.\n"
            "````\n"
            "Visible tapestry.\n"
            "~~~text\n"
            "Needless to say, hidden again.\n"
            "```\n"
            "~~~\n"
        )
        prepared = prepare_markdown(raw)
        findings = scan(prepared, default_policy())
        self.assertEqual(
            [(finding.rule_id, finding.location.line) for finding in findings],
            [("PW011", 6)],
        )

    def test_serialized_match_is_bounded_but_location_remains_exact(self):
        policy = self.policy([
            one_rule(kind="regex", expression=r"(?s).+")
        ])
        text = "x" * 70_000
        finding = scan(text, policy)[0]
        serialized = finding.to_dict()
        self.assertEqual(finding.location.end, len(text))
        self.assertEqual(len(serialized["matched"]), 180)
        self.assertTrue(serialized["matched"].endswith("..."))


if __name__ == "__main__":
    unittest.main()
