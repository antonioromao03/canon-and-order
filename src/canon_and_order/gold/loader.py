"""Load and validate gold-set files."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from canon_and_order.gold.schema import GoldUniverse


class GoldFileError(ValueError):
    """A gold file that cannot be read or does not pass validation."""


def load_gold_file(path: Path) -> GoldUniverse:
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        universe = GoldUniverse.model_validate(data)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise GoldFileError(f"{path}: {error}") from error
    if universe.id != path.stem:
        raise GoldFileError(f"{path}: id '{universe.id}' must match the file name '{path.stem}'")
    return universe


def gold_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.yaml"))


def load_gold_dir(directory: Path) -> list[GoldUniverse]:
    return [load_gold_file(path) for path in gold_files(directory)]
