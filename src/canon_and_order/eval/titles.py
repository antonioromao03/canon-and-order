"""Title normalisation for matching predicted works to gold works.

Fuzzy scoring compares words, so first remove differences that never tell two works
apart: case, accents, punctuation, a leading article, Roman versus Arabic numerals, and
a trailing bracketed year such as "(2002)". Bracketed text other than a year is kept,
because it can be the only difference between two works. See docs/evaluation.md
(Matching).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["normalise_title", "title_numbers"]

_TRAILING_YEAR = re.compile(r"\s*\(\d{4}\)\s*$")
# Straight, right and left single quotes, modifier-letter apostrophe, backtick.
_APOSTROPHES = re.compile(r"['\u2019\u2018\u02bc`]")
# Anything that is not a letter, digit or space (\w also matches "_", so list it).
_PUNCTUATION = re.compile(r"[^\w\s]|_")
_DIGITS = re.compile(r"\d+")
_ARTICLES = frozenset({"the", "a", "an"})


def _roman_numerals() -> dict[str, int]:
    """The standard forms of 1-39, the numerals written with I, V and X only.

    Larger numerals need L, C, D or M, which turn ordinary words such as "mix" (1009)
    or "dc" into numbers; titles rarely number past 39.
    """
    tens = ["", "x", "xx", "xxx"]
    ones = ["", "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix"]
    return {t + o: 10 * ti + oi for ti, t in enumerate(tens) for oi, o in enumerate(ones) if t + o}


_ROMAN = _roman_numerals()


def normalise_title(title: str) -> str:
    """Lower-case words separated by single spaces, ready for fuzzy comparison."""
    # NFKD splits an accented letter into the letter plus a combining mark (dropped
    # below) and turns compatibility characters such as "³" into plain ones ("3").
    text = unicodedata.normalize("NFKD", title)
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    text = _TRAILING_YEAR.sub("", text)
    text = _APOSTROPHES.sub("", text)  # "schindler's" -> "schindlers", not "schindler s"
    words = _PUNCTUATION.sub(" ", text).split()
    if len(words) > 1 and words[0] in _ARTICLES:
        words = words[1:]
    return " ".join(str(_ROMAN.get(word, word)) for word in words)


def title_numbers(title: str) -> tuple[int, ...]:
    """The numbers in a title after normalisation, sorted: the number guard compares these.

    "Spider-Man" and "Spider-Man 2" score 100 with token_set_ratio, so two titles may
    match only if their numbers agree. Sorting makes order irrelevant but keeps repeats:
    "Season 1 - Part 1" gives (1, 1), which differs from "Season 1".
    """
    return tuple(sorted(int(digits) for digits in _DIGITS.findall(normalise_title(title))))
