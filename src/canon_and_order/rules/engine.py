"""Build the ordered timeline rows for one universe from its works.

The rules are in gold/ANNOTATION_GUIDE.md (Rows). Three steps:

1. Split: a single release that comes out while a multi-piece work is still releasing
   cuts that work at its date, so one work can give several rows.
2. Sort: every ordinary row by its date, then the same-day tie-breaks.
3. Attach companions: a work made for a season and released during its run is cut where
   the season is cut, and each part goes directly before or after its season part.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from canon_and_order.domain import Kind, PartialDate, Piece, PieceRange, Row, RowRole, Work

DayKey = tuple[int, int, int, int]

# Sorts after every real date, so undated rows go last.
_UNDATED: DayKey = (1, 0, 0, 0)

# Supplementary content never splits these.
_PROTECTED = frozenset({Kind.TV_SEASON, Kind.MINISERIES})


@dataclass(frozen=True)
class _Entry:
    """A row plus what the sorting rules need to place it."""

    row: Row
    part: int  # which stretch between the work's cuts (or its season's) the row covers
    date: PartialDate | None  # the row's own date: its first piece for a split part
    run_start: PartialDate | None  # when the work's run began (earlier than date for later parts)
    supplementary: bool
    single: bool  # a single release: no pieces, or all of them out on one day


def build_rows(works: Sequence[Work]) -> list[Row]:
    """Return the universe's rows in timeline order.

    A whole-work row has ``pieces=None``; a split part carries its piece range.
    """
    by_id = {work.id: work for work in works}
    # Companion work -> the season it was made for.
    seasons = {work.id: work.parent for work in works if work.parent and _is_companion(work, by_id)}
    companions = [work for work in works if work.id in seasons]
    ordinary = [work for work in works if work.id not in seasons]

    cuts = {work.id: _cuts(work, works) for work in ordinary}
    entries = sorted(
        (entry for work in ordinary for entry in _entries(work, cuts[work.id], RowRole.MAIN)),
        key=_sort_key,
    )

    # Companion parts, keyed by the (season, part) row they sit next to.
    before: dict[tuple[str, int], list[_Entry]] = defaultdict(list)
    after: dict[tuple[str, int], list[_Entry]] = defaultdict(list)
    season_rows = {(entry.row.work, entry.part): entry for entry in entries}
    for work in companions:
        season_id = seasons[work.id]
        for entry in _entries(work, cuts[season_id], RowRole.COMPANION):
            # A stretch where the season has no episode attaches to the season's previous part.
            part = max(p for (w, p) in season_rows if w == season_id and p <= entry.part)
            anchor = season_rows[(season_id, part)]
            side = before if _day(entry.date) <= _day(anchor.date) else after
            side[(season_id, part)].append(entry)

    rows: list[Row] = []
    for entry in entries:
        anchor_key = (entry.row.work, entry.part)
        rows += [e.row for e in sorted(before[anchor_key], key=_sort_key)]
        rows.append(entry.row)
        rows += [e.row for e in sorted(after[anchor_key], key=_sort_key)]
    return rows


# --- Companions ----------------------------------------------------------------------------


def _is_companion(work: Work, by_id: dict[str, Work]) -> bool:
    """Whether supplementary content made for a season was released during its run.

    The run is premiere to finale, both days included. The guide sets ``parent`` only on
    supplementary content made for a season, so anything else, or a work whose season is
    missing or whose dates are incomplete, is an ordinary row.
    """
    parent = by_id.get(work.parent) if work.parent else None
    if parent is None or not work.kind.is_supplementary or parent.kind not in _PROTECTED:
        return False
    run, span = _span(parent), _span(work)
    return run is not None and span is not None and span[0] <= run[1] and span[1] >= run[0]


def _span(work: Work) -> tuple[DayKey, DayKey] | None:
    """First and last release day: of its pieces, or its own release if it has none."""
    dates = [piece.release for piece in work.pieces] if work.pieces else [work.release]
    if any(date is None for date in dates):
        return None
    return _day(dates[0]), _day(dates[-1])


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


def _entries(work: Work, cuts: list[DayKey], role: RowRole) -> list[_Entry]:
    """One entry for a work that falls in one stretch between cuts, else one per stretch.

    A companion is cut with its season's cuts, so even a whole companion row records
    which stretch, and so which season part, it belongs to.
    """
    supplementary = work.kind.is_supplementary

    def stretch(date: PartialDate | None) -> int:
        # How many cuts fall strictly before the day: pieces on a cut day stay before it.
        return sum(cut < _day(date) for cut in cuts)

    parts: dict[int, list[Piece]] = defaultdict(list)
    for piece in work.pieces:
        parts[stretch(piece.release)].append(piece)
    if len(parts) <= 1:
        part = next(iter(parts)) if parts else stretch(work.release)
        single = _single_release_date(work) is not None
        row = Row(work=work.id, role=role)
        return [_Entry(row, part, work.release, work.release, supplementary, single)]
    run_start = work.pieces[0].release
    return [
        _Entry(
            Row(work=work.id, pieces=PieceRange(first=ps[0].number, last=ps[-1].number), role=role),
            part,
            ps[0].release,
            run_start,
            supplementary,
            single=False,
        )
        for part, ps in sorted(parts.items())  # stretches with no piece leave no row
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
