"""Core domain models.

A *work* is one release the pipeline finds and the gold set records: a film, a TV season
or part, a special, a short, or a set of webisodes or promo pieces. A *row* is one line of
the timeline the user sees; the rule engine builds rows from works (splitting a season
around a film, attaching promos to the season they were made for, and so on).
Keeping the two apart lets the evaluation score completeness on works and rule
compliance on rows.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from canon_and_order.domain.dates import PartialDate

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class Model(BaseModel):
    """Base for domain models: immutable; unknown fields are errors (this catches YAML typos)."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Medium(StrEnum):
    SCREEN = "screen"
    PRINT = "print"  # books, planned
    AUDIO = "audio"  # audio originals, planned


class Kind(StrEnum):
    """What a work is. Screen kinds mirror the spec's types; book kinds come later."""

    FEATURE_FILM = "feature_film"
    TV_MOVIE = "tv_movie"
    TV_SEASON = "tv_season"
    MINISERIES = "miniseries"
    TV_SPECIAL = "tv_special"
    TV_EPISODE = "tv_episode"
    SHORT_FILM = "short_film"
    WEB_SERIES = "web_series"
    PROMOTIONAL_CONTENT = "promotional_content"

    @property
    def is_supplementary(self) -> bool:
        """Supplementary works never split a TV season and sort first on same-day ties."""
        return self in _SUPPLEMENTARY

    @property
    def label(self) -> str:
        """The type name the timeline shows."""
        return _LABELS[self]


_SUPPLEMENTARY = frozenset({Kind.SHORT_FILM, Kind.WEB_SERIES, Kind.PROMOTIONAL_CONTENT})

_LABELS = {
    Kind.FEATURE_FILM: "Feature Film",
    Kind.TV_MOVIE: "TV Movie",
    Kind.TV_SEASON: "TV Show",
    Kind.MINISERIES: "Miniseries",
    Kind.TV_SPECIAL: "TV Special",
    Kind.TV_EPISODE: "TV Episode",
    Kind.SHORT_FILM: "Short Film",
    Kind.WEB_SERIES: "Web Series",
    Kind.PROMOTIONAL_CONTENT: "Promotional Content",
}


class Canon(StrEnum):
    CANON = "canon"
    SEMI_CANON = "semi_canon"  # shown with a dagger in the timeline


class Channel(StrEnum):
    """How the public first got it; the release-date rule depends on this."""

    THEATRICAL = "theatrical"
    BROADCAST = "broadcast"
    STREAMING = "streaming"
    HOME_VIDEO = "home_video"
    WEB = "web"
    OTHER = "other"


class CitationField(StrEnum):
    """Which part of a work a citation supports."""

    EXISTENCE = "existence"
    RELEASE = "release"
    PIECES = "pieces"
    CANON = "canon"
    PARENT = "parent"
    CONTINUITY = "continuity"


class WorkFlag(StrEnum):
    """Annotation caveats, mirrored by the notes the spec asks the timeline to carry."""

    DATE_CONFLICT = "date_conflict"
    DATE_UNCONFIRMED = "date_unconfirmed"
    PIECE_DATES_UNCONFIRMED = "piece_dates_unconfirmed"
    SAME_DAY_ORDER_UNCONFIRMED = "same_day_order_unconfirmed"
    CANON_UNCLEAR = "canon_unclear"
    DESCRIPTIVE_NAME = "descriptive_name"
    TODO = "todo"


class Piece(Model):
    """One episode, webisode or promo piece of a work, numbered in release order."""

    number: int = Field(ge=1)
    title: str | None = None
    release: PartialDate | None = None


class PieceRange(Model):
    """An inclusive range of piece numbers, written ``[first, last]`` in YAML."""

    first: int = Field(ge=1)
    last: int = Field(ge=1)

    @model_validator(mode="before")
    @classmethod
    def _from_list(cls, value: Any) -> Any:
        if isinstance(value, int) and not isinstance(value, bool):
            return {"first": value, "last": value}
        if isinstance(value, list | tuple) and len(value) == 2:
            return {"first": value[0], "last": value[1]}
        return value

    @model_validator(mode="after")
    def _ordered(self) -> PieceRange:
        if self.first > self.last:
            raise ValueError(f"piece range [{self.first}, {self.last}] is reversed")
        return self

    def numbers(self) -> range:
        return range(self.first, self.last + 1)


class Citation(Model):
    url: HttpUrl
    accessed: dt.date
    supports: list[CitationField] = Field(default_factory=lambda: [CitationField.EXISTENCE])
    snippet: str = Field(default="", max_length=240)


class Work(Model):
    id: str = Field(pattern=SLUG_PATTERN)
    title: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    kind: Kind
    medium: Medium = Medium.SCREEN
    animated: bool = False
    canon: Canon = Canon.CANON
    channel: Channel | None = None
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    release: PartialDate | None = None
    parent: str | None = Field(default=None, pattern=SLUG_PATTERN)
    pieces: list[Piece] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)
    citations: list[Citation] = Field(default_factory=list)
    flags: list[WorkFlag] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def _check(self) -> Work:
        numbers = [piece.number for piece in self.pieces]
        if numbers != sorted(set(numbers)):
            raise ValueError(f"{self.id}: piece numbers must be unique and in release order")
        if self.parent == self.id:
            raise ValueError(f"{self.id}: a work cannot be its own parent")
        return self

    def piece_numbers(self) -> set[int]:
        return {piece.number for piece in self.pieces}


class RowRole(StrEnum):
    MAIN = "main"
    COMPANION = "companion"


class Row(Model):
    """One timeline row: a whole work, or a range of its pieces."""

    work: str = Field(pattern=SLUG_PATTERN)
    pieces: PieceRange | None = None
    role: RowRole = RowRole.MAIN
    label: str | None = None  # the expected display name, for humans reading the gold file
