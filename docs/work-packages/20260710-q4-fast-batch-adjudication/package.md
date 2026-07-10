# Q4 — Fast-Batch Comparison + Promotion Adjudication

Status: `EXECUTED-AWAITING-OPERATOR-ADJUDICATION` — comparison run
and analyzed against the pre-pinned gate; **recommendation: retire
the fast-batch line** (`artifacts/promotion-adjudication.md`); the
promotion/retirement decision is the operator's per ADR-0002.
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
| (c) performance vs off | ≥ 1.5× | 1.24× (with sidecar) | **1.32× generation-only** | **FAIL** |

All three legs were required. The batch line is
**quality-equivalent but not performance-material** once the qc_off
re-baseline exists: the pathological cost ADR-0002's perf arc
attributed to the batch problem was the *conditioner* (faithful → off
is 1.70× median / 8.8× corpus-total), not `RANDN` (off → v0 is
1.32×).

## Recommendation (operator decides)

Retire the fast-batch line with this negative result on the record:
SPEC-FAST-BATCH-V1 is not ratified, `fast_batch_v1` is never
schema-accepted, and `fast_batch_v0` remains a closed spike (kept, as
shipped, for reproducibility of the perf-arc record). Rationale and
full numbers: `artifacts/promotion-adjudication.md`.

## Artifacts

- `artifacts/promotion-adjudication.md` — the recommendation and its
  evidence trail.
- Comparison data: the Q3 package artifacts (single campaign, one
  matrix).
