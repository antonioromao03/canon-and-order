"""What a prediction is, and the cut-off filter applied before scoring.

A prediction has the same shapes as a gold file: works (what completeness and dates are
scored on) and rows (what order and rule checks are scored on). Gold is frozen at its
cut-off date, so predicted works released after it are dropped before scoring, together
with their rows (docs/evaluation.md, Gold Set).
"""

import datetime as dt

import pytest
from pydantic import ValidationError

from canon_and_order.domain import Kind, PartialDate, Piece, Row, Work
from canon_and_order.eval import Prediction, filter_to_cutoff

CUTOFF = dt.date(2026, 11, 30)


def work(work_id: str, release: str | None = None, pieces: list[str] | None = None) -> Work:
    return Work(
        id=work_id,
        title=work_id,
        kind=Kind.TV_SEASON if pieces else Kind.FEATURE_FILM,
        release=None if release is None else PartialDate.parse(release),
        pieces=[
            Piece(number=n, release=PartialDate.parse(date))
            for n, date in enumerate(pieces or [], start=1)
        ],
    )


def ids(prediction: Prediction) -> tuple[list[str], list[str]]:
    return [w.id for w in prediction.works], [r.work for r in prediction.rows]


# --- The model ---------------------------------------------------------------------------


def test_an_empty_prediction_is_valid() -> None:
    assert Prediction(works=[], rows=[]) == Prediction(works=[], rows=[])


def test_a_work_without_a_row_is_allowed() -> None:
    # It still counts for completeness and dates; only order and rule checks need rows.
    prediction = Prediction(works=[work("a"), work("b")], rows=[Row(work="a")])
    assert ids(prediction) == (["a", "b"], ["a"])


def test_work_ids_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="duplicate work ids: a"):
        Prediction(works=[work("a"), work("a")], rows=[])


def test_rows_must_name_a_listed_work() -> None:
    with pytest.raises(ValidationError, match="row 2: unknown work 'b'"):
        Prediction(works=[work("a")], rows=[Row(work="a"), Row(work="b")])


def test_unknown_fields_are_errors() -> None:
    with pytest.raises(ValidationError):
        Prediction.model_validate({"works": [], "rows": [], "notes": "x"})


# --- The cut-off filter ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("release", "kept"),
    [
        ("2026-11-30", True),  # released on the cut-off day
        ("2026-12-01", False),
        # A partial date is dropped only if every day it could be is after the cut-off.
        ("2026-11", True),
        ("2026-12", False),
        ("2026", True),
        ("2027", False),
        (None, True),  # undated: may well be out already; scored like any other work
    ],
)
def test_works_released_after_the_cutoff_are_dropped(release: str | None, kept: bool) -> None:
    prediction = Prediction(works=[work("w", release)], rows=[Row(work="w")])
    expected = (["w"], ["w"]) if kept else ([], [])
    assert ids(filter_to_cutoff(prediction, CUTOFF)) == expected


def test_dropping_a_work_drops_all_its_rows_and_keeps_the_rest_in_order() -> None:
    prediction = Prediction(
        works=[work("early", "2020-01-01"), work("late", "2027-01-01"), work("mid", "2024-06")],
        rows=[Row(work="late"), Row(work="early"), Row(work="late"), Row(work="mid")],
    )
    assert ids(filter_to_cutoff(prediction, CUTOFF)) == (["early", "mid"], ["early", "mid"])


def test_pieces_after_the_cutoff_do_not_drop_a_work_that_started_before() -> None:
    # Only the work's own release date is compared; a season that premiered before the
    # cut-off stays whole.
    season = work("s", "2026-11-20", pieces=["2026-11-20", "2026-11-27", "2026-12-04"])
    prediction = Prediction(works=[season], rows=[Row(work="s")])
    assert filter_to_cutoff(prediction, CUTOFF) == prediction
