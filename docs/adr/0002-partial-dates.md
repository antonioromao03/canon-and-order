# 0002. A PartialDate value type instead of datetime.date

- Status: accepted
- Date: 2026-11-06

## Context

Many release dates are known only to the month or year (the spec writes `??/03/2009`),
and the planned book universes need historical years (`c. 725 BC`). `datetime.date`
cannot represent either. Storing strings would push parsing and sorting into every caller.

## Decision

`PartialDate` stores `year` (negative for BC, no year 0), optional `month` and `day`, and
an `approximate` flag. It parses ISO forms, the spec's `DD/MM/YYYY` with `??`, and
historical forms; it sorts by the earliest day it could be, as the spec requires; and it
renders back to the spec's format.

## Consequences

- One type for screen and book dates, so books need no migration.
- Evaluation can measure "precision overclaim" (a predicted day where only the month is known).
- Centuries and ranges (`8th century BC`, `c. 1200 BC–AD 100`) are not supported yet; add
  them when the first book universe needs them.
