"""Small builders shared by the rule-engine tests."""

from canon_and_order.domain import Kind, PartialDate, Piece, Row, RowRole, Work

RowKey = tuple[str, tuple[int, int] | None, RowRole]


def make_work(
    work_id: str,
    kind: Kind,
    release: str | None,
    pieces: list[str | None] | None = None,
    parent: str | None = None,
) -> Work:
    """A minimal work; ``pieces`` lists piece release dates in release order (None: undated)."""
    return Work(
        id=work_id,
        title=work_id,
        kind=kind,
        parent=parent,
        release=None if release is None else PartialDate.parse(release),
        pieces=[
            Piece(number=number, release=None if date is None else PartialDate.parse(date))
            for number, date in enumerate(pieces or [], start=1)
        ],
    )


def keys(rows: list[Row]) -> list[RowKey]:
    """What the evaluation compares: work, piece range and role (labels are not scored)."""
    return [
        (row.work, None if row.pieces is None else (row.pieces.first, row.pieces.last), row.role)
        for row in rows
    ]


def order(rows: list[Row]) -> list[str]:
    return [row.work for row in rows]
