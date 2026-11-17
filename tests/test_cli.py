import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from resume_matcher.cli import main

ROOT = Path(__file__).resolve().parent.parent
RESUME = str(ROOT / "examples" / "resume.txt")
JOB = str(ROOT / "examples" / "job_posting.txt")


def run(*args):
    """Run the CLI in-process and return (exit_code, printed_output)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(list(args))
    return code, out.getvalue()


class CliTests(unittest.TestCase):
    def test_text_report_on_the_bundled_examples(self):
        code, output = run(RESUME, JOB)
        self.assertEqual(code, 0)
        self.assertIn("RESUME MATCH", output)
        self.assertIn("AWS", output)
        self.assertNotIn("\033[", output, "no color codes when output is not a terminal")

    def test_json_output_is_valid_and_complete(self):
        code, output = run(RESUME, JOB, "--json")
        data = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(0 < data["score"] < 100)
        missing = {item["skill"] for item in data["missing"]}
        matched = {item["skill"] for item in data["matched"]}
        self.assertIn("AWS", missing)
        self.assertIn("Kubernetes", missing)
        self.assertIn("Python", matched)
        self.assertIn("ROS", matched)

    def test_min_score_sets_the_exit_code(self):
        self.assertEqual(run(RESUME, JOB, "--min-score", "1")[0], 0)
        self.assertEqual(run(RESUME, JOB, "--min-score", "100")[0], 1)

    def test_top_zero_hides_extra_keywords(self):
        _, output = run(RESUME, JOB, "--json", "--top", "0")
        self.assertEqual(json.loads(output)["missing_keywords"], [])

    def test_missing_file_is_a_clear_error(self):
        with self.assertRaises(SystemExit) as ctx:
            run("no-such-file.txt", JOB)
        self.assertIn("file not found", str(ctx.exception))

    def test_pdf_is_rejected_with_advice(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf:
            with self.assertRaises(SystemExit) as ctx:
                run(pdf.name, JOB)
        self.assertIn("plain text", str(ctx.exception))

    def test_runs_as_a_module(self):
        result = subprocess.run(
            [sys.executable, "-m", "resume_matcher", RESUME, JOB, "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("score", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
