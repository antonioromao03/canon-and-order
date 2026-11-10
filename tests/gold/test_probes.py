"""The resolution probe set must validate and stay consistent with the gold universes."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from canon_and_order.gold import GoldFileError, ProbeSet, Split, load_probe_file
from canon_and_order.gold.__main__ import main

ROOT = Path(__file__).resolve().parents[2]
UNIVERSES = ROOT / "gold" / "universes"
PROBES = ROOT / "gold" / "probes.yaml"


def probe(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": "example",
        "input": {"title": "Example", "year": "2010"},
        "category": "misspelling",
        "split": "dev",
        "expected": "universe",
        "universe": "example-2010",
    }
    return {**data, **overrides}


def probe_set(*probes: dict[str, Any]) -> ProbeSet:
    return ProbeSet.model_validate({"status": "draft", "probes": list(probes)})


def test_repo_probe_set_is_valid() -> None:
    assert load_probe_file(PROBES, UNIVERSES).probes


def test_cli_validates_the_probe_set(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(PROBES)]) == 0
    assert "probes" in capsys.readouterr().out


@pytest.mark.parametrize(
    "overrides",
    [{"universe": None}, {"expected": "not_found"}, {"expected": "other"}],
    ids=["universe-missing", "not-found-with-universe", "other-with-universe"],
)
def test_universe_must_match_the_outcome(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="universe"):
        probe_set(probe(**overrides))


def test_probe_ids_are_unique() -> None:
    with pytest.raises(ValidationError, match="duplicate probe ids"):
        probe_set(probe(), probe())


def test_unknown_universe_and_split_mismatch_are_errors() -> None:
    probes = probe_set(probe(id="a", universe="missing-2000"), probe(id="b", split="test"))
    errors = probes.universe_errors({"example-2010": Split.DEV})
    assert errors == [
        "a: unknown universe 'missing-2000'",
        "b: split 'test' differs from universe 'example-2010'",
    ]


def test_loader_reports_universe_errors(tmp_path: Path) -> None:
    broken = tmp_path / "probes.yaml"
    data = {"status": "draft", "probes": [probe(universe="missing-2000")]}
    broken.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(GoldFileError, match="unknown universe"):
        load_probe_file(broken, UNIVERSES)
