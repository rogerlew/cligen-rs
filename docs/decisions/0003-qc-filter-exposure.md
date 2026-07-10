# ADR-0003: `qc_filter` Is User-Facing; Conditioning Is a Declared Per-Use-Class Choice

Status: **Accepted** — operator ratification 2026-07-10 ("ratify
both"), on the R1-amended record. Drafted by Claude Code from the Q3
dissection evidence; amended same-day per the Codex R1 review (all
five amendments applied; review + dispositions in
`docs/work-packages/20260710-q3-qc-filter-dissection/artifacts/`).
Deciders: Roger Lew (operator)
Evidence: `docs/work-packages/20260710-q3-qc-filter-dissection/`
(ratified pre-registration, 102-run matrix, frontier analysis).

## Context

ADR-0002 ruling 3 decomposed generation policy into orthogonal knobs
and left the exposure question to this adjudication: is the Meyer QC
conditioner a user-facing policy, and is conditioning opt-in or
opt-out per use class? The Q3 dissection measured it against
pre-registered bounds: ~52% of off-trajectory batches fail the raw
counterfactual QC verdicts in every climate regime (faithful
execution retries and discards substantially more attempts on
pathological stations — corpus median failed-attempt fraction ≈ 97%
at 100 yr); the convergence benefit is real, and its horizon
dependence is estimator-sensitive (B1 = 1.25/1.12 under the recorded
aggregation, 1.44/1.41 under all-cells — the pre-registration pinned
the threshold but not the aggregation hierarchy, an R1 finding); the
interannual-variability cost is material at both horizons and, in
this single-burn Daymet comparison, output moves **away** from
observed climate on 15/17 corpus stations (detrended 14/17; GHCN
secondary 6/8); conditioning is the dominant generation cost (1.7×
median, 8.8× corpus-total, with 908 QC give-up events at 100 yr
meaning conditioning is not even uniformly applied).

## Decision

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
   mechanism): 30-year agricultural runs keep the default; for
   100-year variance-priority hydrology runs (the WEPPcloud native
   use class — "native" here names the use class, not the future
   `native-f64-v1` profile), **consider `qc_filter: off` and inspect
   the emitted quality report** — the variability cost of
   conditioning is material at that horizon while the size of its
   remaining convergence benefit is estimator-sensitive. Not claimed
   universally correct for every rangeland/forest run; wepppy
   adoption is wepppy's decision, made visible by the quality report
   rather than argued from this ADR.
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
