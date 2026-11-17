"""Command-line entry point: `resume-match RESUME JOB_POSTING`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .matcher import compare
from .report import render


def _read(path_str: str) -> str:
    if path_str == "-":
        return sys.stdin.read()
    path = Path(path_str)
    if not path.is_file():
        raise SystemExit(f"error: file not found: {path}")
    if path.suffix.lower() in {".pdf", ".docx", ".doc"}:
        raise SystemExit(
            f"error: {path.name} is a {path.suffix} file. Save or copy it as plain text (.txt) first."
        )
    return path.read_text(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-match",
        description="Compare a resume to a job posting and see which skills you're missing.",
    )
    parser.add_argument("resume", help="path to your resume as a .txt or .md file (use - for stdin)")
    parser.add_argument("job", help="path to the job posting as a .txt or .md file")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead")
    parser.add_argument("--top", type=int, default=10, metavar="N", help="how many extra keywords to list (default 10)")
    parser.add_argument("--no-color", action="store_true", help="turn off colored output")
    parser.add_argument("--min-score", type=int, metavar="PCT", help="exit with code 1 if the score is below PCT")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.resume == "-" and args.job == "-":
        raise SystemExit("error: only one of the inputs can come from stdin")

    report = compare(_read(args.resume), _read(args.job), top_keywords=args.top)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        use_color = not args.no_color and sys.stdout.isatty() and "NO_COLOR" not in os.environ
        print(render(report, color=use_color))

    if args.min_score is not None and report.score < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
