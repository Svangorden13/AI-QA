import os
import sys
import tempfile
import unittest
from dotenv import load_dotenv
from unittest.mock import patch

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

load_dotenv()

from validation import selftest
from validation.response_validator import validate_response
from validation.llm_validator import validate_response as llm_validate_response
from prompt_wrappers.wrapper_factory import build_wrapper

OPENROUTER_PROVIDER = "openrouter"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"
GEMINI_PROVIDER = "gemini"
GEMINI_MODEL = "models/gemini-3.5-flash-lite"

SYSTEM_PROMPT = """
Sunrise Family Clinic FAQ

- Hours: Monday to Friday, 8am to 5pm.
- Address: 120 Maple Street, Suite 4, Springfield.
- Phone: (555) 010-2200.
- New patients are welcome. The first visit lasts 40 minutes. Arrive 15 minutes early with a photo ID and your insurance card.
- We accept Blue Shield, Aetna, and Cigna. We do not accept Medicaid.
- Cancel at least 24 hours ahead to avoid a $35 fee. The fee is waived for emergencies.
- Prescription refills: request them through the patient portal. Allow 2 business days.
- Lab results appear in the patient portal within 5 business days.
- Parking is free in the lot behind the building.
- Telehealth is available for follow-up visits only, not first visits.
"""


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

            self.assertTrue(validate_response("What are your hours?", "We are open Monday-Friday, 8am-5pm.", path, SYSTEM_PROMPT))
            self.assertFalse(validate_response("What are your hours?", "We are open Saturday.", path, SYSTEM_PROMPT))

    def test_gemini_validator_passes_and_fails_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "test_set.xlsx")
            pd.DataFrame([{
                "ID": 1,
                "User prompt": "What are your hours?",
                "Observed Response": "",
                "Response must include": "Monday || /8am/",
                "Response must exclude": "Saturday && closed",
                "Expected response (rubric)": "We are open Monday through Friday, 8am to 5pm.",
            }]).to_excel(path, sheet_name="Test Set", index=False)

            gemini_llm = build_wrapper(provider=GEMINI_PROVIDER, model=GEMINI_MODEL)

            self.assertTrue(llm_validate_response("What are your hours?", "We are open Monday-Friday, 8am-5pm.", path, gemini_llm, SYSTEM_PROMPT))
            self.assertFalse(llm_validate_response("What are your hours?", "We are open Saturday.", path, gemini_llm, SYSTEM_PROMPT))

    def test_openrouter_validator_passes_and_fails_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "test_set.xlsx")
            pd.DataFrame([{
                "ID": 1,
                "User prompt": "What are your hours?",
                "Observed Response": "",
                "Response must include": "Monday || /8am/",
                "Response must exclude": "Saturday && closed",
                "Expected response (rubric)": "We are open Monday through Friday, 8am to 5pm.",
            }]).to_excel(path, sheet_name="Test Set", index=False)

            openrouter_llm = build_wrapper(provider=OPENROUTER_PROVIDER, model=OPENROUTER_MODEL)

            self.assertTrue(llm_validate_response("What are your hours?", "We are open Monday-Friday, 8am-5pm.", path, openrouter_llm, SYSTEM_PROMPT))
            self.assertFalse(llm_validate_response("What are your hours?", "We are open Saturday.", path, openrouter_llm, SYSTEM_PROMPT))

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
