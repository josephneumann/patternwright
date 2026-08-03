import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from patternwright import cli

from tests.support import one_rule, policy_source


class CliTests(unittest.TestCase):
    def run_cli(self, argv, stdin=""):
        output = io.StringIO()
        errors = io.StringIO()
        prior = sys.stdin
        sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = cli.main(argv)
        finally:
            sys.stdin = prior
        return code, output.getvalue(), errors.getvalue()

    def test_default_warnings_report_but_do_not_fail(self):
        code, output, errors = self.run_cli([
            "scan", "--text", "Needless to say, this is pivotal."
        ])
        self.assertEqual(code, 0)
        self.assertIn("PW022", output)
        self.assertIn("2 warnings", output)
        self.assertEqual(errors, "")

    def test_fail_on_warning_is_explicit(self):
        code, unused_output, unused_errors = self.run_cli([
            "scan", "--text", "Needless to say.", "--fail-on", "warning"
        ])
        self.assertEqual(code, 1)

    def test_custom_error_policy_controls_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "policy.toml"
            policy.write_text(
                policy_source([one_rule(severity="error")]), encoding="utf-8"
            )
            code, output, errors = self.run_cli([
                "scan", "--text", "A stock phrase.", "--no-default-policy",
                "--policy", str(policy),
            ])
        self.assertEqual(code, 1)
        self.assertIn("[ERROR FX001", output)
        self.assertEqual(errors, "")

    def test_stdin_and_json_report_are_versioned(self):
        code, output, errors = self.run_cli(
            ["scan", "-", "--format", "json"], stdin="A tapestry."
        )
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "patternwright/report/v1")
        self.assertEqual(report["documents"][0]["source"], "<stdin>")
        self.assertIn("no authorship inference", report["claim"].lower())
        self.assertNotIn("disabled_rules", report["policy"])
        self.assertEqual(errors, "")

    def test_invalid_utf8_surrogate_on_stdin_is_a_controlled_failure(self):
        code, output, errors = self.run_cli(["scan", "-"], stdin="\udcff")
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("<stdin> is not valid UTF-8", errors)

    def test_markdown_file_masks_nonprose(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.md"
            path.write_text(
                "---\ntitle: Tapestry\n---\n`delve`\n\nPlain sentence.\n",
                encoding="utf-8",
            )
            code, output, errors = self.run_cli(["scan", str(path)])
        self.assertEqual(code, 0)
        self.assertIn("0 warnings", output)
        self.assertEqual(errors, "")

    def test_multiple_files_preserve_input_order(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.txt"
            second = Path(directory) / "second.txt"
            first.write_text("A tapestry.", encoding="utf-8")
            second.write_text("A plethora.", encoding="utf-8")
            code, output, unused_errors = self.run_cli([
                "scan", str(second), str(first), "--format", "json"
            ])
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(
            [Path(document["source"]).name for document in report["documents"]],
            ["second.txt", "first.txt"],
        )

    def test_usage_and_io_failures_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            bad_utf8 = Path(directory) / "bad.txt"
            bad_utf8.write_bytes(b"\xff")
            cases = (
                ["scan", "--text", "text", "file.txt"],
                ["scan", "-", "-"],
                ["scan", directory],
                ["scan", str(Path(directory) / "missing.txt")],
                ["scan", str(bad_utf8)],
                ["scan", "--text", "text", "--no-default-policy"],
            )
            for argv in cases:
                with self.subTest(argv=argv):
                    code, output, errors = self.run_cli(argv)
                    self.assertEqual(code, 2)
                    self.assertEqual(output, "")
                    self.assertIn("patternwright:", errors)

    def test_policy_check_supports_text_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            path.write_text(policy_source([one_rule()]), encoding="utf-8")
            code, output, errors = self.run_cli(["policy", "check", str(path)])
            self.assertEqual(code, 0)
            self.assertIn("1 active rules", output)
            self.assertEqual(errors, "")
            code, output, unused_errors = self.run_cli([
                "policy", "check", str(path), "--format", "json"
            ])
            report = json.loads(output)
            self.assertEqual(report["name"], "fixture")
            self.assertEqual(report["description"], "Fixture policy.")
            self.assertNotIn("disabled_rules", report)

    def test_policy_check_rejects_zero_width_lookahead(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            path.write_text(
                policy_source([
                    one_rule(kind="regex", expression=r"(?=z)")
                ]),
                encoding="utf-8",
            )
            code, output, errors = self.run_cli(["policy", "check", str(path)])
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("must consume at least one character", errors)

    def test_default_rule_can_be_disabled_by_project_overlay(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            path.write_text(
                policy_source([], disabled_rules=("PW014",)), encoding="utf-8"
            )
            code, output, errors = self.run_cli([
                "scan", "--text", "This is pivotal. A tapestry.",
                "--policy", str(path), "--format", "json",
            ])
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(
            [finding["rule_id"] for finding in report["documents"][0]["findings"]],
            ["PW011"],
        )
        self.assertEqual(report["policy"]["disabled_rules"], ["PW014"])
        self.assertEqual(errors, "")

    def test_unresolved_suppression_without_default_exits_two(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            path.write_text(
                policy_source([], disabled_rules=("PW014",)), encoding="utf-8"
            )
            code, output, errors = self.run_cli([
                "scan", "--text", "pivotal", "--no-default-policy",
                "--policy", str(path),
            ])
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("no active earlier rule", errors)

    def test_policy_check_can_validate_overlay_with_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            path.write_text(
                policy_source([], disabled_rules=("PW014",)), encoding="utf-8"
            )
            code, output, errors = self.run_cli([
                "policy", "check", "--with-default-policy", str(path),
                "--format", "json",
            ])
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(report["disabled_rules"], ["PW014"])
        self.assertNotIn("PW014", [rule["id"] for rule in report["rules"]])
        self.assertEqual(errors, "")


if __name__ == "__main__":
    unittest.main()
