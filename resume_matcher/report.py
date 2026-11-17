"""Turn a MatchReport into readable terminal output."""

from __future__ import annotations

from .matcher import MatchReport, SkillHit

_COLORS = {
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


class _Style:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        if not self.enabled or not styles:
            return text
        return "".join(_COLORS[s] for s in styles) + text + _COLORS["reset"]


def _bar(score: int, width: int = 30) -> str:
    filled = round(width * score / 100)
    return "█" * filled + "░" * (width - filled)


def _verdict(score: int) -> tuple[str, str]:
    if score >= 80:
        return "Strong match", "green"
    if score >= 55:
        return "Good match, a few gaps", "yellow"
    return "Big gaps to close", "red"


def _group(hits: list[SkillHit]) -> dict[str, list[SkillHit]]:
    grouped: dict[str, list[SkillHit]] = {}
    for hit in hits:
        grouped.setdefault(hit.category, []).append(hit)
    return grouped


def render(report: MatchReport, color: bool = True) -> str:
    s = _Style(color)
    if report.skills_in_posting == 0:
        return "\n".join(
            [
                "",
                s("  RESUME MATCH", "bold"),
                "  No recognizable skills were found in the job posting, so there is nothing to score.",
                "  Check that the second file is the job posting and that it is plain text.",
                "",
            ]
        )
    verdict, tone = _verdict(report.score)
    lines = [
        "",
        s("  RESUME MATCH", "bold"),
        f"  {s(_bar(report.score), tone)}  {s(str(report.score) + '%', 'bold', tone)}  {verdict}",
        "",
    ]

    if report.missing_required:
        lines.append(s("  Missing — required", "bold", "red"))
        for category, hits in _group(report.missing_required).items():
            names = ", ".join(h.name for h in hits)
            lines.append(f"    {s(category + ':', 'dim')} {names}")
        lines.append("")

    if report.missing_preferred:
        lines.append(s("  Missing — nice to have", "bold", "yellow"))
        for category, hits in _group(report.missing_preferred).items():
            names = ", ".join(h.name for h in hits)
            lines.append(f"    {s(category + ':', 'dim')} {names}")
        lines.append("")

    if report.matched:
        lines.append(s("  Already on your resume", "bold", "green"))
        for category, hits in _group(report.matched).items():
            names = ", ".join(h.name for h in hits)
            lines.append(f"    {s(category + ':', 'dim')} {names}")
        lines.append("")

    if report.missing_keywords:
        lines.append(s("  Other words the posting repeats", "bold"))
        lines.append("    " + ", ".join(report.missing_keywords))
        lines.append("")

    if report.missing_required:
        names = [h.name for h in report.missing_required[:3]]
        top = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]
        lines.append(s("  Tip: ", "bold") + f"if you have experience with {top}, say so in a bullet point.")
        lines.append("")

    return "\n".join(lines)
