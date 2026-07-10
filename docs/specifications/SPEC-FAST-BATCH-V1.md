# SPEC-FAST-BATCH-V1 — Fast Batch Runtime Profile and Quality Assessment

Status: **RETIRED** — Q4 adjudication ratified by the operator
2026-07-10 (`20260710-q4-fast-batch-adjudication`): quality-equivalent
to the `qc_filter: off` baseline, observed end-to-end gain modest, the
performance pathology was the conditioner rather than the RNG.
`fast_batch_v1` is never schema-accepted; `fast_batch_v0` remains a
closed, labeled spike. Reopening condition pinned in the Q4 package
(production refill-path profiling on wepp1). Retained as the design
study of record; no implementation is authorized by this document.
(Previously: draft rev 2 — re-anchored under
[ADR-0002](../decisions/0002-quality-metrics-authority.md).)
Surface: the proposed `generation_profile: fast_batch_v1` value in an
`inp.yaml` rev-1 runspec, its required CLI-header declaration, and the
quality evidence required before any recommendation.

> Rev 2 (2026-07-10): the rev-1 "stochastic parity to faithful"
> assessment is superseded. Authority for extension quality is the
> SPEC-QUALITY-REPORT vector against the `.par` contract and observed
> climate (ADR-0002); distance to faithful output is reported
> compatibility information, never a gate. The rev-1 internal QC-policy
> fork is superseded by the orthogonal `qc_filter` runspec knob.

## Purpose and authority

`fast_batch_v1` is a proposed non-faithful extension that replaces the
monthly random-array refill backend. It is a **performance and
parallelism** play, deliberately decoupled from the conditioning
question: QC policy is owned by the orthogonal `qc_filter` runspec
knob (SPEC-GENERATION-PROFILES), which composes with every backend
including faithful. It does not alter the authority of the vendored
Fortran: `faithful_5_32_3` remains the default source-authority
profile under ADR-0001, and quality authority for this and every
extension is the ADR-0002 metric vector.

The draft supersedes neither the implemented `fast_batch_v0` spike nor the
current runspec schema. `fast_batch_v1` must be rejected until an
implementation package ratifies this document, updates
SPEC-GENERATION-PROFILES and SPEC-RUNSPEC, adds the schema value, and emits
the declared provenance marker.

## Runtime selection and provenance

The runtime selector is the existing top-level `inp.yaml` field:

```yaml
generation_profile: faithful_5_32_3  # default and faithful
# or, after this draft is ratified and implemented:
generation_profile: fast_batch_v1
```

There is no unversioned `fast_batch` value. The exact profile name is part of
run identity: it commits the random backend, state derivation, mask semantics,
and assessment corpus. An implemented v1 output must append
`--generation-profile fast-batch-v1` to the CLI header command echo. It must
not be selectable by environment, host, build feature, or an implicit
fallback.

The first v1 implementation package must state whether it retires v0 from the
public schema or leaves v0 temporarily available as a clearly experimental
spike. It must never reinterpret a v0 run as v1.

## Proposed v1 backend contract

These are the required behavioral boundaries for a v1 candidate. The exact
PRNG and QC policy are open decisions below and must be ratified before code.

- The backend owns only the existing monthly `Crandom3State.ranary` refill
  seam. Faithful `ranset` remains unchanged and available to
  `faithful_5_32_3`.
- The source `rng.burn` initialization remains at the runspec boundary. The
  v1 state derivation begins from the post-burn, post-warm seed surface and is
  published as part of the profile. It retains at least four independently
  domain-separated state lanes; it must not repeat v0's single 64-bit seed
  funnel.
- The backend may use portable batch/vector-friendly operations, but neither
  profile may use fast-math, float-reordering, unsafe SIMD, or a host-specific
  implicit algorithm.
- Produced uniform values are finite f32 values strictly inside `(0, 1)`.
  The profile tests must establish repeatability for a fixed runspec and
  profile version.
- The refill preserves the source's conditional support, not merely its 9 by
  31 storage shape. Parameter 5 (one-based, precipitation amount) is zero on
  days the batch-side wet/dry `ell` chain calls dry and is an open-interval
  uniform on wet days. Parameter 9 (time to peak) is zero when parameter 5 is
  zero and on every observed-mode (`iopt = 6`) day; otherwise it is an
  open-interval uniform.
- The `ell` chain starts and advances with the source-compatible meaning
  (1 = preceding day wet, 2 = dry). The existing daily `bk7.v7 == 0.0`
  recovery remains reachable; v1 must instrument its occurrence rather than
  silently removing that branch. The source and daily chains may still
  desynchronize because they consume different random streams, so this is an
  attention cell, not an assertion that recovery is impossible.
- February and other short-month handling follows the source-visible `dimi`
  count. A vector implementation may write padded matrix slots, but no daily
  behavior may depend on them; short-month slots are assessed explicitly.

`fast_batch_v0` fills every slot with a nonzero uniform and consequently
violates the parameter-5/9 support rules above. It remains useful only as the
completed performance spike.

## Source QC that v1 must characterize

Faithful `ranset` does not apply a simple independent monthly filter. For each
parameter and calendar month it accumulates accepted draws across the run and
retries a candidate month attempt when any applicable check exceeds its
threshold (`reference/cligen532/cligen.f:4002-4340`).

