"""Companion rows (gold/ANNOTATION_GUIDE.md, Rows).

A work whose ``parent`` is a season becomes a companion row when its release span (first
to last piece, or its release date if it has no pieces) overlaps the season's run,
premiere to finale, both days included. It goes directly before the season row if its
first piece came out on or before the premiere, otherwise directly after it. A parented
work released wholly outside the run is an ordinary row in date order.

When the season is split, its companion rows split at the same days, and only there:
other releases never split a companion on their own. Each companion part is placed
against the season part it falls in, by the same before/after test.
"""

import pytest
from builders import keys, make_work, order

from canon_and_order.domain import Kind, RowRole, Work
from canon_and_order.rules import build_rows

MAIN = RowRole.MAIN
COMPANION = RowRole.COMPANION

# A weekly season: four episodes, 1 to 22 January 2020.
SEASON = make_work(
    "show-s1",
    Kind.TV_SEASON,
    "2020-01-01",
    pieces=["2020-01-01", "2020-01-08", "2020-01-15", "2020-01-22"],
)


def promos(dates: list[str | None], work_id: str = "promos") -> Work:
    """A promo set made for SEASON."""
    first = dates[0] if dates else None
    return make_work(work_id, Kind.PROMOTIONAL_CONTENT, first, pieces=dates, parent="show-s1")


def extra(date: str, work_id: str = "extra", kind: Kind = Kind.SHORT_FILM) -> Work:
    """A single release made for SEASON."""
    return make_work(work_id, kind, date, parent="show-s1")


def test_breaking_bad_parented_works() -> None:
    # The Breaking Bad dev gold, seasons cut to their premiere and finale. Three companions
    # go before their season, three after, and three parented works released outside
    # the run (Chicks 'N' Guns, Taste the Family, American Greed) stay ordinary rows.
    def show(work_id: str, premiere: str, finale: str) -> Work:
        return make_work(work_id, Kind.TV_SEASON, premiere, pieces=[premiere, finale])

    def made_for(
        parent: str, work_id: str, kind: Kind, first: str, last: str | None = None
    ) -> Work:
        pieces: list[str | None] | None = None if last is None else [first, last]
        return make_work(work_id, kind, first, pieces=pieces, parent=parent)

    promo, short = Kind.PROMOTIONAL_CONTENT, Kind.SHORT_FILM
    works = [
        show("bb-s5a", "2012-07-15", "2012-09-02"),
        made_for("bb-s5a", "chicks-n-guns", short, "2013-06-04"),
        show("bb-s5b", "2013-08-11", "2013-09-29"),
        made_for("bcs-s3", "pollos-commercial-2017", promo, "2017-01-11"),
        made_for("bcs-s3", "pollos-training", promo, "2017-04-04", "2017-06-19"),
        show("bcs-s3", "2017-04-10", "2017-06-19"),
        made_for("bcs-s3", "no-picnic", short, "2017-06-19"),
        show("bcs-s4", "2018-08-06", "2018-10-08"),
        made_for("bcs-s4", "madrigal-training", promo, "2018-08-20", "2018-10-10"),
        make_work("el-camino", Kind.FEATURE_FILM, "2019-10-11"),
        make_work("snow-globe", short, "2020-02-17"),
        made_for("bcs-s5", "ethics-training", promo, "2020-02-23", "2020-04-20"),
        show("bcs-s5", "2020-02-23", "2020-04-20"),
        made_for("bcs-s6a", "american-greed", promo, "2022-04-01"),
        show("bcs-s6a", "2022-04-18", "2022-05-23"),
        made_for("bcs-s6a", "slippin-jimmy", Kind.WEB_SERIES, "2022-05-23"),
        made_for("bcs-s6b", "filmmaker-training", promo, "2022-07-11", "2022-08-16"),
        show("bcs-s6b", "2022-07-11", "2022-08-15"),
    ]
    assert keys(build_rows(list(reversed(works)))) == [
        ("bb-s5a", None, MAIN),
        ("chicks-n-guns", None, MAIN),
        ("bb-s5b", None, MAIN),
        ("pollos-commercial-2017", None, MAIN),
        ("pollos-training", None, COMPANION),
        ("bcs-s3", None, MAIN),
        ("no-picnic", None, COMPANION),
        ("bcs-s4", None, MAIN),
        ("madrigal-training", None, COMPANION),
        ("el-camino", None, MAIN),
        ("snow-globe", None, MAIN),
        ("ethics-training", None, COMPANION),
        ("bcs-s5", None, MAIN),
        ("american-greed", None, MAIN),
        ("bcs-s6a", None, MAIN),
        ("slippin-jimmy", None, COMPANION),
        ("filmmaker-training", None, COMPANION),
        ("bcs-s6b", None, MAIN),
    ]


