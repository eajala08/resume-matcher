"""The core comparison: how well does a resume cover what a job posting asks for?"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .skills import iter_skills
from .text import CASE_SENSITIVE, collapse_whitespace, count_in, keyword_table, normalize_word

REQUIRED_WEIGHT = 1.0
PREFERRED_WEIGHT = 0.5

_BULLET = re.compile(r"^([-*•–·]|\d+[.)])\s+")
_PREFERRED_HEADING = re.compile(r"\b(preferred|nice[- ]to[- ]haves?|bonus|pluses|desired|optional)\b", re.I)
_REQUIRED_HEADING = re.compile(r"\b(required|requirements?|must[- ]haves?|minimum|basic)\b", re.I)
_SECTION_WORDS = re.compile(
    r"\b(qualifications?|responsibilities|about|benefits|perks|what you|who you|skills|duties|compensation|overview)\b",
    re.I,
)
# A single line can also mark itself as optional: "Kubernetes is a plus".
_INLINE_PREFERRED = re.compile(
    r"\b(a plus|nice[- ]to[- ]have|preferred|bonus points?|a bonus|ideally|desirable)\b", re.I
)


@dataclass
class SkillHit:
    name: str
    category: str
    weight: float  # how much this skill counts toward the score
    mentions: int  # times it appears in the job posting
    preferred: bool  # True if the posting only lists it as a nice-to-have


@dataclass
class MatchReport:
    score: int  # 0-100
    matched: list[SkillHit] = field(default_factory=list)
    missing: list[SkillHit] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)

    @property
    def skills_in_posting(self) -> int:
        return len(self.matched) + len(self.missing)

    @property
    def missing_required(self) -> list[SkillHit]:
        return [s for s in self.missing if not s.preferred]

    @property
    def missing_preferred(self) -> list[SkillHit]:
        return [s for s in self.missing if s.preferred]

    def to_dict(self) -> dict:
        def hit(s: SkillHit) -> dict:
            return {
                "skill": s.name,
                "category": s.category,
                "mentions": s.mentions,
                "preferred": s.preferred,
            }

        return {
            "score": self.score,
            "matched": [hit(s) for s in self.matched],
            "missing": [hit(s) for s in self.missing],
            "missing_keywords": self.missing_keywords,
        }


def _heading_kind(line: str) -> str | None:
    """Classify a line as a "preferred" heading, a "required" heading, or not a heading (None).

    Any heading that isn't about nice-to-haves ("Benefits:", "About us")
    counts as "required", which simply ends a preferred section.
    """
    text = line.strip().strip("#*_ ").strip()
    if not text or len(text) > 60 or _BULLET.match(line.strip()):
        return None
    words = text.split()
    names_a_section = bool(
        _PREFERRED_HEADING.search(text) or _REQUIRED_HEADING.search(text) or _SECTION_WORDS.search(text)
    )
    looks_like_heading = (
        line.strip().startswith("#")
        or text.endswith(":")
        or (text.isupper() and (names_a_section or len(words) >= 2))
        or (len(words) <= 6 and not text.endswith(".") and names_a_section)
    )
    if not looks_like_heading:
        return None
    if _PREFERRED_HEADING.search(text) and not _REQUIRED_HEADING.search(text):
        return "preferred"
    return "required"


def split_sections(job_text: str) -> tuple[str, str]:
    """Split a job posting into (required_text, preferred_text).

    Lines under a heading like "Nice to have:" are preferred until the next
    heading. A single line that calls itself optional ("Docker is a plus")
    is preferred on its own. Everything else is required.
    """
    required: list[str] = []
    preferred: list[str] = []
    in_preferred = False
    for line in job_text.splitlines():
        if not line.strip():
            continue
        kind = _heading_kind(line)
        if kind:
            in_preferred = kind == "preferred"
        # Heading lines are kept too, since some carry skills: "Required: Python, SQL".
        if in_preferred or (not kind and _INLINE_PREFERRED.search(line)):
            preferred.append(line)
        else:
            required.append(line)
    return "\n".join(required), "\n".join(preferred)


def find_skills(text: str) -> dict[str, tuple[str, int]]:
    """Return {skill_name: (category, mention_count)} for every known skill in `text`."""
    collapsed = collapse_whitespace(text)
    lowered = collapsed.lower()
    found: dict[str, tuple[str, int]] = {}
    for category, name, aliases in iter_skills():
        count = count_in(collapsed, lowered, aliases)
        if count:
            found[name] = (category, count)
    return found


def compare(resume_text: str, job_text: str, top_keywords: int = 10) -> MatchReport:
    """Compare a resume against a job posting and build a MatchReport.

    Score = weighted share of the job's skills that also appear in the resume.
    Required skills count fully, preferred ones count half, and a skill the
    posting mentions several times counts a bit more (up to 2x).
    """
    required_text, preferred_text = split_sections(job_text)
    required_skills = find_skills(required_text)
    preferred_skills = find_skills(preferred_text)
    resume_skills = find_skills(resume_text)

    hits: list[SkillHit] = []
    for name in set(required_skills) | set(preferred_skills):
        is_required = name in required_skills
        category = (required_skills.get(name) or preferred_skills[name])[0]
        mentions = required_skills.get(name, ("", 0))[1] + preferred_skills.get(name, ("", 0))[1]
        base = REQUIRED_WEIGHT if is_required else PREFERRED_WEIGHT
        weight = base * min(1 + 0.25 * (mentions - 1), 2.0)
        hits.append(SkillHit(name, category, weight, mentions, preferred=not is_required))

    # Most important first: required before preferred, then by weight, then name.
    hits.sort(key=lambda s: (s.preferred, -s.weight, s.name.lower()))
    matched = [s for s in hits if s.name in resume_skills]
    missing = [s for s in hits if s.name not in resume_skills]

    total = sum(s.weight for s in hits)
    score = round(100 * sum(s.weight for s in matched) / total) if total else 0

    return MatchReport(
        score=score,
        matched=matched,
        missing=missing,
        missing_keywords=_missing_keywords(resume_text, job_text, top_keywords),
    )


def _skill_words() -> set[str]:
    """Every individual word used in the skills dictionary, normalized.

    Used to keep skills out of the "other keywords" list, since they are
    already reported in their own sections.
    """
    words: set[str] = set()
    for _, _, aliases in iter_skills():
        for alias in aliases:
            if alias.startswith(CASE_SENSITIVE):
                alias = alias[len(CASE_SENSITIVE):]
            for part in re.split(r"[\s,/]+", alias.lower()):
                words.add(part)
                words.add(normalize_word(part))
    return words


def _missing_keywords(resume_text: str, job_text: str, limit: int) -> list[str]:
    """Words the posting repeats (2+ times) that never appear in the resume.

    These catch things the skills dictionary doesn't know about, like
    "robotics", "payments" or "accessibility".
    """
    if limit <= 0:
        return []
    job_table = keyword_table(job_text)
    resume_words = set(keyword_table(resume_text))
    skill_words = _skill_words()

    candidates = []
    for word, spellings in job_table.items():
        count = sum(spellings.values())
        if count < 2 or word in resume_words or word in skill_words:
            continue
        if any(spelling in skill_words for spelling in spellings):
            continue
        candidates.append((spellings.most_common(1)[0][0], count))

    candidates.sort(key=lambda wc: (-wc[1], wc[0]))
    return [word for word, _ in candidates[:limit]]
