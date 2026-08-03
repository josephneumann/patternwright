import unittest

from patternwright import Policy, PolicyError, default_policy, merge_policies, parse_policy

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

    def test_suppression_only_overlay_parses_as_unresolved(self):
        policy = parse_policy(
            policy_source([], disabled_rules=("PW014",)),
            source_name="overlay.toml",
        )
        self.assertEqual(policy.rules, ())
        self.assertEqual(policy.disabled_rules, ("PW014",))
        self.assertFalse(policy.composition_complete)
        self.assertEqual(policy.to_dict()["disabled_rules"], ["PW014"])

    def test_disabled_rule_validation_fails_closed(self):
        valid = policy_source([], disabled_rules=("PW014",))
        cases = (
            valid.replace('disabled-rules = ["PW014"]', 'disabled-rules = "PW014"'),
            valid.replace('disabled-rules = ["PW014"]', 'disabled-rules = [14]'),
            valid.replace("PW014", "pw014"),
            valid.replace('disabled-rules = ["PW014"]', 'disabled-rules = ["PW014", "PW014"]'),
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(PolicyError):
                    parse_policy(source)

    def test_policy_cannot_define_and_disable_the_same_rule(self):
        with self.assertRaisesRegex(PolicyError, "cannot define and disable"):
            parse_policy(
                policy_source([one_rule(id="FX001")], disabled_rules=("FX001",))
            )

    def test_invalid_regex_and_word_whitespace_fail(self):
        with self.assertRaises(PolicyError):
            parse_policy(policy_source([one_rule(kind="regex", expression="[")]))
        with self.assertRaises(PolicyError):
            parse_policy(policy_source([one_rule(kind="word", expression="two words")]))

    def test_zero_width_capable_rules_fail_during_policy_validation(self):
        for expression in (r"a*", r"(?=z)", r"(?:a|)", r"^", r"\b"):
            with self.subTest(expression=expression):
                with self.assertRaises(PolicyError):
                    parse_policy(policy_source([
                        one_rule(kind="regex", expression=expression)
                    ]))

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

    def test_merge_suppresses_only_active_earlier_rules(self):
        base = parse_policy(policy_source([
            one_rule(id="AA001", expression="first"),
            one_rule(id="AA002", expression="second"),
        ]), source_name="base.toml")
        overlay = parse_policy(
            policy_source([], disabled_rules=("AA001",)),
            source_name="overlay.toml",
        )
        merged = merge_policies(base, overlay)
        self.assertEqual([rule.id for rule in merged.rules], ["AA002"])
        self.assertEqual([rule.order for rule in merged.rules], [0])
        self.assertEqual(merged.disabled_rules, ("AA001",))
        self.assertTrue(merged.composition_complete)

    def test_unknown_forward_repeated_and_redefined_suppressions_fail(self):
        base = parse_policy(
            policy_source([one_rule(id="AA001")]), source_name="base.toml"
        )
        suppress = parse_policy(
            policy_source([], disabled_rules=("AA001",)), source_name="off.toml"
        )
        unknown = parse_policy(
            policy_source([], disabled_rules=("ZZ999",)), source_name="unknown.toml"
        )
        later = parse_policy(
            policy_source([one_rule(id="ZZ999")]), source_name="later.toml"
        )
        redefine = parse_policy(
            policy_source([one_rule(id="AA001")]), source_name="again.toml"
        )
        with self.assertRaisesRegex(PolicyError, "no active earlier rule"):
            merge_policies(unknown)
        with self.assertRaisesRegex(PolicyError, "no active earlier rule"):
            merge_policies(unknown, later)
        with self.assertRaisesRegex(PolicyError, "disabled more than once"):
            merge_policies(base, suppress, suppress)
        with self.assertRaisesRegex(PolicyError, "duplicate rule id AA001"):
            merge_policies(base, suppress, redefine)

    def test_nested_merge_matches_flat_merge(self):
        base = parse_policy(policy_source([
            one_rule(id="AA001", expression="first"),
            one_rule(id="AA002", expression="second"),
        ]), source_name="base.toml")
        first = parse_policy(
            policy_source([], disabled_rules=("AA001",)), source_name="first.toml"
        )
        added = parse_policy(
            policy_source([one_rule(id="BB001", expression="third")]),
            source_name="added.toml",
        )
        flat = merge_policies(base, first, added)
        nested = merge_policies(merge_policies(base, first), added)
        self.assertEqual(nested, flat)

    def test_existing_four_argument_policy_constructor_remains_valid(self):
        parsed = parse_policy(policy_source([one_rule()]))
        policy = Policy("manual", "Manual.", parsed.rules, ("manual",))
        self.assertEqual(policy.disabled_rules, ())
        self.assertTrue(policy.composition_complete)

    def test_default_policy_is_advisory_and_identity_stable(self):
        policy = default_policy()
        self.assertEqual(policy.name, "editorial-signals")
        self.assertGreaterEqual(len(policy.rules), 20)
        self.assertEqual(len({rule.id for rule in policy.rules}), len(policy.rules))
        self.assertTrue(all(rule.severity == "warning" for rule in policy.rules))


if __name__ == "__main__":
    unittest.main()