def test_a_set_starting_after_the_premiere_is_a_companion_after_the_season() -> None:
    companion = promos(["2020-01-02", "2020-01-09", "2020-01-16", "2020-01-23"])
    assert keys(build_rows([companion, SEASON])) == [
        ("show-s1", None, MAIN),
        ("promos", None, COMPANION),
    ]


@pytest.mark.parametrize(
    "first",
    [
        pytest.param("2019-12-28", id="before the premiere"),
        pytest.param("2020-01-01", id="on the premiere day"),
    ],
)
def test_a_set_starting_by_the_premiere_is_a_companion_before_the_season(first: str) -> None:
    companion = promos([first, "2020-01-08", "2020-01-15"])
    assert keys(build_rows([SEASON, companion])) == [
        ("promos", None, COMPANION),
        ("show-s1", None, MAIN),
    ]


@pytest.mark.parametrize(
    "date",
    [
        pytest.param("2020-01-10", id="mid-run"),
        pytest.param("2020-01-22", id="on the finale day"),
    ],
)
@pytest.mark.parametrize("kind", [Kind.SHORT_FILM, Kind.WEB_SERIES])
def test_a_single_release_during_the_run_is_a_companion(date: str, kind: Kind) -> None:
    # No Picnic (a short on the finale night) and Slippin' Jimmy (a web series released
    # all at once) are companions in the Breaking Bad gold: a set is not required.
    assert keys(build_rows([SEASON, extra(date, kind=kind)])) == [
        ("show-s1", None, MAIN),
        ("extra", None, COMPANION),
    ]


@pytest.mark.parametrize(
    ("work", "expected"),
    [
        pytest.param(extra("2019-12-31"), ["extra", "show-s1"], id="single before the premiere"),
        pytest.param(extra("2020-01-23"), ["show-s1", "extra"], id="single after the finale"),
        pytest.param(
            promos(["2019-12-20", "2019-12-31"]),
            ["promos", "show-s1"],
            id="set ending before the premiere",
        ),
        pytest.param(
            promos(["2020-01-23", "2020-01-30"]),
            ["show-s1", "promos"],
            id="set starting after the finale",
        ),
    ],
)
def test_a_parented_work_wholly_outside_the_run_is_an_ordinary_row(
    work: Work, expected: list[str]
) -> None:
    rows = build_rows([SEASON, work])
    assert order(rows) == expected
    assert all(row.role is MAIN for row in rows)


def test_a_companion_goes_directly_after_its_season_row() -> None:
    # The unparented short (3 January) sorts before the companion's first piece
    # (10 January), but the companion stays next to its season.
    short = make_work("short", Kind.SHORT_FILM, "2020-01-03")
    companion = promos(["2020-01-10", "2020-01-17"])
    assert keys(build_rows([short, companion, SEASON])) == [
        ("show-s1", None, MAIN),
        ("promos", None, COMPANION),
        ("short", None, MAIN),
    ]


def test_a_companion_goes_directly_before_its_season_row() -> None:
    # The unparented short (30 December) sorts after the companion's first piece
    # (28 December), but the companion stays next to its season.
    short = make_work("short", Kind.SHORT_FILM, "2019-12-30")
    companion = promos(["2019-12-28", "2020-01-08"])
    assert keys(build_rows([SEASON, companion, short])) == [
        ("short", None, MAIN),
        ("promos", None, COMPANION),
        ("show-s1", None, MAIN),
    ]


