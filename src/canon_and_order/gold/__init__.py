"""The gold set: hand-verified timelines used to evaluate the pipeline."""

from canon_and_order.gold.loader import (
    GoldFileError,
    gold_files,
    load_gold_dir,
    load_gold_file,
    load_probe_file,
)
from canon_and_order.gold.schema import GoldUniverse, Outcome, ProbeSet, Rule, Split, Status

__all__ = [
    "GoldFileError",
    "GoldUniverse",
    "Outcome",
    "ProbeSet",
    "Rule",
    "Split",
    "Status",
    "gold_files",
    "load_gold_dir",
    "load_gold_file",
    "load_probe_file",
]
