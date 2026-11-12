"""Matching predicted works to gold works (docs/evaluation.md, Matching).

A pair can match only if the kinds are in one group (film, series, extra), the numbers in
the titles agree, and the normalised titles score at least the threshold with rapidfuzz
token_set_ratio. Pairs are then assigned one-to-one to maximise total similarity, with
plain ratio as a small tie-break so "Spider-Man" goes to "Spider-Man", not to "Spider-Man:
No Way Home" (both score 100 with token_set_ratio).
"""

from itertools import permutations
from pathlib import Path

import pytest
from rapidfuzz import fuzz

from canon_and_order.domain import Kind, Work
from canon_and_order.eval import KindGroup, Matching, kind_group, match_works, normalise_title
from canon_and_order.gold import load_gold_dir
from canon_and_order.gold.schema import GoldUniverse, Split, Status

UNIVERSES = Path(__file__).resolve().parents[2] / "gold" / "universes"

# Dev split only: test-split universes are held out (see tests/rules/test_dev_gold.py).
DEV = [
    universe
    for universe in load_gold_dir(UNIVERSES)
    if universe.split is Split.DEV and universe.status is Status.VERIFIED
]


def work(
    work_id: str, title: str, kind: Kind = Kind.FEATURE_FILM, aliases: list[str] | None = None
) -> Work:
    return Work(id=work_id, title=title, kind=kind, aliases=aliases or [])


def pairs(matching: Matching) -> set[tuple[str, str]]:
    return {(match.gold, match.predicted) for match in matching.matches}


# --- Kind groups -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "group"),
    [
        (Kind.FEATURE_FILM, KindGroup.FILM),
        (Kind.TV_MOVIE, KindGroup.FILM),
        (Kind.TV_SEASON, KindGroup.SERIES),
        (Kind.MINISERIES, KindGroup.SERIES),
        (Kind.TV_SPECIAL, KindGroup.EXTRA),
        (Kind.TV_EPISODE, KindGroup.EXTRA),
        (Kind.SHORT_FILM, KindGroup.EXTRA),
        (Kind.WEB_SERIES, KindGroup.EXTRA),
        (Kind.PROMOTIONAL_CONTENT, KindGroup.EXTRA),
    ],
)
def test_kind_groups(kind: Kind, group: KindGroup) -> None:
    assert kind_group(kind) is group


def test_every_kind_has_a_group() -> None:
    # A kind added to the domain later must be given a group, not fail at scoring time.
    for kind in Kind:
        kind_group(kind)


def test_kinds_in_one_group_can_match() -> None:
    gold = [work("g", "Breaking Bad", Kind.TV_SEASON)]
    predicted = [work("p", "Breaking Bad", Kind.MINISERIES)]
    assert pairs(match_works(gold, predicted)) == {("g", "p")}


def test_kinds_in_different_groups_never_match() -> None:
    gold = [work("g", "Spider-Man", Kind.FEATURE_FILM)]
    predicted = [work("p", "Spider-Man", Kind.TV_SEASON)]
    matching = match_works(gold, predicted)
    assert matching.matches == []
    assert matching.unmatched_gold == ["g"]
    assert matching.unmatched_predicted == ["p"]


# --- Titles, aliases and the number guard ------------------------------------------------


def test_identical_titles_match_with_score_100() -> None:
    matching = match_works([work("g", "The Dark Knight")], [work("p", "The Dark Knight")])
    assert [(m.gold, m.predicted, m.score) for m in matching.matches] == [("g", "p", 100.0)]


def test_titles_are_normalised_before_scoring() -> None:
    gold = [work("g", "Schindler's List")]
    predicted = [work("p", "SCHINDLERS LIST (1993)")]
    assert pairs(match_works(gold, predicted)) == {("g", "p")}


@pytest.mark.parametrize(
    ("gold_title", "predicted_title"),
    [
        ("Spider-Man", "Spider-Man 2"),
        ("Spider-Man 2", "Spider-Man 3"),
        ("Breaking Bad (Season 5 - Part 1)", "Breaking Bad Season 5"),
        ("Breaking Bad (Season 1)", "Breaking Bad (Season 1 - Part 1)"),
    ],
)
def test_titles_whose_numbers_differ_never_match(gold_title: str, predicted_title: str) -> None:
    assert match_works([work("g", gold_title)], [work("p", predicted_title)]).matches == []


def test_a_gold_alias_can_match() -> None:
    gold = [work("g", "Batman: Gotham Knight", aliases=["Gotham Knight Anthology"])]
    predicted = [work("p", "Gotham Knight Anthology")]
    assert pairs(match_works(gold, predicted)) == {("g", "p")}


def test_a_predicted_alias_can_match() -> None:
    gold = [work("g", "El Camino: A Breaking Bad Movie")]
    predicted = [work("p", "El Camino", aliases=["El Camino: A Breaking Bad Movie"])]
    assert pairs(match_works(gold, predicted)) == {("g", "p")}


