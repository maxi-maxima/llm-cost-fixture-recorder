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

    def test_custom_prices_json_prices_new_models(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir, "calls.csv")
            price_path = Path(temp_dir, "prices.json")
            with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["name", "model", "prompt_tokens", "completion_tokens"])
                writer.writeheader()
                writer.writerow({"name": "probe", "model": "future-model", "prompt_tokens": "1000000", "completion_tokens": "500000"})
            price_path.write_text(json.dumps({"future-model": {"input_per_million": "2.00", "output_per_million": "4.00"}}), encoding="utf-8")

            proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', str(csv_path), '--prices-json', str(price_path), '--strict-models', '--json'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["total_usd"], "4.000000")
        self.assertEqual(payload["unknown_models"], [])
        self.assertTrue(payload["calls"][0]["priced"])

    def test_bad_prices_json_returns_configuration_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as price_file:
            price_file.write('{"future-model": {"input_per_million": "oops", "output_per_million": "4"}}')
            price_path = price_file.name
        try:
            proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', 'examples/calls.csv', '--prices-json', price_path], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        finally:
            Path(price_path).unlink(missing_ok=True)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 4)
        self.assertIn("Could not load prices", proc.stdout)

    def test_warn_budget_reports_without_failing(self):
        proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', 'examples/calls.csv', '--warn-budget', '0.01'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Budget warning: 0.038000 > 0.01", proc.stdout)

    def test_warn_budget_is_included_in_json(self):
        proc = subprocess.run(['python', '-m', 'llm_cost_fixture_recorder', 'examples/calls.csv', '--warn-budget', '0.01', '--json'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["warn_budget_usd"], "0.010000")
        self.assertTrue(payload["warn_budget_exceeded"])

if __name__ == "__main__":
    unittest.main()
