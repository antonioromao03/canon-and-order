"""Title normalisation for matching (docs/evaluation.md, Matching).

Two titles that name the same work should normalise to the same string, without making
different works collide. The number guard compares the numbers left after normalisation.
"""

import pytest

from canon_and_order.eval import normalise_title, title_numbers


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        # Case.
        ("THE DARK KNIGHT", "dark knight"),
        # Accents are dropped, but letters outside the Latin alphabet are kept.
        ("Metástasis", "metastasis"),
        ("千と千尋の神隠し", "千と千尋の神隠し"),
        # Apostrophes join the word; other punctuation separates words.
        ("Schindler's List", "schindlers list"),
        ("Schindler\u2019s List", "schindlers list"),  # curly apostrophe
        ("Chicks 'N' Guns", "chicks n guns"),
        ("Batman: Gotham Knight", "batman gotham knight"),
        ("Spider-Man", "spider man"),
        (  # en dash
            "Breaking Bad: Original Minisodes (Minisodes 1\u20135)",
            "breaking bad original minisodes minisodes 1 5",
        ),
        ("  Breaking   Bad  ", "breaking bad"),
    ],
)
def test_case_accents_and_punctuation(title: str, expected: str) -> None:
    assert normalise_title(title) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("The Batman", "batman"),
        ("A Quiet Place", "quiet place"),
        ("An American Tail", "american tail"),
        # Only a leading article goes.
        ("Rise of the Planet of the Apes", "rise of the planet of the apes"),
        # An article that is the whole title stays: dropping it would leave nothing.
        ("The", "the"),
    ],
)
def test_a_leading_article_is_dropped(title: str, expected: str) -> None:
    assert normalise_title(title) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Rocky II", "rocky 2"),
        ("Star Wars: Episode VI", "star wars episode 6"),
        ("Part XXXIX", "part 39"),
        ("Henry V", "henry 5"),
        # Only numerals 1-39 written with I, V and X, in standard form, are converted,
        # so ordinary words made of numeral letters survive.
        ("Mix", "mix"),
        ("DC Showcase", "dc showcase"),
        ("Mild", "mild"),
        ("Part XL", "part xl"),
        ("Part IIII", "part iiii"),
    ],
)
def test_roman_numerals_become_arabic(title: str, expected: str) -> None:
    assert normalise_title(title) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        # A trailing year in brackets disambiguates; it is not part of the title.
        ("Spider-Man (2002)", "spider man"),
        ("Voices from the List (2004)", "voices from the list"),
        # Any other bracketed text is kept: it can be what tells two works apart.
        (
            "Schindler's List (25th anniversary re-release, 2018)",
            "schindlers list 25th anniversary re release 2018",
        ),
        # A year that is part of the title stays.
        ("Blade Runner 2049", "blade runner 2049"),
    ],
)
def test_only_a_trailing_bracketed_year_is_dropped(title: str, expected: str) -> None:
    assert normalise_title(title) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Spider-Man", ()),
        ("Spider-Man 2", (2,)),
        ("Spider-Man (2002)", ()),  # the disambiguating year is not a title number
        ("Rocky II", (2,)),  # Roman numerals count once converted
        ("X2", (2,)),  # digits inside a word count
        ("Alien³", (3,)),  # superscripts are digits after normalisation
        ("Breaking Bad: Original Minisodes (Minisodes 1\u20135)", (1, 5)),  # en dash
        # A multiset, sorted: order does not matter, repeats do.
        ("Breaking Bad (Season 5 - Part 1)", (1, 5)),
        ("Part 1 of Season 5", (1, 5)),
        ("Season 1 - Part 1", (1, 1)),
        ("Agent 007", (7,)),
    ],
)
def test_title_numbers(title: str, expected: tuple[int, ...]) -> None:
    assert title_numbers(title) == expected
