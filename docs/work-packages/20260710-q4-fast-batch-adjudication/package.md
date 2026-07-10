# Q4 — Fast-Batch Comparison + Promotion Adjudication

Status: `EXECUTED-COMPLETE` — **closes ROADMAP item Q4 and the
quality arc.** Comparison analyzed against the pre-pinned gate
(quality legs pass; performance leg not evaluable as registered — R1
finding 2); **retirement ratified by the operator 2026-07-10** as a
portfolio decision with the pinned reopening condition.
SPEC-FAST-BATCH-V1 → RETIRED; `fast_batch_v0` stays a closed spike.
Date: 2026-07-10
Evidence mode: **Ran** (shares the Q3 matrix evidence:
`../20260710-q3-qc-filter-dissection/artifacts/`)

## Objective

Close ROADMAP Q4: same-instrument comparison of
{faithful, faithful + qc_off, fast_batch_v0} on the ratified Q3
corpus at 30/100 years, the performance case against the Q3 qc_off
re-baseline, and the promotion adjudication for the fast-batch line
(SPEC-FAST-BATCH-V1) with pre-registered bounds.

## Method

- The comparison matrix ran inside the Q3 campaign (102 runs; the
  fast-v0 column is 34 of them). The promotion gate was **pre-pinned
  in the ratified Q3 pre-registration** (§Bounds, "Q4 promotion
  gate") before any output existed.
- **Legacy-Fortran column**: cligen-rs faithful mode ≡ the pinned
  legacy binary byte-for-byte (12/12 goldens through the binary,
  ~46M bit-identical interior records, and Q1's post-hoc
  measurements of raw legacy production `.cli` files). The faithful
  column therefore *is* the legacy column; no separate Fortran runs
  were executed (equivalence Ran previously, cited — not re-run).
- Performance: generation-only timing (`output.quality: false`,
  best-of-3, 100 yr, 17 stations) isolates the generator from the
  sidecar cost.

## Result against the pre-pinned gate (both horizons)

| Gate leg | Bound | 30 yr | 100 yr | Verdict |
|---|---|---|---|---|
| (a) group A quality vs off | median rel-err ratio ≤ 1.1 | 1.023 | 1.021 | **pass** |
| (b) group B dispersion vs off | SD ratio in [0.9, 1.15] | 0.953 | 0.953 | **pass** |
| (c) performance vs off | ≥ 1.5× | 1.24× (with sidecar) | 1.32× generation-only | **NOT EVALUATED AS PRE-REGISTERED** (R1 finding 2: whole-run wall is a proxy for the pinned refill-path quantity; measurement configs differ between horizons; wepp1 was not measured; no raw timing samples retained) |

Leg (a) is additionally aggregation-sensitive (R1 finding 1: a
station-median estimator gives 1.104 at 30 yr, narrowly outside the
1.1 bound). What the measurements do establish: the batch line is
**quality-equivalent, and the observed end-to-end gain is modest** —
the pathological cost ADR-0002's perf arc attributed to the batch
problem was the *conditioner* (faithful → off is 1.70× median /
8.8× corpus-total on this host), not `RANDN` (off → v0 observed at
1.32× end-to-end; the refill-path-specific gain was not isolated).

## Recommendation (operator decides)

Retire the fast-batch line — **as a portfolio and maintenance
decision** (amended per the R1 review, whose independent opinion
concurs with retirement): the observed end-to-end gain is modest,
v0 carries declared semantic divergences, a source-support-preserving
v1 would cost real maintenance, and the quality frontier lies in
model augmentation (A5), not RNG work. This is **not** a proof that a
refill backend cannot exceed 1.5× on production hardware — leg (c)
was not evaluated as pre-registered. Reopening condition (pinned):
only if production profiling shows the unconditioned refill/RNG path
is a material bottleneck, beginning with direct refill benchmarks and
consistent pinned-core end-to-end measurements on wepp1.
SPEC-FAST-BATCH-V1 is not ratified, `fast_batch_v1` is never
schema-accepted, `fast_batch_v0` remains a closed spike. Full
rationale: `artifacts/promotion-adjudication.md`.

## Artifacts

- `artifacts/promotion-adjudication.md` — the recommendation and its
  evidence trail.
- Comparison data: the Q3 package artifacts (single campaign, one
  matrix).
