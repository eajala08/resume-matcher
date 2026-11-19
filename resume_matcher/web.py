"""A small web front end: `resume-match-web` serves one page and a JSON API.

Standard library only, like the rest of the project. Nothing is stored: the
text a visitor submits is scored in memory and thrown away.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__
from .matcher import compare
from .report import _verdict

STATIC_DIR = Path(__file__).resolve().parent / "static"

# A resume plus a job posting is a few KB. This is generous, and stops anyone
# from making the server read and score something enormous.
MAX_BODY_BYTES = 300_000

# Only these paths are served, so no request can reach any other file.
_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
    "/example/resume": ("example_resume.txt", "text/plain; charset=utf-8"),
    "/example/job": ("example_job.txt", "text/plain; charset=utf-8"),
}

_SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


class Handler(BaseHTTPRequestHandler):
    server_version = f"resume-match/{__version__}"

    def _send(self, status: int, body: bytes, content_type: str, cache: str = "no-store") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        for name, value in _SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def do_GET(self) -> None:  # noqa: N802 - name required by BaseHTTPRequestHandler
        path = self.path.split("?", 1)[0]
        if path == "/health":
            return self._json(200, {"status": "ok"})
        asset = _ASSETS.get(path)
        if asset is None:
            return self._error(405 if path == "/api/match" else 404, "Method not allowed" if path == "/api/match" else "Not found")
        filename, content_type = asset
        self._send(200, (STATIC_DIR / filename).read_bytes(), content_type, cache="no-cache")

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path != "/api/match":
            known = path in _ASSETS or path == "/health"
            return self._error(405 if known else 404, "Method not allowed" if known else "Not found")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._error(411, "Content-Length is required")
        if length < 0:
            return self._error(400, "Invalid Content-Length")
        if length > MAX_BODY_BYTES:
            # Close instead of reading a body we have already decided to refuse.
            self.close_connection = True
            return self._error(413, "That is too much text. Paste the resume and the posting only.")

        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            return self._error(400, "Request body must be valid JSON")
        if not isinstance(data, dict):
            return self._error(400, "Request body must be a JSON object")

        resume, job = data.get("resume"), data.get("job")
        if not isinstance(resume, str) or not isinstance(job, str):
            return self._error(400, "Send both 'resume' and 'job' as text")
        if not resume.strip() or not job.strip():
            return self._error(400, "Paste both your resume and the job posting")

        report = compare(resume, job)
        verdict, tone = _verdict(report.score)
        self._json(
            200,
            {**report.to_dict(), "skills_in_posting": report.skills_in_posting, "verdict": verdict, "tone": tone},
        )

    def do_PUT(self) -> None:  # noqa: N802
        self._error(405, "Method not allowed")

    do_DELETE = do_PATCH = do_PUT

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Request lines only (method, path, status). Submitted text is never logged.
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-match-web",
        description="Serve the Resume Matcher web page.",
    )
    on_host = "PORT" in os.environ  # hosting platforms set PORT and need 0.0.0.0
    parser.add_argument("--host", default="0.0.0.0" if on_host else "127.0.0.1", help="address to listen on")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="port (default 8000)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as err:
        raise SystemExit(f"error: could not listen on {args.host}:{args.port} ({err.strerror})")
    print(f"Resume Matcher is running at http://{args.host}:{server.server_address[1]}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
