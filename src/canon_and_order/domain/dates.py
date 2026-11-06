"""Partial dates for releases known only to the year or the month.

Release dates are often partial (the spec writes them as ``??/03/2009``), and book
universes will add historical years such as ``c. 725 BC``. ``datetime.date`` can
represent neither, so this value type stores a year with an optional month and day.

Sorting follows the spec: a partial date sorts by the earliest day it could be.
See docs/adr/0002-partial-dates.md.
"""

from __future__ import annotations

import calendar
import datetime as dt
import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = ["PartialDate", "Precision"]


class Precision(StrEnum):
    """How much of a date is known."""

    YEAR = "year"
    MONTH = "month"
    DAY = "day"


_ISO = re.compile(r"^(?P<year>\d{4})(?:-(?P<month>\d{2})(?:-(?P<day>\d{2}))?)?$")
_SPEC = re.compile(r"^(?P<day>\d{2}|\?\?)/(?P<month>\d{2}|\?\?)/(?P<year>\d{4})$")
_HISTORICAL = re.compile(
    r"^(?P<circa>c\.\s*)?(?P<ad>AD\s+)?(?P<year>\d{1,4})(?:\s+(?P<era>BC|AD))?$",
    re.IGNORECASE,
)


def _parse(text: str) -> dict[str, Any]:
    """Turn a date string into PartialDate fields, or raise ValueError."""
    value = text.strip()
    if match := _ISO.match(value):
        return {
            "year": int(match["year"]),
            "month": int(match["month"]) if match["month"] else None,
            "day": int(match["day"]) if match["day"] else None,
        }
    if match := _SPEC.match(value):
        day, month = match["day"], match["month"]
        if day != "??" and month == "??":
            raise ValueError(f"{text!r}: a known day needs a known month")
        return {
            "year": int(match["year"]),
            "month": None if month == "??" else int(month),
            "day": None if day == "??" else int(day),
        }
    if match := _HISTORICAL.match(value):
        if match["ad"] and match["era"]:
            raise ValueError(f"{text!r}: give the era once")
        year = int(match["year"])
        if (match["era"] or "").upper() == "BC":
            year = -year
        return {"year": year, "approximate": bool(match["circa"])}
    raise ValueError(
        f"{text!r} is not a supported date: use YYYY-MM-DD, YYYY-MM, YYYY, "
        "DD/MM/YYYY with ?? for unknown parts, or a form like 'c. 725 BC'"
    )


class PartialDate(BaseModel):
    """A year (negative for BC; there is no year 0), an optional month and day, and a circa flag."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    year: int
    month: int | None = None
    day: int | None = None
    approximate: bool = False

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, value: Any) -> Any:
        """Accept strings, plain years and ``datetime.date``: YAML produces all three."""
        if isinstance(value, dt.datetime):
            value = value.date()
        if isinstance(value, dt.date):
            return {"year": value.year, "month": value.month, "day": value.day}
        if isinstance(value, int) and not isinstance(value, bool):
            return {"year": value}
        if isinstance(value, str):
            return _parse(value)
        return value

    @model_validator(mode="after")
    def _check_ranges(self) -> PartialDate:
        if self.year == 0:
            raise ValueError("there is no year 0: write 1 BC as -1")
        if self.month is None:
            if self.day is not None:
                raise ValueError("a day needs a month")
            return self
        if not 1 <= self.month <= 12:
            raise ValueError(f"month {self.month} is not between 1 and 12")
        if self.day is not None:
            last = calendar.monthrange(self.year, self.month)[1] if self.year > 0 else 31
            if not 1 <= self.day <= last:
                raise ValueError(f"day {self.day} does not exist in month {self.month}")
        return self

    @classmethod
    def parse(cls, text: str) -> PartialDate:
        """Parse ``2008-07-18``, ``2008-07``, ``2008``, ``??/07/2008`` or ``c. 725 BC``."""
        return cls.model_validate(text)

    @property
    def precision(self) -> Precision:
        if self.day is not None:
            return Precision.DAY
        if self.month is not None:
            return Precision.MONTH
        return Precision.YEAR

    @property
    def is_exact(self) -> bool:
        """True for a known day that is not marked approximate."""
        return self.precision is Precision.DAY and not self.approximate

    def sort_key(self) -> tuple[int, int, int]:
        """The earliest day this date could be, as a tuple that also orders BC years."""
        return (self.year, self.month or 1, self.day or 1)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PartialDate):
            return NotImplemented
        return self.sort_key() < other.sort_key()

    def earliest(self) -> dt.date:
        """The first day this date could be (AD dates only)."""
        self._require_ad()
        return dt.date(self.year, self.month or 1, self.day or 1)

    def latest(self) -> dt.date:
        """The last day this date could be (AD dates only)."""
        self._require_ad()
        month = self.month or 12
        day = self.day or calendar.monthrange(self.year, month)[1]
        return dt.date(self.year, month, day)

    def contains(self, day: dt.date) -> bool:
        """Whether a full date is consistent with this partial date."""
        return self.earliest() <= day <= self.latest()

    def starts_after(self, day: dt.date) -> bool:
        """Whether every day this date could be is later than ``day`` (for cut-off checks)."""
        return self.year > 0 and self.earliest() > day

    def to_spec(self) -> str:
        """Render as the spec does: ``DD/MM/YYYY`` with ``??`` for unknown parts, or ``c. 725 BC``.

        Historical forms keep only the year, which is all the spec ever shows for them.
        """
        if self.year >= 1000 and not self.approximate:
            day = f"{self.day:02d}" if self.day else "??"
            month = f"{self.month:02d}" if self.month else "??"
            return f"{day}/{month}/{self.year}"
        circa = "c. " if self.approximate else ""
        if self.year < 0:
            return f"{circa}{-self.year} BC"
        if self.year < 1000:
            return f"{circa}AD {self.year}"
        return f"{circa}{self.year}"

    def __str__(self) -> str:
        return self.to_spec()

    def _require_ad(self) -> None:
        if self.year < 1:
            raise ValueError(f"{self.to_spec()} cannot be converted to datetime.date")
