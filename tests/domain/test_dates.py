import datetime as dt

import pytest
from pydantic import ValidationError

from canon_and_order.domain import PartialDate, Precision


@pytest.mark.parametrize(
    ("text", "year", "month", "day", "approximate"),
    [
        ("2008-07-18", 2008, 7, 18, False),
        ("2008-07", 2008, 7, None, False),
        ("2008", 2008, None, None, False),
        ("18/07/2008", 2008, 7, 18, False),
        ("??/03/2009", 2009, 3, None, False),
        ("??/??/2009", 2009, None, None, False),
        ("c. 725 BC", -725, None, None, True),
        ("800 BC", -800, None, None, False),
        ("AD 160", 160, None, None, False),
        ("c. 1010", 1010, None, None, True),
    ],
)
def test_parses_supported_forms(
    text: str, year: int, month: int | None, day: int | None, approximate: bool
) -> None:
    date = PartialDate.parse(text)
    assert (date.year, date.month, date.day, date.approximate) == (year, month, day, approximate)


@pytest.mark.parametrize("value", [dt.date(2008, 7, 18), "2008-07-18", "18/07/2008"])
def test_accepts_yaml_values(value: object) -> None:
    assert PartialDate.model_validate(value) == PartialDate(year=2008, month=7, day=18)


def test_accepts_a_bare_year_as_yaml_gives_it() -> None:
    assert PartialDate.model_validate(2008) == PartialDate(year=2008)


@pytest.mark.parametrize(
    "text",
    ["2008-13", "2009-02-30", "2010-02-29", "15/??/2009", "0", "July 2008", "AD 160 AD"],
)
def test_rejects_invalid_dates(text: str) -> None:
    with pytest.raises(ValidationError):
        PartialDate.parse(text)


def test_a_day_needs_a_month() -> None:
    with pytest.raises(ValidationError):
        PartialDate(year=2008, day=3)


def test_leap_day_is_valid() -> None:
    assert PartialDate.parse("2008-02-29").day == 29


@pytest.mark.parametrize(
    ("text", "precision"),
    [("2008-07-18", Precision.DAY), ("??/07/2008", Precision.MONTH), ("2008", Precision.YEAR)],
)
def test_precision(text: str, precision: Precision) -> None:
    assert PartialDate.parse(text).precision is precision


def test_only_known_days_are_exact() -> None:
    assert PartialDate.parse("2008-07-18").is_exact
    assert not PartialDate.parse("2008-07").is_exact
    assert not PartialDate(year=1010, month=1, day=1, approximate=True).is_exact


def test_sorts_by_the_earliest_day_it_could_be() -> None:
    texts = ["2009-03-15", "??/03/2009", "2009", "c. 725 BC", "2008-12-31"]
    ordered = sorted(PartialDate.parse(text) for text in texts)
    assert [date.to_spec() for date in ordered] == [
        "c. 725 BC",
        "31/12/2008",
        "??/??/2009",
        "??/03/2009",
        "15/03/2009",
    ]


@pytest.mark.parametrize(
    "text", ["18/07/2008", "??/03/2009", "??/??/2009", "c. 725 BC", "AD 160", "c. 1010"]
)
def test_spec_format_round_trips(text: str) -> None:
    assert PartialDate.parse(text).to_spec() == text


def test_earliest_latest_and_contains() -> None:
    february = PartialDate.parse("2008-02")
    assert february.earliest() == dt.date(2008, 2, 1)
    assert february.latest() == dt.date(2008, 2, 29)
    assert february.contains(dt.date(2008, 2, 15))
    assert not february.contains(dt.date(2008, 3, 1))


def test_starts_after_a_cutoff() -> None:
    cutoff = dt.date(2026, 11, 30)
    assert PartialDate.parse("2027").starts_after(cutoff)
    assert not PartialDate.parse("2026-11").starts_after(cutoff)
    assert not PartialDate.parse("c. 725 BC").starts_after(cutoff)


def test_bc_dates_have_no_calendar_date() -> None:
    with pytest.raises(ValueError, match="cannot be converted"):
        PartialDate.parse("c. 725 BC").earliest()
