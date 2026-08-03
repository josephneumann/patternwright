import unittest

from patternwright import PolicyError, default_policy, merge_policies, parse_policy
from patternwright.scanner import scan

from tests.support import one_rule, policy_source


class PolicyTests(unittest.TestCase):
    def test_all_rule_families_compile_and_preserve_policy_lines(self):
        source = policy_source([
            one_rule(id="FX001", kind="regex", expression=r"\bnot\b"),
            one_rule(id="FX002", kind="word", expression="robust"),
            one_rule(id="FX003", kind="phrase", expression="stock phrase"),
        ])
        policy = parse_policy(source, source_name="fixture.toml")
        self.assertEqual([rule.kind for rule in policy.rules], ["regex", "word", "phrase"])
        self.assertEqual([rule.policy_line for rule in policy.rules], [5, 13, 21])
        self.assertTrue(all(rule.source == "fixture.toml" for rule in policy.rules))

    def test_unknown_missing_and_invalid_fields_fail_closed(self):
        valid = policy_source([one_rule()])
        cases = (
            valid.replace("schema-version = 1", "schema-version = true"),
            valid.replace('description = "Fixture policy."\n', ""),
            valid.replace('message = "Inspect this surface."', 'extra = "x"'),
            valid.replace('kind = "phrase"', 'kind = "semantic"'),
            valid.replace('severity = "warning"', 'severity = "advisory"'),
            valid.replace('category = "fixture"', 'category = "Bad Category"'),
            valid.replace('id = "FX001"', 'id = "bad.id"'),
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(PolicyError):
                    parse_policy(source)

    def test_empty_policy_and_empty_expressions_fail(self):
        with self.assertRaises(PolicyError):
            parse_policy(
                'schema-version = 1\nname = "x"\ndescription = "x"\n'
            )
        with self.assertRaises(PolicyError):
            parse_policy(policy_source([one_rule(expression=" ")]))

    def test_invalid_regex_and_word_whitespace_fail(self):
        with self.assertRaises(PolicyError):
            parse_policy(policy_source([one_rule(kind="regex", expression="[")]))
        with self.assertRaises(PolicyError):
            parse_policy(policy_source([one_rule(kind="word", expression="two words")]))

    def test_zero_width_rules_fail_at_parse_or_first_match(self):
        with self.assertRaises(PolicyError):
            parse_policy(policy_source([one_rule(kind="regex", expression=r"a*")]))
        policy = parse_policy(
            policy_source([one_rule(kind="regex", expression=r"(?=z)")])
        )
        with self.assertRaises(PolicyError):
            scan("z", policy)

    def test_duplicate_rule_ids_fail_within_and_across_policies(self):
        duplicate = policy_source([one_rule(), one_rule()])
        with self.assertRaises(PolicyError):
            parse_policy(duplicate)
        first = parse_policy(policy_source([one_rule()], name="first"), source_name="a")
        second = parse_policy(policy_source([one_rule()], name="second"), source_name="b")
        with self.assertRaises(PolicyError):
            merge_policies(first, second)

    def test_merge_assigns_global_policy_order(self):
        first = parse_policy(policy_source([one_rule(id="AA001")], name="a"))
        second = parse_policy(policy_source([one_rule(id="BB001")], name="b"))
        merged = merge_policies(first, second)
        self.assertEqual([rule.order for rule in merged.rules], [0, 1])
        self.assertEqual(merged.sources, ("<policy>", "<policy>"))

    def test_default_policy_is_advisory_and_identity_stable(self):
        policy = default_policy()
        self.assertEqual(policy.name, "editorial-signals")
        self.assertGreaterEqual(len(policy.rules), 20)
        self.assertEqual(len({rule.id for rule in policy.rules}), len(policy.rules))
        self.assertTrue(all(rule.severity == "warning" for rule in policy.rules))


if __name__ == "__main__":
    unittest.main()

