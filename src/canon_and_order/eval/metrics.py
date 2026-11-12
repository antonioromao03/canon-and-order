"""Metrics computed from one universe's matching (docs/evaluation.md, Metrics).

Results are integer counts; rates are derived from them. Micro averages across
universes are then plain sums of counts, and recorded results compare exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from canon_and_order.domain import Canon, Work
from canon_and_order.domain.models import Model
from canon_and_order.eval.matching import KindGroup, Matching, kind_group

__all__ = ["Counts", "Slice", "work_counts"]


# --- Works: precision, recall, F1 --------------------------------------------------------


class Slice(StrEnum):
    """Subsets of works that precision, recall and F1 are also reported on."""

    ALL = "all"
    CORE = "core"  # films and series
    EXTRAS = "extras"  # everything else: specials, episodes, shorts, web series, promos
    CANON = "canon"
    SEMI_CANON = "semi_canon"


class Counts(Model):
    tp: int  # gold works matched by a prediction
    fp: int  # predictions matching no gold work
    fn: int  # gold works no prediction matched

    @property
    def precision(self) -> float | None:
        return _ratio(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float | None:
        return _ratio(self.tp, self.tp + self.fn)

    @property
    def f1(self) -> float | None:
        """2tp / (2tp + fp + fn): the harmonic mean of precision and recall when both exist.

        Written over counts, it is also defined when one of them is not: a slice gold
        does not have, where every prediction is wrong, scores 0 rather than None.
        """
        return _ratio(2 * self.tp, 2 * self.tp + self.fp + self.fn)


def work_counts(
    gold: Sequence[Work], predicted: Sequence[Work], matching: Matching
) -> dict[Slice, Counts]:
    """True positives, false positives and misses in every slice.

    A match or a miss is sliced by the gold work's labels; a false positive has no gold
    work, so it is sliced by the predicted work's labels.
    """
    gold_by_id = {work.id: work for work in gold}
    predicted_by_id = {work.id: work for work in predicted}
    tp = [gold_by_id[match.gold] for match in matching.matches]
    fn = [gold_by_id[work_id] for work_id in matching.unmatched_gold]
    fp = [predicted_by_id[work_id] for work_id in matching.unmatched_predicted]
    return {
        s: Counts(
            tp=sum(s in _slices(w) for w in tp),
            fp=sum(s in _slices(w) for w in fp),
            fn=sum(s in _slices(w) for w in fn),
        )
        for s in Slice
    }


def _slices(work: Work) -> set[Slice]:
    extra = kind_group(work.kind) is KindGroup.EXTRA
    semi = work.canon is Canon.SEMI_CANON
    return {
        Slice.ALL,
        Slice.EXTRAS if extra else Slice.CORE,
        Slice.SEMI_CANON if semi else Slice.CANON,
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    """numerator / denominator, or None when 0/0 leaves the rate undefined."""
    return numerator / denominator if denominator else None
