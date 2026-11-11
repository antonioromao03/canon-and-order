"""Regression test: the rule engine rebuilds the rows of every verified dev gold universe.

Gold rows were written by hand from the annotation guide, never by the engine, so this
checks the engine against an independent reading of the spec. It compares work, piece
range and role (labels are not scored).

Only ``split: dev`` universes run here. Test-split universes are held out: seeing their
results while changing the rules would be tuning on the test set. They are scored only
at evaluation milestones.
"""

from pathlib import Path

import pytest

from canon_and_order.domain import Row
from canon_and_order.gold import load_gold_dir
from canon_and_order.gold.schema import GoldUniverse, Split, Status
from canon_and_order.rules import build_rows

UNIVERSES = Path(__file__).resolve().parents[2] / "gold" / "universes"

DEV = [
    universe
    for universe in load_gold_dir(UNIVERSES)
    if universe.split is Split.DEV and universe.status is Status.VERIFIED
]


def describe(rows: list[Row]) -> list[str]:
    """One readable line per row, so a failure shows a line-by-line diff."""
    lines = []
    for row in rows:
        pieces = "" if row.pieces is None else f" [{row.pieces.first}-{row.pieces.last}]"
        lines.append(f"{row.work}{pieces} ({row.role})")
    return lines


def test_there_are_dev_universes_to_check() -> None:
    # Guards against the parametrized test below silently running zero cases.
    assert len(DEV) >= 4


@pytest.mark.parametrize("universe", DEV, ids=lambda universe: universe.id)
def test_engine_rebuilds_the_gold_rows(universe: GoldUniverse) -> None:
    assert describe(build_rows(universe.works)) == describe(universe.rows)
