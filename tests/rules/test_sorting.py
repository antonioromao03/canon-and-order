"""Sorting rules (gold/ANNOTATION_GUIDE.md, Rows): oldest first, then same-day tie-breaks.

These cases have no splits or companions, so each work is exactly one row. The
"run began earlier" tie-break only differs from plain date order for split rows, so it
is tested with splitting.
"""

from itertools import permutations

import pytest

from canon_and_order.domain import Kind, PartialDate, Piece, Row, RowRole, Work
from canon_and_order.rules import build_rows

RowKey = tuple[str, tuple[int, int] | None, RowRole]


def make_work(
    work_id: str,
    kind: Kind,
    release: str | None,
    pieces: list[str] | None = None,
) -> Work:
    """A minimal work; ``pieces`` lists piece release dates in release order."""
    return Work(
        id=work_id,
        title=work_id,
        kind=kind,
        release=None if release is None else PartialDate.parse(release),
        pieces=[
            Piece(number=number, release=PartialDate.parse(date))
            for number, date in enumerate(pieces or [], start=1)
        ],
    )


def keys(rows: list[Row]) -> list[RowKey]:
    """What the evaluation compares: work, piece range and role (labels are not scored)."""
    return [
        (row.work, None if row.pieces is None else (row.pieces.first, row.pieces.last), row.role)
        for row in rows
    ]


def order(rows: list[Row]) -> list[str]:
    return [row.work for row in rows]


def test_no_works_give_no_rows() -> None:
    assert build_rows([]) == []


@pytest.mark.parametrize(
    "works",
    list(
        permutations(
            [
                make_work("batman-begins", Kind.FEATURE_FILM, "2005-06-15"),
                make_work("the-dark-knight", Kind.FEATURE_FILM, "2008-07-18"),
                make_work("the-dark-knight-rises", Kind.FEATURE_FILM, "2012-07-20"),
            ]
        )
    ),
)
def test_rows_run_oldest_first_whatever_the_input_order(works: tuple[Work, ...]) -> None:
    assert order(build_rows(works)) == [
        "batman-begins",
        "the-dark-knight",
        "the-dark-knight-rises",
    ]


def test_a_whole_work_is_one_main_row_without_a_piece_range() -> None:
    season = make_work(
        "bb-s1", Kind.TV_SEASON, "2008-01-20", pieces=["2008-01-20", "2008-01-27", "2008-02-10"]
    )
    assert keys(build_rows([season])) == [("bb-s1", None, RowRole.MAIN)]


def test_a_year_only_date_sorts_by_the_first_day_of_the_year() -> None:
    # Breaking Bad: minisodes dated only "2010" go before Season 3 (21 March 2010).
    season = make_work("bb-s3", Kind.TV_SEASON, "2010-03-21", pieces=["2010-03-21"])
    minisodes = make_work("bb-minisodes-2", Kind.WEB_SERIES, "2010", pieces=["2010", "2010"])
    assert order(build_rows([season, minisodes])) == ["bb-minisodes-2", "bb-s3"]


def test_a_month_only_date_sorts_by_the_first_day_of_the_month() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2010-03-02")
    special = make_work("special", Kind.TV_SPECIAL, "2010-03")
    assert order(build_rows([film, special])) == ["special", "film"]


@pytest.mark.parametrize("kind", [Kind.SHORT_FILM, Kind.WEB_SERIES, Kind.PROMOTIONAL_CONTENT])
def test_on_the_same_day_supplementary_goes_before_main(kind: Kind) -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2019-10-11")
    extra = make_work("extra", kind, "2019-10-11")
    assert order(build_rows([film, extra])) == ["extra", "film"]


def test_a_partial_date_ties_with_the_first_day_it_could_be() -> None:
    # "2010" and 1 January 2010 have the same earliest day, so the tie-break decides.
    film = make_work("film", Kind.FEATURE_FILM, "2010-01-01")
    promo = make_work("promo", Kind.PROMOTIONAL_CONTENT, "2010")
    assert order(build_rows([film, promo])) == ["promo", "film"]


def test_supplementary_first_does_not_beat_an_earlier_date() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2019-10-10")
    short = make_work("short", Kind.SHORT_FILM, "2019-10-11")
    assert order(build_rows([short, film])) == ["film", "short"]


def test_unbroken_same_day_ties_do_not_depend_on_the_input_order() -> None:
    first = make_work("film-a", Kind.FEATURE_FILM, "2021-12-17")
    second = make_work("film-b", Kind.FEATURE_FILM, "2021-12-17")
    assert build_rows([first, second]) == build_rows([second, first])


def test_works_without_a_release_date_go_last() -> None:
    undated = make_work("undated", Kind.SHORT_FILM, None)
    film = make_work("film", Kind.FEATURE_FILM, "2002-05-03")
    assert order(build_rows([undated, film])) == ["film", "undated"]