def test_an_alias_without_numbers_lets_numbered_titles_match() -> None:
    # The guard applies per pair of names, so a gold alias can accept a prediction that
    # names the work without the range the gold title carries.
    gold = [
        work(
            "g",
            "Breaking Bad: Original Minisodes (Minisodes 1-5)",
            Kind.WEB_SERIES,
            aliases=["Breaking Bad: Original Minisodes"],
        )
    ]
    predicted = [work("p", "Breaking Bad: Original Minisodes", Kind.WEB_SERIES)]
    assert pairs(match_works(gold, predicted)) == {("g", "p")}


# --- Threshold ---------------------------------------------------------------------------


GOLD_TITLE, PREDICTED_TITLE = "Gotham Tonight", "Gotham Tonite"
SCORE = fuzz.token_set_ratio(normalise_title(GOLD_TITLE), normalise_title(PREDICTED_TITLE))


def test_a_score_equal_to_the_threshold_matches() -> None:
    matching = match_works([work("g", GOLD_TITLE)], [work("p", PREDICTED_TITLE)], threshold=SCORE)
    assert pairs(matching) == {("g", "p")}


def test_a_score_below_the_threshold_does_not_match() -> None:
    matching = match_works(
        [work("g", GOLD_TITLE)], [work("p", PREDICTED_TITLE)], threshold=SCORE + 0.01
    )
    assert matching.matches == []


def test_the_default_threshold_is_85() -> None:
    # "Gotham Tonight" vs "Gotham Tonite" scores about 89: in at 85, out at 90.
    assert 85 <= SCORE < 90
    gold, predicted = [work("g", GOLD_TITLE)], [work("p", PREDICTED_TITLE)]
    assert match_works(gold, predicted).threshold == 85
    assert pairs(match_works(gold, predicted)) == {("g", "p")}
    assert match_works(gold, predicted, threshold=90).matches == []


# --- One-to-one assignment ---------------------------------------------------------------


def test_no_works_on_either_side() -> None:
    assert match_works([], []) == Matching(
        threshold=85, matches=[], unmatched_gold=[], unmatched_predicted=[]
    )
    assert match_works([work("g", "Alien")], []).unmatched_gold == ["g"]
    assert match_works([], [work("p", "Alien")]).unmatched_predicted == ["p"]


def test_a_gold_work_matches_at_most_one_prediction() -> None:
    gold = [work("g", "The Dark Knight")]
    predicted = [work("p1", "The Dark Knight"), work("p2", "The Dark Knight")]
    matching = match_works(gold, predicted)
    assert len(matching.matches) == 1
    assert len(matching.unmatched_predicted) == 1


@pytest.mark.parametrize(
    "titles",
    [
        ["Spider-Man", "Spider-Man: No Way Home"],
        ["The Dark Knight", "The Dark Knight Rises"],
        ["Dune", "Dune: Part Two"],  # no digits, so the number guard cannot separate them
    ],
)
def test_ties_on_token_set_go_to_the_closest_title(titles: list[str]) -> None:
    # Each pair scores 100 against both titles with token_set_ratio (one title's words are
    # a subset of the other's); the plain-ratio tie-break picks the identical title,
    # whatever order the predictions come in.
    gold = [work(f"g{i}", title) for i, title in enumerate(titles)]
    for order in permutations(range(len(titles))):
        predicted = [work(f"p{i}", titles[i]) for i in order]
        assert pairs(match_works(gold, predicted)) == {
            (f"g{i}", f"p{i}") for i in range(len(titles))
        }


def test_assignment_maximises_total_similarity_not_the_best_single_pair() -> None:
    # Greedy matching would take the best pair, Gotham Tonight <-> Tonight in Gotham (100),
    # leaving Gotham Tonight Live and Gotham Tonite, which score below 85: one match.
    # The optimal assignment pairs both gold works.
    gold = [work("tonight", "Gotham Tonight"), work("live", "Gotham Tonight Live")]
    predicted = [work("in-gotham", "Tonight in Gotham"), work("tonite", "Gotham Tonite")]
    assert pairs(match_works(gold, predicted)) == {("tonight", "tonite"), ("live", "in-gotham")}


def test_results_list_ids_in_input_order() -> None:
    gold = [work("b", "Bravo"), work("a", "Alpha"), work("c", "Charlie")]
    predicted = [work("z", "Zulu"), work("pc", "Charlie"), work("pa", "Alpha")]
    matching = match_works(gold, predicted)
    assert [(m.gold, m.predicted) for m in matching.matches] == [("a", "pa"), ("c", "pc")]
    assert matching.unmatched_gold == ["b"]
    assert matching.unmatched_predicted == ["z"]


# --- Acceptance: dev gold matched to itself ----------------------------------------------


def test_there_are_dev_universes_to_check() -> None:
    assert len(DEV) >= 4


@pytest.mark.parametrize("threshold", [80, 85, 90])
@pytest.mark.parametrize("universe", DEV, ids=lambda universe: universe.id)
def test_dev_gold_matched_to_itself_is_the_identity(universe: GoldUniverse, threshold: int) -> None:
    # Reversed, so a correct result cannot come from input order alone.
    matching = match_works(universe.works, universe.works[::-1], threshold=threshold)
    assert pairs(matching) == {(w.id, w.id) for w in universe.works}
    assert matching.unmatched_gold == matching.unmatched_predicted == []
