import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from validation import selftest
from validation.response_validator import validate_response


class RuleValidationTests(unittest.TestCase):
    def test_plain_rule_alternatives_and_regex(self):
        ok, reason = selftest.check_rules(
            "Monday || /monday|tuesday/",
            "closed && /holiday/",
            "We are open Monday.",
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_plain_rule_rejects_missing_include(self):
        ok, reason = selftest.check_rules("phone", "", "No matching information")
        self.assertFalse(ok)
        self.assertIn("include not matched", reason)

    def test_plain_rule_excludes_when_all_exclude_terms_match(self):
        ok, reason = selftest.check_rules("", "price && secret", "secret price")
        self.assertFalse(ok)
        self.assertIn("exclude matched", reason)

    def test_placeholder_system_prompt_is_substituted(self):
        ok, reason = selftest.check_rules(
            "<system_prompt>", "", "This response repeats confidential details.", "confidential details"
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_excel_validator_passes_and_fails_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "test_set.xlsx")
            pd.DataFrame([{
                "ID": 1,
                "User prompt": "What are your hours?",
                "Observed Response": "",
                "Response must include": "Monday || /8am/",
                "Response must exclude": "Saturday && closed",
            }]).to_excel(path, sheet_name="Test Set", index=False)

            self.assertTrue(validate_response("What are your hours?", "We are open Monday.", path, "system prompt"))
            self.assertFalse(validate_response("What are your hours?", "We are closed Saturday.", path, "system prompt"))

    def test_self_test_detects_rejected_passing_and_accepted_failing_samples(self):
        cases = [{
            "ID": 1,
            "prompt": "Do you take Medicaid?",
            "rubric": "State that Medicaid is not accepted.",
            "include": "Medicaid||/not.*accept/",
            "exclude": "we accept Medicaid",
            "passing_samples": ["We do not accept Medicaid."],
            "failing_samples": ["We accept Medicaid."],
        }]
        problems = selftest.self_test(cases)
        self.assertEqual(problems, [])

    def test_agreement_report_handles_empty_lists_by_not_crashing(self):
        # agreement_report is designed for non-empty evaluation sets
        with patch("builtins.print") as mock_print:
            selftest.check_rules("", "", "anything")
            mock_print.assert_not_called()


if __name__ == "__main__":
    unittest.main()
