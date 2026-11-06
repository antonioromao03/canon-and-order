from typing import Any

import pytest
from pydantic import ValidationError

from canon_and_order.gold import GoldUniverse


def make_universe(**overrides: Any) -> dict[str, Any]:
    """A small valid universe: a season split around a film."""
    data: dict[str, Any] = {
        "id": "example-2010",
        "input": {"title": "Example", "year": "2010"},
        "status": "draft",
        "split": "dev",
        "cutoff": "2026-11-30",
        "works": [
            {
                "id": "s1",
                "title": "Example (Season 1)",
                "kind": "tv_season",
                "release": "2010-01-10",
                "pieces": [
                    {"number": 1, "release": "2010-01-10"},
                    {"number": 2, "release": "2010-01-24"},
                ],
            },
            {
                "id": "film",
                "title": "Example: The Film",
                "kind": "feature_film",
                "release": "2010-01-17",
            },
        ],
        "rows": [
            {"work": "s1", "pieces": [1, 1]},
            {"work": "film"},
            {"work": "s1", "pieces": [2, 2]},
        ],
    }
    data.update(overrides)
    return data


def errors_for(**overrides: Any) -> str:
    with pytest.raises(ValidationError) as info:
        GoldUniverse.model_validate(make_universe(**overrides))
    return str(info.value)


def test_a_valid_universe_loads() -> None:
    universe = GoldUniverse.model_validate(make_universe())
    assert [row.work for row in universe.rows] == ["s1", "film", "s1"]
    assert universe.work("film").kind.label == "Feature Film"


def test_rows_must_reference_known_works() -> None:
    rows = [{"work": "s1"}, {"work": "film"}, {"work": "ghost"}]
    assert "unknown work 'ghost'" in errors_for(rows=rows)


def test_work_ids_must_be_unique() -> None:
    works = make_universe()["works"] + [
        {"id": "film", "title": "Again", "kind": "feature_film", "release": "2011"}
    ]
    assert "duplicate work ids: film" in errors_for(works=works)


def test_every_work_must_appear_in_a_row() -> None:
    rows = [{"work": "s1"}]
    assert "film: does not appear in any row" in errors_for(rows=rows)


def test_split_rows_must_cover_each_piece_once() -> None:
    rows = [{"work": "s1", "pieces": [1, 1]}, {"work": "film"}, {"work": "s1", "pieces": [1, 2]}]
    assert "cover each piece exactly once" in errors_for(rows=rows)


def test_split_rows_all_need_piece_ranges() -> None:
    rows = [{"work": "s1", "pieces": [1, 1]}, {"work": "film"}, {"work": "s1"}]
    assert "every row needs a piece range" in errors_for(rows=rows)


def test_row_pieces_must_exist() -> None:
    rows = [{"work": "s1", "pieces": [1, 3]}, {"work": "film"}]
    assert "are not all pieces of 's1'" in errors_for(rows=rows)


def test_nothing_may_be_released_after_the_cutoff() -> None:
    assert "after the cut-off" in errors_for(cutoff="2010-01-20")


def test_parents_must_exist() -> None:
    works = make_universe()["works"]
    works[1] = {**works[1], "parent": "nowhere"}
    assert "parent 'nowhere'" in errors_for(works=works)


def test_checks_must_reference_known_works() -> None:
    checks = [{"type": "present", "rule": "semi_canon", "work": "ghost"}]
    assert "unknown work 'ghost'" in errors_for(checks=checks)


def test_checks_need_a_known_type() -> None:
    checks = [{"type": "sometimes", "rule": "split", "work": "film"}]
    assert "sometimes" in errors_for(checks=checks)


def test_verified_files_need_citations_and_annotation_metadata() -> None:
    message = errors_for(status="verified")
    assert "need annotator, annotated_on and time_spent_minutes" in message
    assert "s1: verified works need at least one citation" in message


def test_a_complete_verified_file_passes() -> None:
    citation = {"url": "https://example.org/list", "accessed": "2026-11-07"}
    data = make_universe(
        status="verified",
        annotator="A. Annotator",
        annotated_on="2026-11-07",
        time_spent_minutes=25,
    )
    data["works"] = [{**work, "citations": [citation]} for work in data["works"]]
    assert GoldUniverse.model_validate(data).status == "verified"
