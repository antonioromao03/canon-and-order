"""Validate gold files: ``python -m canon_and_order.gold validate [paths...]``.

A path named ``probes.yaml`` is the resolution probe set, checked against the
``universes`` directory next to it; every other file is a universe file.

Runs in CI and as a pre-commit hook, so a broken annotation never reaches main.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from canon_and_order.gold.loader import GoldFileError, gold_files, load_gold_file, load_probe_file

DEFAULT_PATHS = [Path("gold/universes"), Path("gold/probes.yaml")]
PROBE_FILE_NAME = "probes.yaml"


def _expand(paths: Sequence[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        files.extend(gold_files(path) if path.is_dir() else [path])
    return files


def validate(paths: Sequence[Path]) -> int:
    files = _expand(paths)
    if not files:
        print("no gold files found", file=sys.stderr)
        return 1
    failures = 0
    tally: Counter[str] = Counter()
    for path in files:
        if path.name == PROBE_FILE_NAME:
            try:
                probes = load_probe_file(path, path.parent / "universes")
            except GoldFileError as error:
                failures += 1
                print(f"FAIL {error}", file=sys.stderr)
                continue
            tally[f"probes/{probes.status}"] += 1
            print(f"ok   {'probes':<40} {'':<4} {probes.status:<8} {len(probes.probes):>3} probes")
            continue
        try:
            universe = load_gold_file(path)
        except GoldFileError as error:
            failures += 1
            print(f"FAIL {error}", file=sys.stderr)
            continue
        tally[f"{universe.split}/{universe.status}"] += 1
        print(
            f"ok   {universe.id:<40} {universe.split:<4} {universe.status:<8} "
            f"{len(universe.works):>3} works {len(universe.rows):>3} rows"
        )
    summary = ", ".join(f"{count} {key}" for key, count in sorted(tally.items())) or "none valid"
    print(f"{len(files) - failures}/{len(files)} valid ({summary})")
    return 1 if failures else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m canon_and_order.gold")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate", help="validate gold files or directories")
    check.add_argument("paths", nargs="*", type=Path, default=DEFAULT_PATHS)
    args = parser.parse_args(argv)
    return validate(args.paths)


if __name__ == "__main__":
    raise SystemExit(main())
