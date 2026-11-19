import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from resume_matcher.matcher import compare
from resume_matcher.web import MAX_BODY_BYTES, STATIC_DIR, Handler

ROOT = Path(__file__).resolve().parent.parent
RESUME = (ROOT / "examples" / "resume.txt").read_text(encoding="utf-8")
JOB = (ROOT / "examples" / "job_posting.txt").read_text(encoding="utf-8")


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, body=None, raw=None, headers=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, headers=headers or {})
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as err:
            return err.code, err.headers, err.read()

    def test_serves_the_page_and_its_assets(self):
        for path, kind in [("/", "text/html"), ("/app.css", "text/css"), ("/app.js", "text/javascript"), ("/favicon.svg", "image/svg+xml")]:
            status, headers, body = self.request(path)
            self.assertEqual(status, 200, path)
            self.assertIn(kind, headers["Content-Type"])
            self.assertTrue(body)
        self.assertIn("default-src 'self'", self.request("/")[1]["Content-Security-Policy"])

    def test_health_check(self):
        status, _, body = self.request("/health")
        self.assertEqual((status, json.loads(body)), (200, {"status": "ok"}))

    def test_unknown_path_is_404(self):
        self.assertEqual(self.request("/nope")[0], 404)
        self.assertEqual(self.request("/../pyproject.toml")[0], 404)

    def test_match_returns_the_same_result_as_the_library(self):
        status, _, body = self.request("/api/match", {"resume": RESUME, "job": JOB})
        self.assertEqual(status, 200)
        result = json.loads(body)
        expected = compare(RESUME, JOB).to_dict()
        for key in ("score", "matched", "missing", "missing_keywords"):
            self.assertEqual(result[key], expected[key])
        self.assertEqual(result["skills_in_posting"], len(expected["matched"]) + len(expected["missing"]))
        self.assertIn(result["tone"], {"green", "yellow", "red"})
        self.assertTrue(result["verdict"])

    def test_match_with_no_skills_in_posting(self):
        status, _, body = self.request("/api/match", {"resume": "Python", "job": "We like hats."})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["skills_in_posting"], 0)

    def test_rejects_bad_input(self):
        cases = [
            ({"raw": b"not json"}, 400),
            ({"body": ["a", "b"]}, 400),
            ({"body": {"resume": "x"}}, 400),
            ({"body": {"resume": 1, "job": "y"}}, 400),
            ({"body": {"resume": "  ", "job": "y"}}, 400),
        ]
        for kwargs, expected in cases:
            status, _, body = self.request("/api/match", **kwargs)
            self.assertEqual(status, expected, kwargs)
            self.assertIn("error", json.loads(body))

    def test_rejects_oversized_body(self):
        big = {"resume": "a" * (MAX_BODY_BYTES + 1), "job": "b"}
        self.assertEqual(self.request("/api/match", big)[0], 413)

    def test_wrong_method_is_405(self):
        self.assertEqual(self.request("/api/match")[0], 405)
        self.assertEqual(self.request("/", body={"a": 1})[0], 405)

    def test_bundled_examples_match_the_repo_examples(self):
        """The page's "Try an example" button must not drift from examples/."""
        self.assertEqual((STATIC_DIR / "example_resume.txt").read_text(encoding="utf-8"), RESUME)
        self.assertEqual((STATIC_DIR / "example_job.txt").read_text(encoding="utf-8"), JOB)


if __name__ == "__main__":
    unittest.main()
