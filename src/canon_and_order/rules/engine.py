"""Build the ordered timeline rows for one universe from its works."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from canon_and_order.domain import PartialDate, Row, Work

# Sorts after every real date, so undated works go last.
_UNDATED = (1, 0, 0, 0)


@dataclass(frozen=True)
class _Entry:
    """A row plus what the sorting rules need to place it."""

    row: Row
    date: PartialDate | None
    supplementary: bool


def build_rows(works: Sequence[Work]) -> list[Row]:
    """Return the universe's rows in timeline order.

    A whole-work row has ``pieces=None``; a split or companion part carries its piece range.
    """
    entries = [
        _Entry(Row(work=work.id), work.release, work.kind.is_supplementary) for work in works
    ]
    return [entry.row for entry in sorted(entries, key=_sort_key)]


def _sort_key(entry: _Entry) -> tuple[tuple[int, int, int, int], bool, str]:
    """Oldest first; same day: supplementary before main; then work id, so the result is stable.

    A partial date sorts by the earliest day it could be (ADR 0002), so "2010" ties with
    1 January 2010 and the tie-breaks decide.
    """
    date = _UNDATED if entry.date is None else (0, *entry.date.sort_key())
    return (date, not entry.supplementary, entry.row.work)
