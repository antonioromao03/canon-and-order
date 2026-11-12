# Evaluation Protocol

The headline comparison is the hybrid pipeline against LLM-only baselines on held-out
universes, scored on **works** (completeness, dates, citations) and **rows** (rules,
order), with extras reported separately from films and seasons.

## Gold Set

- v1: 12 universes, frozen at the cut-off date 2026-11-30. Predictions are filtered to
  the same date before scoring.
- **Dev** (4): Breaking Bad (2008), The Dark Knight (2008), Spider-Man (2002),
  Schindler's List (1993). Breaking Bad and The Dark Knight appear as examples in the
  product spec, so they can never be test universes.
- **Test** (8): 12 Angry Men (1957), The Godfather (1972), Dune (2021), The Matrix (1999),
  Sherlock (2010), Wednesday (2022), The Lord of the Rings (2001), Alien (1979).
- A **resolution probe set** ([gold/probes.yaml](../gold/probes.yaml)) of 16 inputs
  (misspellings, missing or wrong years, duplicates, other continuities, titles with no
  screen adaptation). Each expects a gold universe, a duplicate of one, a universe
  outside the gold set (`other`) or "not found", and shares the split of the universe it
  names.
- Annotated with [gold/ANNOTATION_GUIDE.md](../gold/ANNOTATION_GUIDE.md); versioned in
  [gold/CHANGELOG.md](../gold/CHANGELOG.md). Only `status: verified` files are scored.

## Matching

Titles are normalised and may match listed aliases. Normalisation removes case, accents,
apostrophes (so "Schindler's" gives "schindlers"), other punctuation (replaced by a space),
a leading "the", "a" or "an", and a trailing bracketed year such as "(2002)". It turns
Roman numerals 1–39 (those written with I, V and X) into digits; larger ones are left
alone, because they would turn words such as "mix" into numbers. Other bracketed text is
kept, since it can be the only difference between two works.

A gold work and a predicted work are a candidate pair when all three hold:

1. Their kinds are in one group: **film** (feature film, TV movie), **series** (TV season,
   miniseries) or **extra** (TV special, TV episode, short, web series, promotional
   content).
2. For some pair of their names (title or alias), the numbers in the two normalised names
   agree, as a sorted multiset (the **number guard**). `token_set_ratio` scores
   "Spider-Man" vs "Spider-Man 2" at 100, so without the guard an invented sequel could
   match a missed original. A gold alias without numbers lets a prediction that omits a
   range ("Original Minisodes") match.
3. On such a pair of names, rapidfuzz `token_set_ratio` is at least the threshold (85; a
   score equal to the threshold matches).

Candidates are assigned one-to-one with the Hungarian algorithm (scipy
`linear_sum_assignment`), maximising total similarity. `token_set_ratio` also gives 100
when one title's words are a subset of the other's ("Spider-Man" vs "Spider-Man: No Way
Home", "The Dark Knight" vs "The Dark Knight Rises"), which leaves ties that can pair works
crosswise. The assignment weight is therefore `token_set_ratio + ratio / 1000`: plain
ratio breaks ties in favour of the closer title, and the nudge (at most 0.1) cannot
override a clearer `token_set_ratio` difference. Results are also reported at thresholds
80 and 90. Fifty matches are audited by hand to measure the matcher itself.

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
| Resolution accuracy | Inputs | Expected outcome on the probe set (universe, duplicate, other, not found), by category |
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
