"""What the evaluation scores: a predicted timeline, in the same shapes as a gold file.

Works are scored on completeness and dates, rows on order and rule checks. Every approach
(closed-book, one-article, hybrid) is converted to this form before scoring, so the
metrics never depend on how a prediction was made.
"""

from __future__ import annotations

import datetime as dt

from pydantic import model_validator

from canon_and_order.domain import Row, Work
from canon_and_order.domain.models import Model

__all__ = ["Prediction", "filter_to_cutoff"]


class Prediction(Model):
    works: list[Work]
    rows: list[Row]  # in timeline order

    @model_validator(mode="after")
    def _check_integrity(self) -> Prediction:
        """Ids must be unique and rows must name listed works, or matching is ambiguous.

        Lighter than gold validation on purpose: a work without a row, or rows that
        cover pieces wrongly, are prediction errors to score, not malformed input.
        """
        errors: list[str] = []
        ids = [work.id for work in self.works]
        duplicates = sorted({work_id for work_id in ids if ids.count(work_id) > 1})
        if duplicates:
            errors.append(f"duplicate work ids: {', '.join(duplicates)}")
        known = set(ids)
        errors += [
            f"row {position}: unknown work '{row.work}'"
            for position, row in enumerate(self.rows, start=1)
            if row.work not in known
        ]
        if errors:
            raise ValueError("; ".join(errors))
        return self


def filter_to_cutoff(prediction: Prediction, cutoff: dt.date) -> Prediction:
    """Drop works released after the gold cut-off, and their rows.

    A work goes only if every day its release date could be is after the cut-off, so
    "2026" survives a 2026-11-30 cut-off. Undated works stay, and only the work's own
    release date counts: a season that premiered before the cut-off stays whole.
    """
    dropped = {
        work.id
        for work in prediction.works
        if work.release is not None and work.release.starts_after(cutoff)
    }
    return Prediction(
        works=[work for work in prediction.works if work.id not in dropped],
        rows=[row for row in prediction.rows if row.work not in dropped],
    )
