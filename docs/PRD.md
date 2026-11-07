# Product Requirements (One Page)

## Problem

People starting or catching up on a franchise want to watch everything official, in the
order audiences first saw it, without spoilers. Existing guides are curated for a handful
of franchises, list mostly films, skip shorts, webisodes and promos, and rarely cite where
a date came from.

## Users

- **Completionist viewer:** wants every official item, including extras, in release order,
  and to tick them off.
- **Catch-up viewer:** wants to know what to watch before a new release, and what is coming.

## Jobs to be Done

1. "Give me every official screen release in this universe, in release order, with sources."
2. "Show me what I have watched and what is left."
3. "Tell me what has been announced and when it is due."

## v1 Scope

Title + year in; a cited, rule-compliant timeline out; watched ticks and progress in the
browser; upcoming releases; a demo with precomputed showcase universes and a daily budget
for new research runs.

**Non-goals for v1:** in-universe chronological order (subjective), streaming availability,
ratings, synopses, accounts, notifications, books.

## Metrics

Targets are set after the first baseline (week 3), not guessed now.

| Area | Metric | Source |
| --- | --- | --- |
| Quality | Extras recall and invented-entry rate on the test set | Evaluation |
| Quality | Share of entries with a verified citation | Evaluation and run log |
| Speed | Time to timeline (p50, p95) for a medium universe | Run log |
| Cost | Shadow cost per universe (tokens × list price) | Run log |
| Efficiency | Share of entries resolved without an LLM call; cache hit rate | Run log |
| Usage (later) | Universes added, ticks per session, returning visitors | App analytics |

## Guardrails

- No plot details beyond each title's basic premise.
- Daily research budget and per-IP rate limit on the public demo.
- TMDB attribution; gold data licensed CC BY-SA 4.0.

## Roadmap

| When | Milestone |
| --- | --- |
| 9 Nov – 20 Dec 2026 | v1: pipeline, evaluation (12 gold universes), API, UI, live demo |
| Late Dec | Monthly monitor opening review pull requests; "report a problem" |
| Jan – Feb 2027 | Large-franchise slice, agentic-search baseline, gold set to 20, error analysis |
| Mar 2027 | Accounts and synced watched lists; RSS/iCal feed of upcoming releases |
| Apr 2027 | Books; gold set to 30; write-up |
