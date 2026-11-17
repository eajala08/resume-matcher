"""Small text-processing helpers: cleaning, tokenizing, and phrase matching."""

from __future__ import annotations

import re
from collections import Counter

# An alias written as "cs:REST" must match with exactly that capitalization.
CASE_SENSITIVE = "cs:"

STOPWORDS = frozenset(
    """
    a about above across after again against all also am an and any are as at
    be because been before being below between both but by can could did do does
    doing down during each etc few for from further had has have having he her
    here hers him his how i if in into is it its itself just like may me more
    most must my no nor not now of off on once only or other our ours out over
    own per same she should so some such than that the their them then there
    these they this those through to too under until up upon us very was we
    were what when where which while who whom why will with within without would
    you your yours e.g i.e

    ability able applicants apply based bonus candidate candidates company
    currently day degree employer ensure environment equal equivalent experience
    familiarity get help including job join knowledge least looking make need
    new nice one opportunity plus position preferred proficiency provide
    pursuing qualifications related required requirements responsibilities role
    skills strong support team three two understanding use used using want well
    work working year years
    """.split()
)

_WORD_RE = re.compile(r"[a-z][a-z0-9+#.\-]*[a-z0-9+#]|[a-z]")

# Custom "word boundaries" so symbols count as part of a term: "c++" is found
# in "c++ and java", "java" is not found inside "javascript", and "js" is not
# found inside "node.js".
_BEFORE = r"(?<![A-Za-z0-9+#.])"
_AFTER = r"(?![A-Za-z0-9+#]|\.[A-Za-z])"


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: str) -> str:
    """Lowercase text and collapse whitespace so matching is predictable."""
    return collapse_whitespace(text).lower()


def normalize_word(word: str) -> str:
    """Reduce simple plurals so "APIs" matches "API" and "libraries" matches "library"."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "sis", "us")):
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    """Split text into lowercase words, keeping tech spellings like c++ and node.js intact."""
    return _WORD_RE.findall(normalize_text(text))


def keyword_table(text: str) -> dict[str, Counter]:
    """Group meaningful words by their normalized form.

    Returns {normalized_word: Counter of the spellings actually used}, e.g.
    {"system": Counter({"systems": 3, "system": 1})}. Stopwords and very
    short words are dropped.
    """
    table: dict[str, Counter] = {}
    for token in tokenize(text):
        word = normalize_word(token)
        if len(word) < 3 or word in STOPWORDS or token in STOPWORDS:
            continue
        table.setdefault(word, Counter())[token] += 1
    return table


def find_spans(text: str, phrase: str) -> list[tuple[int, int]]:
    """Return the (start, end) position of every whole-term match of `phrase` in `text`."""
    pattern = _BEFORE + re.escape(phrase) + _AFTER
    return [m.span() for m in re.finditer(pattern, text)]


def count_in(collapsed: str, lowered: str, aliases: list[str]) -> int:
    """Count mentions of a skill given all the ways it can be written.

    Overlapping matches are merged, so "REST API" counts once even though it
    matches both the "REST" and "rest api" aliases.
    """
    spans: list[tuple[int, int]] = []
    for alias in aliases:
        if alias.startswith(CASE_SENSITIVE):
            spans.extend(find_spans(collapsed, alias[len(CASE_SENSITIVE):]))
        else:
            spans.extend(find_spans(lowered, alias))
    spans.sort()

    count, end = 0, -1
    for start, stop in spans:
        if start >= end:
            count += 1
        end = max(end, stop)
    return count


def count_mentions(text: str, aliases: list[str]) -> int:
    """Convenience wrapper around `count_in` for a single piece of raw text."""
    collapsed = collapse_whitespace(text)
    return count_in(collapsed, collapsed.lower(), aliases)
