import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CliExampleTest(unittest.TestCase):
    def test_cli_example(self):
        proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', 'examples/calls.csv', '--budget', '0.05'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        code = proc.returncode
        out = proc.stdout
        err = proc.stderr
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertIn("Total: $0.038000", out)

    def test_unknown_models_are_reported_in_json(self):
        with tempfile.NamedTemporaryFile("w", newline="", suffix=".csv", delete=False) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["name", "model", "prompt_tokens", "completion_tokens"])
            writer.writeheader()
            writer.writerow({"name": "probe", "model": "future-model", "prompt_tokens": "100", "completion_tokens": "50"})
            csv_path = csv_file.name
        try:
            proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', csv_path, '--json'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        finally:
            Path(csv_path).unlink(missing_ok=True)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["unknown_models"], ["future-model"])
        self.assertFalse(payload["calls"][0]["priced"])

    def test_strict_models_fails_on_unknown_model(self):
        with tempfile.NamedTemporaryFile("w", newline="", suffix=".csv", delete=False) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["name", "model", "prompt_tokens", "completion_tokens"])
            writer.writeheader()
            writer.writerow({"name": "probe", "model": "future-model", "prompt_tokens": "100", "completion_tokens": "50"})
            csv_path = csv_file.name
        try:
            proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', csv_path, '--strict-models'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        finally:
            Path(csv_path).unlink(missing_ok=True)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("Unknown model prices: future-model", proc.stdout)

if __name__ == "__main__":
    unittest.main()
