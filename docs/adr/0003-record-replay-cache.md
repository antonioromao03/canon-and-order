# 0003. One record/replay cache for every external call

- Status: accepted (implementation in week 3)
- Date: 2026-11-06

## Context

The pipeline calls TMDB, Wikimedia and LLM providers. Production needs caching for cost;
CI needs deterministic runs with no keys or network; evaluations must be reproducible
after a free model is withdrawn or a page changes.

## Decision

All HTTP and LLM calls go through one cache keyed by a hash of the request (provider,
model, prompt version, messages, schema, or URL and parameters), with three modes:

- `live`: call and cache (production, development);
- `record`: call and store the response as a fixture (before committing an evaluation);
- `replay`: serve stored responses only, and fail on a miss (CI, re-scoring).

## Consequences

- The CI evaluation smoke test is free and deterministic.
- Committed evaluation results can be re-scored after a metric fix without new API calls.
- Fixtures must stay small; only the smoke-test universes are committed.
