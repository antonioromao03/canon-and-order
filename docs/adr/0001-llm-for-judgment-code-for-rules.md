# 0001. The LLM makes judgment calls; code owns dates, rows and order

- Status: accepted
- Date: 2026-11-06

## Context

The prototype asked one LLM to do everything: find releases, date them, apply the row
rules and sort. Its outputs are plausible but hard to verify, and the row rules (splitting
a season around a film, attaching promos to a season, tie-breaks) are precise enough that
an LLM applying them from prose will drift between runs.

## Decision

Split the pipeline by the kind of work:

- **Deterministic code:** fetching candidates from structured sources, picking release
  dates from typed data (TMDB release types per country), building rows, splitting,
  companion placement, sorting and tie-breaks. All unit-tested.
- **LLM, with structured outputs validated by Pydantic:** judgment calls that structured
  data cannot answer: is this short canon, semi-canon or excluded? which season was this
  promo made for? which continuity does an ambiguous title belong to?

## Consequences

- The rule engine can be tested exhaustively, including against every gold file's rows.
- The LLM's job is small and measurable, so model comparisons isolate model quality.
- The "D − rules" ablation measures what this decision is worth.
- More code to write than a single prompt; worth it because it is the part interviewers
  and users can trust.
