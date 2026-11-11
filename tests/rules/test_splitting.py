"""Splitting rules (gold/ANNOTATION_GUIDE.md, Rows).

A single release (no pieces, or every piece out on the same exact day) that comes out
while a multi-piece work is still releasing splits that work at its date: pieces up to
that day stay in the first row, later pieces form a new row after the single release.
Supplementary content never splits a TV season or miniseries, and two multi-piece works
never split each other.

"Still releasing" means the work's first piece came out before the split day and a later
piece comes out after it. Pieces released on the split day itself stay in the first row:
that is what the same-day tie-breaks give (the work's run began earlier, and a
supplementary work goes first anyway), and the Dark Knight gold annotates it that way.

Every work here has no parent; how companion rows split with their season is tested with
companions.
"""

import pytest
from builders import keys, make_work, order

from canon_and_order.domain import Canon, Channel, Kind, RowRole, Work
from canon_and_order.rules import build_rows

MAIN = RowRole.MAIN

# A weekly season: four episodes, 1 to 22 January 2020.
SEASON_DATES: list[str | None] = ["2020-01-01", "2020-01-08", "2020-01-15", "2020-01-22"]


def season(work_id: str = "show-s1", kind: Kind = Kind.TV_SEASON) -> Work:
    return make_work(work_id, kind, "2020-01-01", pieces=SEASON_DATES)


def test_dark_knight_gotham_tonight_splits_around_gotham_knight() -> None:
    # The Dark Knight dev gold, dates as annotated. A semi-canon home-video film still
    # splits; The Dark Knight comes after the last episode, so it splits nothing.
    works = [
        make_work("batman-begins", Kind.FEATURE_FILM, "2005-06-15"),
        make_work(
            "gotham-tonight",
            Kind.PROMOTIONAL_CONTENT,
            "2008-06-13",
            pieces=[
                "2008-06-13",
                "2008-06-23",
                "2008-06-26",
                "2008-06-26",
                "2008-07-05",
                "2008-07-10",
            ],
        ),
        make_work("batman-gotham-knight", Kind.FEATURE_FILM, "2008-07-08").model_copy(
            update={"canon": Canon.SEMI_CANON, "channel": Channel.HOME_VIDEO}
        ),
        make_work("the-dark-knight", Kind.FEATURE_FILM, "2008-07-18"),
        make_work("the-dark-knight-rises", Kind.FEATURE_FILM, "2012-07-20"),
    ]
    assert keys(build_rows(works)) == [
        ("batman-begins", None, MAIN),
        ("gotham-tonight", (1, 5), MAIN),
        ("batman-gotham-knight", None, MAIN),
        ("gotham-tonight", (6, 6), MAIN),
        ("the-dark-knight", None, MAIN),
        ("the-dark-knight-rises", None, MAIN),
    ]


def test_a_film_during_a_season_splits_it() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    assert keys(build_rows([season(), film])) == [
        ("show-s1", (1, 2), MAIN),
        ("film", None, MAIN),
        ("show-s1", (3, 4), MAIN),
    ]


def test_a_work_splits_at_every_single_release() -> None:
    first = make_work("film-a", Kind.FEATURE_FILM, "2020-01-03")
    second = make_work("film-b", Kind.FEATURE_FILM, "2020-01-17")
    assert keys(build_rows([season(), first, second])) == [
        ("show-s1", (1, 1), MAIN),
        ("film-a", None, MAIN),
        ("show-s1", (2, 3), MAIN),
        ("film-b", None, MAIN),
        ("show-s1", (4, 4), MAIN),
    ]


def test_a_work_splits_however_short_the_gap() -> None:
    daily = make_work(
        "daily", Kind.TV_SEASON, "2020-01-01", pieces=["2020-01-01", "2020-01-02", "2020-01-04"]
    )
    special = make_work("special", Kind.TV_SPECIAL, "2020-01-03")
    assert keys(build_rows([daily, special])) == [
        ("daily", (1, 2), MAIN),
        ("special", None, MAIN),
        ("daily", (3, 3), MAIN),
    ]


def test_single_releases_on_the_same_day_make_one_split() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    special = make_work("special", Kind.TV_SPECIAL, "2020-01-10")
    rows = keys(build_rows([season(), film, special]))
    # The order of the two same-day releases is the id fallback, not a spec rule.
    assert rows[0] == ("show-s1", (1, 2), MAIN)
    assert set(rows[1:3]) == {("film", None, MAIN), ("special", None, MAIN)}
    assert rows[3:] == [("show-s1", (3, 4), MAIN)]


def test_single_releases_between_the_same_two_pieces_leave_no_empty_row() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    special = make_work("special", Kind.TV_SPECIAL, "2020-01-12")
    assert keys(build_rows([season(), film, special])) == [
        ("show-s1", (1, 2), MAIN),
        ("film", None, MAIN),
        ("special", None, MAIN),
        ("show-s1", (3, 4), MAIN),
    ]


@pytest.mark.parametrize(
    "kind", [Kind.FEATURE_FILM, Kind.TV_MOVIE, Kind.TV_SPECIAL, Kind.TV_EPISODE]
)
def test_every_main_single_release_kind_splits_a_season(kind: Kind) -> None:
    # TV_EPISODE is how a crossover episode from another show is recorded.
    single = make_work("single", kind, "2020-01-10")
    assert keys(build_rows([season(), single])) == [
        ("show-s1", (1, 2), MAIN),
        ("single", None, MAIN),
        ("show-s1", (3, 4), MAIN),
    ]


