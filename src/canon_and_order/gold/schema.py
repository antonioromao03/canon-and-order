"""Schema for gold-set files (gold/universes/*.yaml).

A gold file records, for one universe, the works a correct timeline contains, the rows
it shows, and a few targeted rule checks. Validation is strict on purpose: an annotation
mistake should fail CI, not quietly skew an evaluation. See gold/ANNOTATION_GUIDE.md.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from canon_and_order.domain.models import SLUG_PATTERN, Kind, Model, Row, Work


class Status(StrEnum):
    DRAFT = "draft"  # may be incomplete; never used to score an evaluation
    VERIFIED = "verified"  # every field checked against a cited source


class Split(StrEnum):
    DEV = "dev"  # used while building and tuning prompts
    TEST = "test"  # held out; scored only at milestones


class Rule(StrEnum):
    """The spec's rules, as named in rule checks and in the evaluation report."""

    SCOPE_CONTINUITY = "scope_continuity"
    CROSSOVER = "crossover"
    SEMI_CANON = "semi_canon"
    EXCLUSION = "exclusion"
    RELEASE_DATE = "release_date"
    SEASON_PARTS = "season_parts"
    COMPANION = "companion"
    SPLIT = "split"
    SORTING = "sorting"


class Input(Model):
    title: str = Field(min_length=1)
    year: str | None = None  # a year or a range such as "2008-2013", as the user types it


class Exclusion(Model):
    title: str
    reason: str


class Upcoming(Model):
    title: str
    kind: Kind
    expected: str  # only as precise as announced: "11/12/2027", "Late 2027", "TBA"


class PresentCheck(Model):
    type: Literal["present"]
    rule: Rule
    work: str = Field(pattern=SLUG_PATTERN)
    note: str = ""


class AbsentCheck(Model):
    type: Literal["absent"]
    rule: Rule
    title: str
    note: str = ""


class BeforeCheck(Model):
    type: Literal["before"]
    rule: Rule
    first: str = Field(pattern=SLUG_PATTERN)
    then: str = Field(pattern=SLUG_PATTERN)
    note: str = ""


class RowCountCheck(Model):
    type: Literal["row_count"]
    rule: Rule
    work: str = Field(pattern=SLUG_PATTERN)
    rows: int = Field(ge=1)
    note: str = ""


Check = Annotated[
    PresentCheck | AbsentCheck | BeforeCheck | RowCountCheck,
    Field(discriminator="type"),
]


class GoldUniverse(Model):
    schema_version: Literal[1] = 1
    id: str = Field(pattern=SLUG_PATTERN)
    input: Input
    status: Status
    split: Split
    cutoff: dt.date
    continuity: str = ""
    seeded_from_draft: bool = False
    annotator: str | None = None
    annotated_on: dt.date | None = None
    time_spent_minutes: int | None = Field(default=None, ge=0)
    works: list[Work]
    rows: list[Row]
    upcoming: list[Upcoming] = Field(default_factory=list)
    exclusions: list[Exclusion] = Field(default_factory=list)
    checks: list[Check] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_integrity(self) -> GoldUniverse:
        errors = [
            *self._work_errors(),
            *self._row_errors(),
            *self._check_errors(),
            *self._verified_errors(),
        ]
        if errors:
            raise ValueError("; ".join(errors))
        return self

    def work(self, work_id: str) -> Work:
        return next(work for work in self.works if work.id == work_id)

    def _work_errors(self) -> list[str]:
        errors: list[str] = []
        ids = [work.id for work in self.works]
        duplicates = sorted({work_id for work_id in ids if ids.count(work_id) > 1})
        if duplicates:
            errors.append(f"duplicate work ids: {', '.join(duplicates)}")
        known = set(ids)
        for work in self.works:
            if work.parent is not None and work.parent not in known:
                errors.append(f"{work.id}: parent '{work.parent}' is not a work in this file")
            dates = [work.release] + [piece.release for piece in work.pieces]
            if any(date is not None and date.starts_after(self.cutoff) for date in dates):
                errors.append(f"{work.id}: released after the cut-off {self.cutoff}")
        return errors

    def _row_errors(self) -> list[str]:
        errors: list[str] = []
        works = {work.id: work for work in self.works}
        rows_by_work: dict[str, list[Row]] = defaultdict(list)
        for position, row in enumerate(self.rows, start=1):
            if row.work not in works:
                errors.append(f"row {position}: unknown work '{row.work}'")
                continue
            rows_by_work[row.work].append(row)
            work = works[row.work]
            if row.pieces is not None and not set(row.pieces.numbers()) <= work.piece_numbers():
                errors.append(
                    f"row {position}: pieces {row.pieces.first}-{row.pieces.last} "
                    f"are not all pieces of '{work.id}'"
                )
        for work in self.works:
            rows = rows_by_work.get(work.id, [])
            if not rows:
                errors.append(f"{work.id}: does not appear in any row")
            elif work.pieces and len(rows) > 1:
                errors.extend(self._coverage_errors(work, rows))
        return errors

    @staticmethod
    def _coverage_errors(work: Work, rows: list[Row]) -> list[str]:
        """A work split over several rows must have each piece in exactly one of them."""
        if any(row.pieces is None for row in rows):
            return [f"{work.id}: split over several rows, so every row needs a piece range"]
        covered = [number for row in rows if row.pieces for number in row.pieces.numbers()]
        if sorted(covered) != sorted(work.piece_numbers()):
            return [f"{work.id}: its rows must cover each piece exactly once"]
        return []

    def _check_errors(self) -> list[str]:
        known = {work.id for work in self.works}
        referenced: list[str] = []
        for check in self.checks:
            if isinstance(check, PresentCheck | RowCountCheck):
                referenced.append(check.work)
            elif isinstance(check, BeforeCheck):
                referenced.extend([check.first, check.then])
        return [f"check refers to unknown work '{ref}'" for ref in referenced if ref not in known]

    def _verified_errors(self) -> list[str]:
        if self.status is not Status.VERIFIED:
            return []
        errors: list[str] = []
        if self.annotator is None or self.annotated_on is None or self.time_spent_minutes is None:
            errors.append("verified files need annotator, annotated_on and time_spent_minutes")
        for work in self.works:
            if work.release is None:
                errors.append(f"{work.id}: verified works need a release date")
            if not work.citations:
                errors.append(f"{work.id}: verified works need at least one citation")
            if any(piece.release is None for piece in work.pieces):
                errors.append(f"{work.id}: verified works need a date for every piece")
        return errors
