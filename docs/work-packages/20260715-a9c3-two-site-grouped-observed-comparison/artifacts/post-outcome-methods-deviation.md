# A9c3 post-outcome methods deviation

Status: outcome-time reporting correction; terminal preserved

Date: 2026-07-15

## Short-screen engineering horizon

The design freeze defines short-screen scientific evidence as the 30-year
prefix from each nested 100-year candidate stream. The implementation computed
the 30-year climate objectives from that prefix, but `candidate_cache`
validated calendar and physical support over the complete 100-year stream and
passed that result into the short-stage hard invariant. Consequently, the six
recorded `eng_calendar_and_support` distances, totaling 609,654 violations,
are 100-year-stream totals and must not be described as 30-year totals.

This deviation does not change promotion or the terminal. Every one of the 240
candidate attempt records retains at least one indexed physical-support
violation within its first 112 generated days; the largest first retained
violation index is 111. All 240 therefore also fail the frozen 30-year-prefix
support invariant. Exact 30-year violation totals cannot be reconstructed
because generated streams were reduced after scoring and each attempt retains
only its first 100 violation labels.

The corrected interpretation is:

- six configurations entered the registered 30-year scientific screen;
- all 240 configuration/site/burn prefixes had a physical-support failure;
- no configuration could advance under the hard-failure rule;
- the 609,654 value describes validation of the parent 100-year streams, not
  the 30-year prefixes; and
- `HOLD-A9C3-NO-SELECTABLE-CANDIDATE` remains the registered terminal.

No threshold, fit, score, candidate identity, station, burn, outcome artifact,
or confirmation access state was changed after outcome access.

## Monthly-reconciliation wording

The fit records report `pass` under an uncertainty-aware Monte Carlo rule that
uses independent target and heldout draws and a 3.290527-standard-error
allowance in addition to absolute and relative tolerances. Some maximum
relative discrepancies are much larger than 0.5 percent because the Monte
Carlo allowance controls those checks. The report therefore describes the
result only as a recorded uncertainty-adjusted reconciliation pass. It does
not claim agreement within 0.5 percent.

Per-month-length moments, standard errors, and applied tolerance values are
hash-bound inside each reconciliation identity but were not persisted in the
canonical fit records. Independent numeric recomputation requires rerunning
the deterministic reconciliation implementation.