def test_an_all_at_once_season_splits_a_running_season() -> None:
    binge = make_work(
        "binge-s1", Kind.TV_SEASON, "2020-01-10", pieces=["2020-01-10", "2020-01-10", "2020-01-10"]
    )
    assert keys(build_rows([season(), binge])) == [
        ("show-s1", (1, 2), MAIN),
        ("binge-s1", None, MAIN),
        ("show-s1", (3, 4), MAIN),
    ]


def test_two_weekly_seasons_do_not_split_each_other() -> None:
    other = make_work(
        "other-s1", Kind.TV_SEASON, "2020-01-10", pieces=["2020-01-10", "2020-01-17", "2020-01-24"]
    )
    assert keys(build_rows([season(), other])) == [
        ("show-s1", None, MAIN),
        ("other-s1", None, MAIN),
    ]


def test_pieces_known_only_to_the_year_are_not_an_all_at_once_release() -> None:
    # Two pieces dated "2020" may have come out months apart, so they split nothing.
    vague = make_work("vague", Kind.TV_SEASON, "2020", pieces=["2020", "2020"])
    running = make_work(
        "running", Kind.TV_SEASON, "2019-12-25", pieces=["2019-12-25", "2020-01-08"]
    )
    assert keys(build_rows([running, vague])) == [
        ("running", None, MAIN),
        ("vague", None, MAIN),
    ]


@pytest.mark.parametrize("protected", [Kind.TV_SEASON, Kind.MINISERIES])
@pytest.mark.parametrize("kind", [Kind.SHORT_FILM, Kind.WEB_SERIES, Kind.PROMOTIONAL_CONTENT])
def test_supplementary_content_never_splits_a_season_or_miniseries(
    protected: Kind, kind: Kind
) -> None:
    extra = make_work("extra", kind, "2020-01-10")
    assert keys(build_rows([season(kind=protected), extra])) == [
        ("show-s1", None, MAIN),
        ("extra", None, MAIN),
    ]


def test_a_standalone_short_splits_a_web_series() -> None:
    webisodes = season("webisodes", kind=Kind.WEB_SERIES)
    short = make_work("short", Kind.SHORT_FILM, "2020-01-10")
    assert keys(build_rows([webisodes, short])) == [
        ("webisodes", (1, 2), MAIN),
        ("short", None, MAIN),
        ("webisodes", (3, 4), MAIN),
    ]


def test_a_film_splits_a_miniseries() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    assert keys(build_rows([season("mini", kind=Kind.MINISERIES), film])) == [
        ("mini", (1, 2), MAIN),
        ("film", None, MAIN),
        ("mini", (3, 4), MAIN),
    ]


def test_pieces_released_on_the_split_day_stay_in_the_first_row() -> None:
    # Gotham Tonight episode 5 is "either way no later than Gotham Knight": a piece on
    # the film's day counts as before it.
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-08")
    assert keys(build_rows([season(), film])) == [
        ("show-s1", (1, 2), MAIN),
        ("film", None, MAIN),
        ("show-s1", (3, 4), MAIN),
    ]


@pytest.mark.parametrize(
    ("date", "expected"),
    [
        pytest.param("2019-12-31", ["film", "show-s1"], id="before the premiere"),
        pytest.param("2020-01-01", ["film", "show-s1"], id="on the premiere day"),
        pytest.param("2020-01-22", ["show-s1", "film"], id="on the finale day"),
        pytest.param("2020-01-23", ["show-s1", "film"], id="after the finale"),
    ],
)
def test_a_release_outside_the_run_splits_nothing(date: str, expected: list[str]) -> None:
    film = make_work("film", Kind.FEATURE_FILM, date)
    rows = build_rows([season(), film])
    assert order(rows) == expected
    assert all(row.pieces is None for row in rows)


def test_a_single_release_goes_before_a_work_premiering_the_same_day() -> None:
    # António's ruling: the run has not begun earlier, so the single release comes first,
    # whatever the ids say ("a-film" would sort first by id, "z-film" would not).
    film = make_work("z-film", Kind.FEATURE_FILM, "2020-01-01")
    assert order(build_rows([season("a-show"), film])) == ["z-film", "a-show"]


def test_on_the_same_day_the_row_whose_run_began_earlier_goes_first() -> None:
    # "zeta" resumes on 8 January after the film; "alpha" premieres the same day. Both are
    # main, so the earlier run wins (the work-id fallback alone would put alpha first).
    zeta = make_work("zeta-s1", Kind.TV_SEASON, "2020-01-01", pieces=["2020-01-01", "2020-01-08"])
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-05")
    alpha = make_work("alpha-s1", Kind.TV_SEASON, "2020-01-08", pieces=["2020-01-08", "2020-01-15"])
    assert keys(build_rows([alpha, film, zeta])) == [
        ("zeta-s1", (1, 1), MAIN),
        ("film", None, MAIN),
        ("zeta-s1", (2, 2), MAIN),
        ("alpha-s1", None, MAIN),
    ]


def test_an_undated_single_release_splits_nothing() -> None:
    undated = make_work("undated", Kind.FEATURE_FILM, None)
    assert order(build_rows([season(), undated])) == ["show-s1", "undated"]


def test_a_work_with_an_undated_piece_stays_whole() -> None:
    gappy = make_work(
        "gappy", Kind.TV_SEASON, "2020-01-01", pieces=["2020-01-01", None, "2020-01-15"]
    )
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    assert keys(build_rows([gappy, film])) == [
        ("gappy", None, MAIN),
        ("film", None, MAIN),
    ]
