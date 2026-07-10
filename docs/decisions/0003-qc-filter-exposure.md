# ADR-0003: `qc_filter` Is User-Facing; Conditioning Is a Declared Per-Use-Class Choice

Status: **Proposed** — drafted by Claude Code from the Q3 dissection
evidence (2026-07-10); awaiting operator ratification.
Deciders: Roger Lew (operator)
Evidence: `docs/work-packages/20260710-q3-qc-filter-dissection/`
(ratified pre-registration, 102-run matrix, frontier analysis).

## Context

ADR-0002 ruling 3 decomposed generation policy into orthogonal knobs
and left the exposure question to this adjudication: is the Meyer QC
conditioner a user-facing policy, and is conditioning opt-in or
opt-out per use class? The Q3 dissection measured it against
pre-registered bounds: the conditioner discards ~52% of all batches
in every climate regime; its convergence benefit is material at the
30-year agricultural horizon (B1 = 1.25) and immaterial at the
100-year native horizon (B1 = 1.12); its interannual-variability cost
is material at both horizons and moves output **away** from observed
climate on 15/17 corpus stations; it is the dominant generation cost
(1.7× median, 8.8× corpus-total, with 908 QC give-up events at
100 yr meaning conditioning is not even uniformly applied).

## Decision (proposed)

1. **`qc_filter` is user-facing and stays.** It is a legitimate
   use-case choice, not an internal detail: convergence-priority
   (30-year agricultural planning) genuinely benefits; variance-
   priority (long-horizon native stochastic hydrology) is measurably
   harmed. The runspec surface implemented in Q3 (rev 5) is ratified.
2. **The default remains `faithful` (conditioning on).** Byte
   compatibility and no-silent-behavior-change outrank ergonomics;
   every unconditioned run must say so (`--qc-filter off` header
   marker, provenance, group P counterfactuals).
3. **Recommended practice, per use class** (recommendation, not
   mechanism): 30-year agricultural runs keep the default; 100-year
   native/rangeland/forest runs (WEPPcloud practice) opt into
   `qc_filter: off` — at that horizon conditioning buys nothing
   material and costs realistic year-to-year variability.
   wepppy adoption is wepppy's decision, made visible by the quality
   report rather than argued from this ADR.
4. **No production default change without a separate operator
   decision**, revisited after production experience with `off`
   reports (unchanged from ADR-0002).

## Consequences

- The faithful-mode retirement path (ADR-0002 ruling 4) is
  unaffected; `qc_filter: off` on the faithful backend is now the
  measured re-baseline for any future generation work (Q4 used it).
- The group-P counterfactual surface (metrics_version 2) is the
  standing instrument for auditing what conditioning would have
  discarded on any run.
- The B3 early-decade result (10/17) tempers the ADR-0002 prose: the
  cumulative-QC early-run distortion exists but is regime-dependent;
  30-year-horizon users should read their own report's `by_decade`
  blocks rather than assume the worst.
