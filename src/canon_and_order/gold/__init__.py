"""The gold set: hand-verified timelines used to evaluate the pipeline."""

from canon_and_order.gold.loader import GoldFileError, gold_files, load_gold_dir, load_gold_file
from canon_and_order.gold.schema import GoldUniverse, Rule, Split, Status

__all__ = [
    "GoldFileError",
    "GoldUniverse",
    "Rule",
    "Split",
    "Status",
    "gold_files",
    "load_gold_dir",
    "load_gold_file",
]
