"""Every gold file in the repo must validate, so a broken annotation fails CI."""

from pathlib import Path

import pytest

from canon_and_order.gold import GoldFileError, gold_files, load_gold_file
from canon_and_order.gold.__main__ import main

ROOT = Path(__file__).resolve().parents[2]
UNIVERSES = ROOT / "gold" / "universes"


def test_template_is_valid() -> None:
    universe = load_gold_file(ROOT / "gold" / "template.yaml")
    assert universe.id == "template"
    assert universe.checks[0].rule == "split"


@pytest.mark.parametrize("path", gold_files(UNIVERSES), ids=lambda path: path.stem)
def test_gold_file_is_valid(path: Path) -> None:
    load_gold_file(path)


def test_the_id_must_match_the_file_name(tmp_path: Path) -> None:
    source = (ROOT / "gold" / "template.yaml").read_text(encoding="utf-8")
    renamed = tmp_path / "something-else.yaml"
    renamed.write_text(source, encoding="utf-8")
    with pytest.raises(GoldFileError, match="must match the file name"):
        load_gold_file(renamed)


def test_cli_passes_on_the_repo_gold_set(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(UNIVERSES)]) == 0
    assert "valid" in capsys.readouterr().out


def test_cli_fails_on_a_broken_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "broken.yaml").write_text("id: broken\nworks: []\n", encoding="utf-8")
    assert main(["validate", str(tmp_path)]) == 1
    assert "FAIL" in capsys.readouterr().err
