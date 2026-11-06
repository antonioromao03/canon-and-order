import pytest
from pydantic import ValidationError

from canon_and_order.domain import Kind, PieceRange, Work


def test_supplementary_kinds_match_the_spec() -> None:
    supplementary = {kind for kind in Kind if kind.is_supplementary}
    assert supplementary == {Kind.SHORT_FILM, Kind.WEB_SERIES, Kind.PROMOTIONAL_CONTENT}


def test_every_kind_shows_a_spec_type_name() -> None:
    assert {kind.label for kind in Kind} == {
        "Feature Film",
        "TV Movie",
        "TV Show",
        "Miniseries",
        "TV Special",
        "TV Episode",
        "Short Film",
        "Web Series",
        "Promotional Content",
    }


def test_pieces_must_be_numbered_in_release_order() -> None:
    with pytest.raises(ValidationError, match="release order"):
        Work.model_validate(
            {
                "id": "s1",
                "title": "S1",
                "kind": "tv_season",
                "pieces": [{"number": 2}, {"number": 1}],
            }
        )


def test_a_work_cannot_be_its_own_parent() -> None:
    with pytest.raises(ValidationError, match="own parent"):
        Work.model_validate(
            {"id": "promo", "title": "Promo", "kind": "web_series", "parent": "promo"}
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="relase"):
        Work.model_validate(
            {"id": "film", "title": "Film", "kind": "feature_film", "relase": "2008"}
        )


def test_work_ids_are_slugs() -> None:
    with pytest.raises(ValidationError):
        Work.model_validate({"id": "Not A Slug", "title": "Film", "kind": "feature_film"})


def test_piece_range_accepts_a_pair_or_a_single_number() -> None:
    assert PieceRange.model_validate([1, 5]).numbers() == range(1, 6)
    assert PieceRange.model_validate(6).numbers() == range(6, 7)


def test_piece_range_cannot_be_reversed() -> None:
    with pytest.raises(ValidationError, match="reversed"):
        PieceRange.model_validate([5, 1])
