import os
import sys
import tempfile
import unittest

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import main_llm as main


class MainTests(unittest.TestCase):
    def test_write_response_to_existing_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "responses.xlsx")
            pd.DataFrame([
                {"ID": 1, "Observed Response": "", "Valid Response": ""},
                {"ID": 2, "Observed Response": "", "Valid Response": ""},
            ]).to_excel(path, sheet_name="Test Set", index=False)

            main.write_response_to_file(2, "Test response", True, path)
            result = pd.read_excel(path, sheet_name="Test Set")
            row = result.loc[result["ID"] == 2].iloc[0]
            self.assertEqual(row["Observed Response"], "Test response")
            self.assertEqual(row["Valid Response"], "PASS")

    def test_write_response_adds_missing_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "responses.xlsx")
            pd.DataFrame([{"ID": 7, "Prompt": "Question"}]).to_excel(path, sheet_name="Test Set", index=False)

            main.write_response_to_file(7, "Answer", False, path)
            result = pd.read_excel(path, sheet_name="Test Set")
            row = result.iloc[0]
            self.assertEqual(row["Observed Response"], "Answer")
            self.assertEqual(row["Valid Response"], "FAIL")

    def test_write_response_missing_id_column_raises_key_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "responses.xlsx")
            pd.DataFrame([{"Prompt": "Question", "Response": ""}]).to_excel(path, sheet_name="Test Set", index=False)

            with self.assertRaises(KeyError):
                main.write_response_to_file(1, "Answer", True, path)


if __name__ == "__main__":
    unittest.main()
