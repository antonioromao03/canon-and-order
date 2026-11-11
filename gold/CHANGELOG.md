# Gold Set Changelog

Every change to a file in `gold/universes/` gets a line here. Evaluation results record
the gold version they were scored against, so a correction never silently changes old
numbers.

## v1 (2026-11-10)

Twelve verified universes (4 dev, 8 test) and the resolution probe set, cut-off
2026-11-30. After the cut-off, check the twelve universes for releases between
2026-11-10 and 2026-11-30; if any, add them and release v1.1.

- 2026-11-06: schema v1, template and annotation guide.
- 2026-11-06: `the-dark-knight-2008` added as a draft seeded from the artifact timeline (unverified).
- 2026-11-08: `the-dark-knight-2008` verified (dev): piece dates 2–4 added, citations added to every work, stale draft notes removed.
- 2026-11-08: `breaking-bad-2008` added and verified (dev), seeded from a draft: citations checked, parents and companion rows settled, checks trimmed to five.
- 2026-11-08: `spider-man-2002` added and verified (dev), annotated from scratch (no draft seed): the baseline for the draft error rate.
- 2026-11-09: `schindlers-list-1993` added and verified (dev), seeded from a draft: citations and dates checked, stale draft note removed.
- 2026-11-09: `12-angry-men-1957` added and verified (test), seeded from a draft: citations and dates checked; opening-day date_conflict flagged.
- 2026-11-09: `the-godfather-1972` added and verified (test), seeded from a draft: citations and dates checked; first-run date_conflict flagged on the first two films.
- 2026-11-10: `dune-2021` added and verified (test), seeded from a draft: citations and dates checked; HBO Max early-access date_conflict flagged on the first film.
- 2026-11-10: `the-matrix-1999` added and verified (test), seeded from a draft: citations and dates checked; Animatrix split around The Matrix Reloaded, with piece 5 date unconfirmed.
- 2026-11-10: `sherlock-2010` added and verified (test), seeded from a draft: citations and dates checked; unaired pilot kept as a semi-canon work.
- 2026-11-10: `wednesday-2022` added and verified (test), seeded from a draft: citations and dates checked; Season 2 split into two parts as Netflix presented it.
- 2026-11-10: `the-lord-of-the-rings-2001` added and verified (test), seeded from a draft: citations and dates checked; War of the Rohirrim treated as canon.
- 2026-11-10: `alien-1979` added and verified (test), seeded from a draft: citations and dates checked; Prometheus viral videos and Covenant shorts split around their films.
- 2026-11-10: annotation guide: limited public runs and early streaming openings count as the release date; `before` checks of plain date order use `rule: sorting`; `upcoming` lists only officially announced titles. All twelve files already follow these.
- 2026-11-10: `the-dark-knight-2008`: source added for Gotham Tonight's Comcast On Demand debut.
- 2026-11-10: `spider-man-2002`: Across the Spider-Verse exclusion reason corrected (archival footage of Maguire's Spider-Man, film not specified); Brand New Day checked: Maguire is not in its cast list.
- 2026-11-10: `schindlers-list-1993`: Shoah Foundation featurette renamed to its disc title; 1994 reissue confirmed by AFI.
- 2026-11-11: annotation guide: a companion row is any parented work whose release span overlaps its season's run, including single shorts and all-at-once releases (matches the existing `breaking-bad-2008` rows); supplementary content never splits a miniseries either. `breaking-bad-2008`: note on companion rows reworded to match; no rows changed.
- 2026-11-10: `12-angry-men-1957`: weak cordcuttersnews citation removed; Juror 8 reason corrected (loosely based on 12 Angry Men).
- 2026-11-10: `the-godfather-1972`: order check moved to `rule: sorting`; Connie novel note sourced and corrected (rights held, no film announced); unsourced "lightly edited" claim removed.
- 2026-11-10: `dune-2021`: order check moved to `rule: sorting`; unconfirmed producer name removed; Prophecy Season 2 `expected` changed from "2026" to "TBA" (no date announced).
- 2026-11-10: `sherlock-2010`: order check moved to `rule: sorting`; Wikipedia mirror links replaced with Wikipedia; unsourced 25 December claim removed.
- 2026-11-10: `wednesday-2022`: order checks moved to `rule: sorting`; TikTok exclusion reason corrected (social post); Season 3 wrap sourced.
- 2026-11-10: `the-lord-of-the-rings-2001`: present check added for The War of the Rohirrim; mirror link replaced with Wikipedia; Shadow of the Past announcement sourced.
- 2026-11-10: `alien-1979`: order check moved to `rule: sorting`; Prometheus viral video 5 moved into the first row (videos 1–5), since its month-only date sorts before the film.
- 2026-11-10: resolution probe set added (`gold/probes.yaml`, 16 probes) with its schema and validation.
- 2026-11-10: draft error rate dropped for v1: the draft-seeded files recorded no error counts.
