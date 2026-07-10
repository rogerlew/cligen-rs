# SPEC-FAST-BATCH-V1 — Fast Batch Runtime Profile and Parity Assessment

Status: draft — operator-directed iteration; no implementation is authorized
by this document
Surface: the proposed `generation_profile: fast_batch_v1` value in an
`inp.yaml` rev-1 runspec, its required CLI-header declaration, and the
evidence needed for a bounded stochastic-parity claim.

## Purpose and authority

`fast_batch_v1` is a proposed non-faithful extension that replaces the
monthly random-array refill backend. It is intended to preserve the source
daily-consumption shape while making random-number production batch-friendly.
It does not alter the authority of the vendored Fortran: `faithful_5_32_3`
remains the default source-authority profile under ADR-0001.

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

## QC policy — decision required before implementation

V1 must select one of these policies before code is written; neither may be
added silently after a benchmark:

1. **Batchwise acceptance:** maintain private, source-shaped QC state and
   resample a v1 batch until the source checks accept it. The retry semantics,
   retry cap, and state rollback must be specified exactly.
2. **Diagnostic-only:** run the same checks on private state, report their
   verdicts and counterfactual retry rate, but never alter v1 output or its
   state progression.

The first policy aligns more closely with the source filter but may reduce the
measured speedup. The second isolates the value of batching but makes QC
divergence a primary parity risk. In either case, diagnostic state must not
mutate faithful state or the output path. The v1 benchmark package must record
the chosen policy, retry/failure counts by parameter and month, and its timing
cost before any parity package is proposed.

## Stochastic-parity assessment strategy

The goal is a bounded statement: *for this declared v1 profile, corpus, and
statistics vector, differences are within pre-registered practical bounds*.
It is neither bit parity nor an unqualified claim of model equivalence.

### Pre-registration and corpus

Before the assessment run, record the profile source revision, binary hash,
runspecs, `.par` hashes, host/CPU and compiler provenance, burn values, years,
and exact statistic implementation. `rng.burn` is a draw-discard count, not
an independent random seed; burn strata must therefore not be reported as
unqualified independent replicates.

The corpus must combine the existing fixture stations with additional station
regimes selected from the production collection (at least arid, humid, cold,
and monsoonal or another documented regime partition). A production invocation
and burn-distribution characterization precedes final sample-count selection,
because the current 12-fixture benchmark is an edge-coverage matrix rather
than a representative workload. The assessment records a fixed station list
and a fixed burn sweep before results are seen.

### Measurements

For each station, month, and declared burn/year block, retain these primary
statistics:

- wet-day fraction, `P(wet | wet)`, and `P(wet | dry)`;
- conditional wet-day amount mean, standard deviation, skew, and declared
  quantiles;
- maximum/minimum temperature, radiation, wind, and dew-point mean, standard
  deviation, and declared quantiles;
- storm duration, time-to-peak, and peak-intensity distributions; and
- annual/seasonal precipitation, storm count, and maximum daily
  precipitation.

The mandatory attention cells are parameter-5 dry/wet masks, parameter-9
zero masks (especially observed mode), first wet day after a dry chain,
`bk7.v7 == 0.0` recovery count, QC diagnostic outcomes, and short-February
or short-month padded slots. Report them even when downstream output makes a
cell appear unchanged.

### Bounds and decision rule

Source QC thresholds are mechanistic screens, not automatically acceptable
bounds on climate outputs. Likewise, `.par` quantization may inform a
resolution floor but cannot be assumed to bound a statistic without measuring
that station/statistic's response to one-quantum perturbations. A pilot may
estimate variability and the quantization response; it must not be used to
choose bounds after viewing the final v1 comparison.

For each primary statistic and attention cell, pre-register an absolute or
relative practical bound, the aggregation rule, and an uncertainty interval
that respects station and burn/year blocks. The final comparison passes only
when every declared primary cell's interval lies inside its bound. Report
effect sizes and intervals, not a collection of non-significant p-values.
Failures remain results and identify the next profile refinement; they do not
license tolerance widening.

## Sequencing and non-goals

This draft deliberately sequences evidence before a broad campaign:

1. Ratify the v1 backend and QC policy in this specification.
2. Implement unit/structural tests, provenance, and QC diagnostics.
3. Run a bounded performance matrix on FMA-capable `wepp1`, with pinned-core
   repeated samples and raw results.
4. Only if the measured v1 performance remains material, dispatch the
   separately pre-registered parity assessment.

The draft does not change faithful code, assert v1 parity, approve a bare
`fast_batch` alias, or authorize a production default change.
