"""Build the ordered timeline rows for one universe from its works.

The rules are in gold/ANNOTATION_GUIDE.md (Rows). Two steps:

1. Split: a single release that comes out while a multi-piece work is still releasing
   cuts that work at its date, so one work can give several rows.
2. Sort: every row by its date, then the same-day tie-breaks.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from canon_and_order.domain import Kind, PartialDate, Piece, PieceRange, Row, Work

DayKey = tuple[int, int, int, int]

# Sorts after every real date, so undated rows go last.
_UNDATED: DayKey = (1, 0, 0, 0)

# Supplementary content never splits these.
_PROTECTED = frozenset({Kind.TV_SEASON, Kind.MINISERIES})


@dataclass(frozen=True)
class _Entry:
    """A row plus what the sorting rules need to place it."""

    row: Row
    date: PartialDate | None  # the row's own date: its first piece for a split part
    run_start: PartialDate | None  # when the work's run began (earlier than date for later parts)
    supplementary: bool
    single: bool  # a single release: no pieces, or all of them out on one day


def build_rows(works: Sequence[Work]) -> list[Row]:
    """Return the universe's rows in timeline order.

    A whole-work row has ``pieces=None``; a split part carries its piece range.
    """
    entries = [entry for work in works for entry in _entries(work, _cuts(work, works))]
    return [entry.row for entry in sorted(entries, key=_sort_key)]


# --- Splitting -----------------------------------------------------------------------------


def _single_release_date(work: Work) -> PartialDate | None:
    """The date of a single release, or None if the work is not one (or is undated).

    Pieces count as one release only when they share one exact day: pieces known only to
    the year may have come out months apart.
    """
    if not work.pieces:
        return work.release
    first = work.pieces[0].release
    if first is None or not first.is_exact:
        return None
    return first if all(piece.release == first for piece in work.pieces) else None


def _cuts(work: Work, works: Sequence[Work]) -> list[DayKey]:
    """The days at which ``work`` is split, in order; empty if it stays whole.

    A work can be split only if it has pieces, all dated, that are not one single release.
    It is cut at each single release that came out after its first piece and before its
    last; pieces on the cut day stay before the cut.
    """
    dates = [piece.release for piece in work.pieces]
    if not dates or _single_release_date(work) is not None:
        return []
    known = [date for date in dates if date is not None]
    if len(known) < len(dates):
        return []  # an undated piece could fall on either side of a cut
    first, last = _day(known[0]), _day(known[-1])
    cuts: set[DayKey] = set()
    for other in works:
        date = _single_release_date(other)
        if date is None or other.id == work.id:
            continue
        if other.kind.is_supplementary and work.kind in _PROTECTED:
            continue
        if first < _day(date) < last:
            cuts.add(_day(date))
    return sorted(cuts)


def _entries(work: Work, cuts: list[DayKey]) -> list[_Entry]:
    """One entry for a whole work, or one per part when it has cuts."""
    supplementary = work.kind.is_supplementary
    if not cuts:
        single = _single_release_date(work) is not None
        return [_Entry(Row(work=work.id), work.release, work.release, supplementary, single)]
    parts: list[list[Piece]] = [[] for _ in range(len(cuts) + 1)]
    for piece in work.pieces:
        # The part index is how many cuts fall strictly before the piece's day.
        parts[sum(cut < _day(piece.release) for cut in cuts)].append(piece)
    run_start = work.pieces[0].release
    return [
        _Entry(
            Row(work=work.id, pieces=PieceRange(first=part[0].number, last=part[-1].number)),
            part[0].release,
            run_start,
            supplementary,
            single=False,
        )
        for part in parts
        if part  # two cuts with no piece between them leave no empty row
    ]


# --- Sorting -------------------------------------------------------------------------------


def _sort_key(entry: _Entry) -> tuple[DayKey, bool, DayKey, bool, str, int]:
    """Oldest first; then the same-day tie-breaks, in the guide's order.

    1. Supplementary before main.
    2. The row whose work's run began earlier (a season's later part before a premiere).
    3. A single release before a multi-piece work premiering that day.
    4. Work id, then first piece: not a spec rule, only so the result never depends on
       the input order.
    """
    first_piece = entry.row.pieces.first if entry.row.pieces else 0
    return (
        _day(entry.date),
        not entry.supplementary,
        _day(entry.run_start),
        not entry.single,
        entry.row.work,
        first_piece,
    )


def _day(date: PartialDate | None) -> DayKey:
    """A comparable key: the earliest day a date could be (ADR 0002); undated sorts last."""
    return _UNDATED if date is None else (0, *date.sort_key())
