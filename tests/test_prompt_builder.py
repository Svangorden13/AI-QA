import os
import sys
import tempfile
import unittest

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import prompt_builder


class PromptBuilderTests(unittest.TestCase):
    def setUp(self):
        prompt_builder.user_prompts = []

    def tearDown(self):
        prompt_builder.user_prompts = []

    def test_build_system_prompt_contains_clinic_policy(self):
        prompt = prompt_builder.build_system_prompt()
        self.assertIn("Sunrise Family Clinic", prompt)
        self.assertIn("Medicaid", prompt)
        self.assertIn("(555) 010-2200", prompt)

    def test_add_and_select_user_prompt(self):
        prompt_builder.add_user_prompt("One")
        prompt_builder.add_user_prompt("Two")
        self.assertEqual(prompt_builder.build_user_prompt(0), "One")
        self.assertEqual(prompt_builder.build_user_prompt(1), "Two")

    def test_create_user_prompts_adds_defaults(self):
        prompt_builder.create_user_prompts()
        self.assertGreaterEqual(len(prompt_builder.user_prompts), 15)
        self.assertIn("What are your hours?", prompt_builder.user_prompts)

    def test_from_file_returns_ids_prompts_and_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tests.xlsx")
            pd.DataFrame([
                {"ID": 1, "User prompt": "First", "Observed Response": "A"},
                {"ID": 2, "User prompt": "Second", "Observed Response": "B"},
            ]).to_excel(path, sheet_name="Test Set", index=False)

            ids, prompts, responses = prompt_builder.from_file(path, n_prompt=-1)
            self.assertEqual(list(ids), [1, 2])
            self.assertEqual(list(prompts), ["First", "Second"])
            self.assertEqual(list(responses), ["A", "B"])

    def test_from_file_supports_index_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tests.xlsx")
            pd.DataFrame([
                {"ID": 1, "User prompt": "First", "Observed Response": "A"},
                {"ID": 2, "User prompt": "Second", "Observed Response": "B"},
                {"ID": 3, "User prompt": "Third", "Observed Response": "C"},
            ]).to_excel(path, sheet_name="Test Set", index=False)

            ids, prompts, responses = prompt_builder.from_file(path, n_prompt="0-1")
            self.assertEqual(list(ids), [1, 2])
            self.assertEqual(list(prompts), ["First", "Second"])
            self.assertEqual(list(responses), ["A", "B"])


if __name__ == "__main__":
    unittest.main()
