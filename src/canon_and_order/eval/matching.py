"""Match predicted works to gold works one-to-one (docs/evaluation.md, Matching).

A gold-predicted pair is a candidate when:

1. their kinds are in the same group (film, series, extra);
2. for some pair of their names (title or alias), the numbers in the two names agree
   (the number guard: token_set_ratio scores "Spider-Man" vs "Spider-Man 2" at 100);
3. on such a pair of names, rapidfuzz token_set_ratio on the normalised names is at least
   the threshold.

Candidates are assigned one-to-one with the Hungarian algorithm, maximising total
similarity. token_set_ratio also scores 100 when one title's words are a subset of the
other's ("Spider-Man" vs "Spider-Man: No Way Home"), so the assignment adds plain ratio
divided by 1000 as a tie-break: identical titles win ties, and the nudge (at most 0.1)
cannot override a clearer token_set difference.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

import numpy as np
from rapidfuzz import fuzz
from scipy.optimize import linear_sum_assignment

from canon_and_order.domain import Kind, Work
from canon_and_order.domain.models import Model
from canon_and_order.eval.titles import normalise_title, title_numbers

__all__ = ["KindGroup", "Match", "Matching", "kind_group", "match_works"]

DEFAULT_THRESHOLD = 85.0


class KindGroup(StrEnum):
    """Kinds that may match each other: a prediction may call a season a miniseries."""

    FILM = "film"
    SERIES = "series"
    EXTRA = "extra"


_GROUPS = {
    Kind.FEATURE_FILM: KindGroup.FILM,
    Kind.TV_MOVIE: KindGroup.FILM,
    Kind.TV_SEASON: KindGroup.SERIES,
    Kind.MINISERIES: KindGroup.SERIES,
    Kind.TV_SPECIAL: KindGroup.EXTRA,
    Kind.TV_EPISODE: KindGroup.EXTRA,
    Kind.SHORT_FILM: KindGroup.EXTRA,
    Kind.WEB_SERIES: KindGroup.EXTRA,
    Kind.PROMOTIONAL_CONTENT: KindGroup.EXTRA,
}


def kind_group(kind: Kind) -> KindGroup:
    return _GROUPS[kind]


class Match(Model):
    gold: str  # gold work id
    predicted: str  # predicted work id
    score: float  # token_set_ratio of the best pair of names, 0-100


class Matching(Model):
    """The one-to-one assignment; ids are listed in the order the works were given."""

    threshold: float
    matches: list[Match]
    unmatched_gold: list[str]
    unmatched_predicted: list[str]


def match_works(
    gold: Sequence[Work], predicted: Sequence[Work], threshold: float = DEFAULT_THRESHOLD
) -> Matching:
    """Assign predicted works to gold works one-to-one, maximising total title similarity."""
    # weights[i, j] is the assignment weight of gold i with predicted j; 0 if not a candidate.
    weights = np.zeros((len(gold), len(predicted)))
    scores: dict[tuple[int, int], float] = {}
    for i, gold_work in enumerate(gold):
        for j, predicted_work in enumerate(predicted):
            best = _best_names(gold_work, predicted_work)
            if best is not None and best[0] >= threshold:
                scores[i, j] = best[0]
                weights[i, j] = best[0] + best[1] / 1000

    # Non-candidates weigh 0, so the solver may pair them only where that costs nothing;
    # such pairs are dropped, which leaves the best assignment of candidates.
    rows, cols = linear_sum_assignment(weights, maximize=True)
    assigned = {
        int(i): int(j) for i, j in zip(rows, cols, strict=True) if (int(i), int(j)) in scores
    }

    matched_predicted = set(assigned.values())
    return Matching(
        threshold=threshold,
        matches=[
            Match(gold=gold[i].id, predicted=predicted[j].id, score=scores[i, j])
            for i, j in sorted(assigned.items())
        ],
        unmatched_gold=[work.id for i, work in enumerate(gold) if i not in assigned],
        unmatched_predicted=[
            work.id for j, work in enumerate(predicted) if j not in matched_predicted
        ],
    )


def _best_names(gold: Work, predicted: Work) -> tuple[float, float] | None:
    """(token_set_ratio, ratio) of the closest pair of names that passes the guards.

    None if the kinds are in different groups or no pair of names has agreeing numbers.
    """
    if kind_group(gold.kind) is not kind_group(predicted.kind):
        return None
    best: tuple[float, float] | None = None
    for gold_name in [gold.title, *gold.aliases]:
        for predicted_name in [predicted.title, *predicted.aliases]:
            if title_numbers(gold_name) != title_numbers(predicted_name):
                continue
            a, b = normalise_title(gold_name), normalise_title(predicted_name)
            candidate = (fuzz.token_set_ratio(a, b), fuzz.ratio(a, b))
            best = candidate if best is None else max(best, candidate)
    return best
