# Fast-Batch Promotion Adjudication — Recommendation

Date: 2026-07-10
Author: Claude Code (executor); decision is the operator's
(ADR-0002: "No production default change without a separate operator
decision"; ROADMAP Q4: promotion or retire-with-record).
Evidence mode: **Ran** — all numbers from the Q3/Q4 matrix
(`../20260710-q3-qc-filter-dissection/artifacts/matrix-analysis.json`,
`timing-no-sidecar.json`), gate pre-pinned in the ratified
pre-registration before any run.

## Recommendation

**Retire the fast-batch line.** SPEC-FAST-BATCH-V1 should not be
ratified; `fast_batch_v1` should never enter the runspec schema;
`fast_batch_v0` stays a closed, labeled spike.

## Why

1. **The observed gain is modest, and the pinned gate could not be
   evaluated as registered** (amended per R1 finding 2: whole-run
   wall time is a proxy for the pinned refill-path quantity; wepp1
   was not measured; verdict recorded as NOT EVALUATED AS
   PRE-REGISTERED, not FAIL). What was measured: against the honest
   baseline — `qc_filter: off` on the faithful backend — the RNG swap
   shows 1.32× generation-only (1.24–1.27× wall) at 100 years on this
   host. The dominant cost was never `RANDN`; it was the conditioner
   (faithful → off: 1.70× median, 8.8× corpus-total, up to 2.5M
   discarded batch attempts on a single 100-year arid run). This is a
   portfolio judgment on modest observed benefit, not a technical
   impossibility proof.
2. **Quality equivalence is not an argument for promotion.** v0
   passes legs (a) and (b) — convergence within 2.3% of the off
   baseline, dispersion ratio 0.95 — i.e., it is statistically
   interchangeable with the source-shaped unconditioned generator. A
   replacement that is neither faster (materially) nor better has no
   claim under ADR-0002's authority vector, and carries real costs:
   declared distributional divergences (dropped column-5/9 masks,
   dead `v7` recovery path), a second RNG lineage to maintain, and a
   provenance surface that must forever explain itself.
3. **The quality frontier work lies elsewhere.** Both v0 and off
   still underdisperse against observed climate in the arid cells
   (CV 0.47–0.51 vs observed 0.61 at Death Valley) — that is the
   ADR-0002 layer-3 structural gap (radiation–wetness coupling,
   interannual variance mechanisms), which is model augmentation
   (A5), not RNG engineering. Every dollar spent on batch RNG work
   would be spent on the wrong layer.

## What is preserved

- `fast_batch_v0` remains implemented and schema-accepted as the
  labeled experimental spike it always was (regression value for the
  refill seam; reproducibility of the perf-arc record). Its reports
  carry `qc_filter: null` and no counterfactual surface
  (SPEC-QUALITY-REPORT rev 5 ruling).
- The perf-arc packages and SPEC-FAST-BATCH-V1 stay in the record as
  the design study that led here; the spec's registry row should read
  "retired (Q4 adjudication)" upon operator ratification.
- The wepp1/FMA question is **unmeasured** (R1 finding 2): all
  timing is this host; no refill-path isolation, raw repetitions, or
  pinned-core methodology was run. The reopening condition in
  `package.md` names exactly what a future case must measure.

## If the operator instead wants the batch line

The honest path would be a v1 spec re-scoped as a *quality* project
(reproduce the source column semantics exactly, compose with
`qc_filter`, and demonstrate a measured gain on whatever host class
production actually uses) — but nothing in this matrix suggests the
gain exists to be found.
