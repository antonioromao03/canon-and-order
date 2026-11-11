"""The rule engine: turns works into the timeline rows users see (ADR 0001).

Deterministic and LLM-free. It imports only ``domain``, so the pipeline can call it and
the gold set can test it. The rules it implements are in gold/ANNOTATION_GUIDE.md (Rows).
"""

from canon_and_order.rules.engine import build_rows

__all__ = ["build_rows"]
