"""Evaluation metrics: score a predicted timeline against a gold universe.

Deterministic and LLM-free. The protocol is docs/evaluation.md: predicted works are
matched one-to-one to gold works by normalised title, then scored on completeness,
dates, row order and the gold file's rule checks.
"""

from canon_and_order.eval.titles import normalise_title, title_numbers

__all__ = ["normalise_title", "title_numbers"]
