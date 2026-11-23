import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import test_generator


class TestGeneratorTests(unittest.TestCase):
    def test_parse_llm_json_strips_markdown_and_parses_list(self):
        raw = '```json\n[{"ID": 1, "User prompt": "Hours?"}]\n```'
        self.assertEqual(test_generator.parse_llm_json(raw), [{"ID": 1, "User prompt": "Hours?"}])

    def test_parse_llm_json_repairs_single_regex_backslashes(self):
        raw = '[{"pattern": "/\\d{1,3}/"}]'
        parsed = test_generator.parse_llm_json(raw)
        self.assertEqual(parsed, [{"pattern": r"/\d{1,3}/"}])

    def test_clean_regex_flags_removes_case_flags(self):
        cleaned = test_generator.clean_regex_flags("/open/i, /hours/gi")
        self.assertEqual(cleaned, "/open/, /hours/")

    def test_generate_test_case_prompts_calls_llm_and_saves_json(self):
        response = {"text": '[{"ID": 1, "User prompt": "Hours?", "Expected response (rubric)": "Call."}]'}
        model = MagicMock()
        model.prompt.return_value = response

        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "pass1.json")
            cases = test_generator.generate_test_case_prompts("Clinic FAQ", model, output)

            model.prompt.assert_called_once()
            call_args = model.prompt.call_args
            self.assertIn("Clinic FAQ", call_args.args[0])
            self.assertEqual(call_args.kwargs["temperature"], 0.2)
            self.assertEqual(call_args.kwargs["response_mime_type"], "application/json")
            self.assertEqual(cases[0]["ID"], 1)
            self.assertTrue(os.path.exists(output))

    def test_generate_validation_rules_passes_cases_to_llm(self):
        response = {"text": '[{"ID": 1, "Response must include": "Monday", "Response must exclude": "", "Passing samples": ["Monday"], "Failing samples": ["Sunday"]}]'}
        model = MagicMock()
        model.prompt.return_value = response

        rules = test_generator.generate_validation_rules(
            "Clinic FAQ",
            [{"ID": 1}],
            model,
            os.devnull,
        )

        model.prompt.assert_called_once()
        call_args = model.prompt.call_args
        self.assertIn("Clinic FAQ", call_args.args[0])
        self.assertIn('"ID": 1', call_args.args[0])
        self.assertEqual(call_args.kwargs["temperature"], 0.2)
        self.assertEqual(call_args.kwargs["response_mime_type"], "application/json")
        self.assertEqual(rules[0]["ID"], 1)

    def test_generate_client_test_set_requires_source_document(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = os.path.join(directory, "missing.txt")
            output = os.path.join(directory, "output.xlsx")
            model = MagicMock()
            with self.assertRaises(FileNotFoundError):
                test_generator.generate_client_test_set(missing, output, model)


if __name__ == "__main__":
    unittest.main()
