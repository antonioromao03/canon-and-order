# Evaluation Protocol

The headline comparison is the hybrid pipeline against LLM-only baselines on held-out
universes, scored on **works** (completeness, dates, citations) and **rows** (rules,
order), with extras reported separately from films and seasons.

## Gold Set

- v1: 12 universes, frozen at a cut-off date (proposed 2026-11-30). Predictions are
  filtered to the same date before scoring.
- **Dev** (4): Breaking Bad (2008), The Dark Knight (2008), The Godfather (1972),
  Schindler's List (1993). Breaking Bad and The Dark Knight appear as examples in the
  product spec, so they can never be test universes.
- **Test** (8): Spider-Man (2002), Battlestar Galactica (2004), Toy Story (1995),
  The Matrix (1999), Alien (1979), Stranger Things (2016), The Lord of the Rings (2001),
  12 Angry Men (1957).
- A **resolution probe set** of about 15 inputs (misspellings, missing or wrong years,
  duplicates, a title with no screen adaptation) with expected outcomes.
- Annotated with [gold/ANNOTATION_GUIDE.md](../gold/ANNOTATION_GUIDE.md); versioned in
  [gold/CHANGELOG.md](../gold/CHANGELOG.md). Only `status: verified` files are scored.

## Matching

Titles are normalised (case, punctuation, leading articles, Roman numerals) and may match
listed aliases. Candidate pairs need a compatible kind group (film, series, extra) and are
scored with rapidfuzz `token_set_ratio`; pairs are assigned one-to-one with the Hungarian
algorithm at threshold 85, with results also reported at 80 and 90. Fifty matches are
audited by hand to measure the matcher itself.

## Metrics

| Metric | Level | Definition |
| --- | --- | --- |
| Precision, recall, F1 | Works | One-to-one matches; micro and macro; core vs extras; by canon status |
| Invented-entry rate | Works | Unmatched predictions adjudicated as not existing ÷ predictions |
| Exact-date accuracy | Works | Predicted date equals gold at gold's precision |
| Date within ±3 days | Works | Day-precision gold only |
| Precision overclaim rate | Works | Prediction more precise than the gold can support |
| Order | Rows | Kendall tau-b over matched rows; share of universes with the exact sequence |
| Rule compliance | Checks | Pass rate of each gold file's `checks`, per rule |
| Citation support rate | Works | Cited snapshot contains title and date (automated; 30 audited by hand) |
| Resolution accuracy | Inputs | Correct universe, "not found" or duplicate on the probe set |
| Cost, latency, tokens | Runs | Mean, p50, p95 per universe; shadow cost at list prices |

Unmatched predictions are adjudicated as *invented*, *real but out of scope*, or *gold
missed it*. The last case fixes the gold set (new version) rather than counting as an error.

## Approaches

| ID | Approach | When |
| --- | --- | --- |
| A | Closed-book: rules prompt + title → JSON timeline | v1 |
| B | A + one Wikipedia article (franchise or series) in context | v1 |
| D | Hybrid pipeline (sources → classify → verify → rule engine) | v1 |
| D − rules | Hybrid, but the LLM builds rows and order | v1 |
| D − verify | Hybrid without verification | backlog |
| C | Agentic web search (search and fetch tools) | backlog |

Models: gpt-oss-120b on Groq (open-weight) and Gemini 3.5 Flash-Lite (free tier).
v1 matrix: A, B and D on both models, plus D − rules on the better one.

## Procedure

1. Temperature 0 where supported. D runs 3 times per model; others once.
2. Every run stores git SHA, gold version, prompt versions, model ID, provider, date and
   raw responses.
3. Gold works released after each model's knowledge cutoff are tagged; recall on them is
   reported separately (contamination check).
4. Differences between approaches use a paired bootstrap over test universes (10,000
   resamples, 95% intervals), with the per-universe table alongside.
5. Fifty errors are labelled by type (missed extra, wrong continuity, date off, split
   error, invented entry) and fed into the backlog.

## CI

A smoke test replays recorded LLM and HTTP responses for two dev universes, with no
network and no keys, and asserts the metrics equal the recorded values exactly. The full
evaluation runs manually; results are committed under `eval/results/` and a script
regenerates the README table.