| Source check | Applies to | Failure condition |
|---|---|---|
| 20-bin K-S uniformity | All parameters except observed-mode parameter 9, which bypasses statistics | Once cumulative nonzero count is at least 100, reject when the maximum cumulative-bin deviation divided by `sqrt(n)` exceeds `0.8276`. |
| Standard-normal mean confidence | Parameters 2–5; parameter 5 includes wet days only | Run only after K-S passes; reject when `conflm`'s confidence level exceeds source `thresh(j)`. |
| Standard-normal variance confidence | Parameters 2–5; parameter 5 includes wet days only | Run only after K-S passes; reject when `confls`'s two-sided confidence level exceeds source `thres2(j)`. |

The transformed-normal tests use the source's rolling predecessor state.
On a failed attempt, `ranset` removes its statistical contribution and
restores the parameter's predecessor state (and precipitation `ell`), but the
already-consumed source RNG draws stay consumed. Its retry count is shared
within the call and stops retrying after 10,000 failures.

The source's commented-out chi-square call is not a live acceptance check.
The table describes the actual K-S / mean / variance path, not a new quality
standard.

## QC policy — owned by the orthogonal `qc_filter` knob

Rev 1 forced a v1-internal choice between batchwise acceptance and
diagnostic-only QC. Both halves now live elsewhere:

- **Conditioning** is the `qc_filter` runspec field
  (SPEC-GENERATION-PROFILES): `faithful` applies the source-shaped
  acceptance/retry protocol to whichever backend is active; `off`
  disables conditioning. v1 must compose with both values, and the
  composition (`fast_batch_v1` × `qc_filter: faithful`) must specify
  retry semantics, cap, and state rollback exactly if implemented.
- **Diagnostics** are standing SPEC-QUALITY-REPORT group-P metrics for
  every run: when conditioning is off, the faithful K-S / mean /
  variance verdicts are evaluated counterfactually over produced
  batches and their would-have-been-rejected rate is reported.
  Diagnostic evaluation must not mutate generation state or the
  output path.

Note the ordering consequence: `qc_filter: off` on the **faithful**
backend keeps `RANDN`, the per-parameter streams, the column-5/9
masks, and the `ell` chain source-shaped while removing the retry
loop and its per-draw normal-deviate accumulation — the dominant
measured cost of the pathological cells. That configuration is both
the QC ablation experiment and, plausibly, most of the fast-batch
speedup. v1's performance case must be made against it, not against
conditioned faithful.

## Quality assessment (supersedes rev-1 stochastic parity)

The goal is a bounded statement per ADR-0002: *for this declared
configuration, corpus, and horizon, the SPEC-QUALITY-REPORT vector
against the `.par` contract and observed climate satisfies its
pre-registered bounds*. Distance to faithful output is reported as
compatibility information and is never an acceptance criterion — a
configuration may beat faithful on group-B interannual metrics and
that is a result, not a violation.

### Matrix

Adjudication runs 30- **and** 100-year horizons over at least:
`faithful_5_32_3` (conditioned), `faithful_5_32_3` + `qc_filter: off`
(the ablation), and `fast_batch_v1` under its proposed `qc_filter`
default. Reports' per-decade group-A/group-B blocks give the
convergence-versus-variability frontier at both horizons.

### Pre-registration and corpus

Unchanged from rev 1 in substance: before the assessment run, record
profile source revision, binary hash, runspecs, `.par` hashes,
host/compiler provenance, burn values, years, and the
`metrics_version`. `rng.burn` is a draw-discard count, not an
independent seed; burn strata must not be reported as unqualified
independent replicates. The corpus combines the fixture stations with
production-collection regimes (at least arid, humid, cold, and
monsoonal), preceded by a production invocation and burn-distribution
characterization. Station list and burn sweep are fixed before
results are seen.

### Attention cells

Mandatory regardless of headline metrics: parameter-5 dry/wet masks,
parameter-9 zero masks (especially observed mode), first wet day
after a dry chain, `bk7.v7 == 0.0` recovery count, group-P
counterfactual verdicts, and short-February / padded-slot handling.

### Bounds and decision rule

Bounds are pre-registered per metric cell with provenance for each
bound (`.par` quantization response measured by one-quantum
perturbation; consumer sensitivity per Srivastava et al. 2019; source
QC thresholds may inform group-P interpretation but are mechanistic
screens, not automatic climate-output bounds). Report effect sizes
and intervals, never bare p-values. Failures are results that
identify the next refinement; they do not license tolerance widening
after the comparison is seen.

## Sequencing and non-goals

Evidence order under ADR-0002:

1. Implement SPEC-QUALITY-REPORT (the instrument precedes everything).
2. Implement `qc_filter` (SPEC-GENERATION-PROFILES) with faithful
   golden identity untouched under `qc_filter: faithful` defaults.
3. Run the dissection matrix (faithful vs `qc_filter: off`, 30/100
   years) — this prices the QC filter and re-baselines performance.
4. Only if v1's batching still buys material performance over
   `faithful + qc_filter: off` on FMA-capable production hardware
   (`wepp1`, pinned-core repeated samples), ratify this spec's backend
   contract and implement v1.
5. Only then dispatch the pre-registered quality assessment above.

The draft does not change faithful code, assert any quality claim for
v1, approve a bare `fast_batch` alias, or authorize a production
default change.