def test_companions_on_the_same_side_keep_date_order() -> None:
    early = promos(["2019-12-30", "2020-01-08"], work_id="z-early")
    earlier = promos(["2019-12-28", "2020-01-08"], work_id="z-earlier")
    late = extra("2020-01-20", work_id="a-late")
    soon = extra("2020-01-05", work_id="b-soon")
    assert keys(build_rows([late, early, SEASON, soon, earlier])) == [
        ("z-earlier", None, COMPANION),
        ("z-early", None, COMPANION),
        ("show-s1", None, MAIN),
        ("b-soon", None, COMPANION),
        ("a-late", None, COMPANION),
    ]


def test_a_companion_splits_with_its_season() -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    companion = promos(["2020-01-02", "2020-01-09", "2020-01-16", "2020-01-23"])
    assert keys(build_rows([SEASON, film, companion])) == [
        ("show-s1", (1, 2), MAIN),
        ("promos", (1, 2), COMPANION),
        ("film", None, MAIN),
        ("show-s1", (3, 4), MAIN),
        ("promos", (3, 4), COMPANION),
    ]


def test_each_companion_part_is_placed_against_its_own_season_part() -> None:
    # Pieces come out with each episode, the first before the premiere. Part 2 starts on
    # the same day as the season's part 2, so it goes before that part, as Ethics
    # Training does before Better Call Saul Season 5.
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    companion = promos(["2019-12-31", "2020-01-08", "2020-01-15", "2020-01-22"])
    assert keys(build_rows([SEASON, film, companion])) == [
        ("promos", (1, 2), COMPANION),
        ("show-s1", (1, 2), MAIN),
        ("film", None, MAIN),
        ("promos", (3, 4), COMPANION),
        ("show-s1", (3, 4), MAIN),
    ]


@pytest.mark.parametrize(
    "companion",
    [
        pytest.param(promos(["2020-01-16", "2020-01-23"]), id="set"),
        pytest.param(extra("2020-01-16"), id="single"),
    ],
)
def test_a_companion_on_one_side_of_the_split_stays_whole_next_to_that_part(
    companion: Work,
) -> None:
    film = make_work("film", Kind.FEATURE_FILM, "2020-01-10")
    assert keys(build_rows([companion, film, SEASON])) == [
        ("show-s1", (1, 2), MAIN),
        ("film", None, MAIN),
        ("show-s1", (3, 4), MAIN),
        (companion.id, None, COMPANION),
    ]


def test_a_companion_is_split_only_where_its_season_is() -> None:
    # A standalone short splits an unparented web series, but supplementary content never
    # splits a season, so the season's companion set stays whole too.
    short = make_work("short", Kind.SHORT_FILM, "2020-01-10")
    companion = make_work(
        "webisodes",
        Kind.WEB_SERIES,
        "2020-01-02",
        pieces=["2020-01-02", "2020-01-09", "2020-01-16"],
        parent="show-s1",
    )
    assert keys(build_rows([SEASON, short, companion])) == [
        ("show-s1", None, MAIN),
        ("webisodes", None, COMPANION),
        ("short", None, MAIN),
    ]


def test_a_parented_main_work_is_not_a_companion_and_splits_the_season() -> None:
    # The guide sets parent only on supplementary content; a special is a single release.
    special = make_work("special", Kind.TV_SPECIAL, "2020-01-10", parent="show-s1")
    assert keys(build_rows([SEASON, special])) == [
        ("show-s1", (1, 2), MAIN),
        ("special", None, MAIN),
        ("show-s1", (3, 4), MAIN),
    ]


def test_a_work_made_for_something_other_than_a_season_is_an_ordinary_row() -> None:
    webisodes = make_work(
        "webisodes", Kind.WEB_SERIES, "2020-01-01", pieces=["2020-01-01", "2020-01-15"]
    )
    promo = make_work("promo", Kind.PROMOTIONAL_CONTENT, "2020-01-08", parent="webisodes")
    assert keys(build_rows([webisodes, promo])) == [
        ("webisodes", (1, 1), MAIN),
        ("promo", None, MAIN),
        ("webisodes", (2, 2), MAIN),
    ]


def test_a_work_whose_parent_is_not_in_the_universe_is_an_ordinary_row() -> None:
    orphan = make_work("orphan", Kind.SHORT_FILM, "2020-01-10", parent="missing-season")
    assert keys(build_rows([SEASON, orphan])) == [
        ("show-s1", None, MAIN),
        ("orphan", None, MAIN),
    ]
