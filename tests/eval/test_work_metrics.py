"""Work metrics: precision, recall and F1 per slice (docs/evaluation.md, Metrics).

Counts are stored as integers and rates computed from them, so micro averages are plain
sums. Slices: all works, core (films and series) vs extras, and canon vs semi-canon.
A true positive or a miss is sliced by the gold work's labels; a false positive, which
has no gold work, by the predicted work's labels.
"""

import pytest

from canon_and_order.domain import Canon, Kind, Work
from canon_and_order.eval import Counts, Slice, match_works, work_counts


def work(
    work_id: str, title: str, kind: Kind = Kind.FEATURE_FILM, canon: Canon = Canon.CANON
) -> Work:
    return Work(id=work_id, title=title, kind=kind, canon=canon)


def counts(gold: list[Work], predicted: list[Work]) -> dict[Slice, Counts]:
    return work_counts(gold, predicted, match_works(gold, predicted))


# --- Rates from counts -------------------------------------------------------------------


def test_rates() -> None:
    c = Counts(tp=3, fp=1, fn=2)
    assert c.precision == pytest.approx(3 / 4)
    assert c.recall == pytest.approx(3 / 5)
    assert c.f1 == pytest.approx(2 * 0.75 * 0.6 / (0.75 + 0.6))  # harmonic mean of P and R


@pytest.mark.parametrize(
    ("c", "precision", "recall", "f1"),
    [
        # Nothing in the slice on either side: every rate is 0/0, so undefined.
        (Counts(tp=0, fp=0, fn=0), None, None, None),
        # Nothing predicted: precision is undefined, recall and F1 are 0.
        (Counts(tp=0, fp=0, fn=2), None, 0.0, 0.0),
        # Nothing in gold but two predictions: recall is undefined, but F1 is 0, since
        # F1 = 2tp / (2tp + fp + fn) and every prediction was wrong.
        (Counts(tp=0, fp=2, fn=0), 0.0, None, 0.0),
    ],
)
def test_undefined_rates_are_none(
    c: Counts, precision: float | None, recall: float | None, f1: float | None
) -> None:
    assert (c.precision, c.recall, c.f1) == (precision, recall, f1)


# --- Counting ----------------------------------------------------------------------------


def test_a_perfect_prediction_has_no_errors_in_any_slice() -> None:
    gold = [
        work("film", "Batman Begins"),
        work("season", "Breaking Bad (Season 1)", Kind.TV_SEASON),
        work("promo", "Gotham Tonight", Kind.PROMOTIONAL_CONTENT),
        work("anime", "Batman: Gotham Knight", canon=Canon.SEMI_CANON),
    ]
    assert counts(gold, gold) == {
        Slice.ALL: Counts(tp=4, fp=0, fn=0),
        Slice.CORE: Counts(tp=3, fp=0, fn=0),
        Slice.EXTRAS: Counts(tp=1, fp=0, fn=0),
        Slice.CANON: Counts(tp=3, fp=0, fn=0),
        Slice.SEMI_CANON: Counts(tp=1, fp=0, fn=0),
    }


def test_every_slice_is_reported_even_when_empty() -> None:
    assert counts([], []) == {s: Counts(tp=0, fp=0, fn=0) for s in Slice}


def test_a_missed_extra_is_a_miss_in_all_and_extras() -> None:
    gold = [
        work("film", "Batman Begins"),
        work("promo", "Gotham Tonight", Kind.PROMOTIONAL_CONTENT),
    ]
    predicted = [work("p-film", "Batman Begins")]
    result = counts(gold, predicted)
    assert result[Slice.ALL] == Counts(tp=1, fp=0, fn=1)
    assert result[Slice.EXTRAS] == Counts(tp=0, fp=0, fn=1)
    assert result[Slice.CORE] == Counts(tp=1, fp=0, fn=0)


def test_an_invented_work_is_a_false_positive_sliced_by_its_predicted_labels() -> None:
    gold = [work("film", "Batman Begins")]
    predicted = [
        work("p-film", "Batman Begins"),
        work("p-invented", "Gotham Knights Origins", Kind.SHORT_FILM, Canon.SEMI_CANON),
    ]
    result = counts(gold, predicted)
    assert result[Slice.ALL] == Counts(tp=1, fp=1, fn=0)
    assert result[Slice.EXTRAS] == Counts(tp=0, fp=1, fn=0)
    assert result[Slice.SEMI_CANON] == Counts(tp=0, fp=1, fn=0)
    assert result[Slice.CANON] == Counts(tp=1, fp=0, fn=0)


def test_a_match_is_sliced_by_the_gold_labels_when_the_prediction_disagrees() -> None:
    # Gold says semi-canon, the prediction says canon: the work was still found, and it
    # counts where gold puts it.
    gold = [work("anime", "Batman: Gotham Knight", canon=Canon.SEMI_CANON)]
    predicted = [work("p-anime", "Batman: Gotham Knight", canon=Canon.CANON)]
    result = counts(gold, predicted)
    assert result[Slice.SEMI_CANON] == Counts(tp=1, fp=0, fn=0)
    assert result[Slice.CANON] == Counts(tp=0, fp=0, fn=0)


def test_core_is_films_and_series_and_extras_is_the_rest() -> None:
    gold = [
        work("feature", "A", Kind.FEATURE_FILM),
        work("tv-movie", "B", Kind.TV_MOVIE),
        work("season", "C", Kind.TV_SEASON),
        work("mini", "D", Kind.MINISERIES),
        work("special", "E", Kind.TV_SPECIAL),
        work("episode", "F", Kind.TV_EPISODE),
        work("short", "G", Kind.SHORT_FILM),
        work("web", "H", Kind.WEB_SERIES),
        work("promo", "I", Kind.PROMOTIONAL_CONTENT),
    ]
    result = counts(gold, [])
    assert result[Slice.CORE].fn == 4
    assert result[Slice.EXTRAS].fn == 5
