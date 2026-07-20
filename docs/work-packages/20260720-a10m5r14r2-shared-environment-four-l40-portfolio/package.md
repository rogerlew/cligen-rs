# A10M5R14R2 — Shared-Environment Four-L40 Portfolio

Status: `EXECUTED-ABORTED-BEFORE-SUBMISSION`
Date: 2026-07-20
Evidence mode: Operational/interface successor; unchanged R14 model and objective
Starting branch and push target: current `main`, push `main`

## Objective

Execute the unchanged A10M5R14 four-arm continuous distribution-head
factorial after A10M5R14R1 established that four concurrent single-GPU jobs
can exhaust node-local storage while independently expanding the same 3.9 GB
canonical wheelhouse and portable runtime. R14R2 replaces those four
duplicated job-local environments with one four-L40 portfolio job, one shared
canonical environment, one shared read-only corpus extraction, and four
independent candidate processes.

R14R1 also exposed an interface-only parameter accounting defect after science
startup. The R14 core reported total control-plus-adapter parameters in the
inherited adapter-only `parameter_count` field; the unchanged caller then added
the control count a second time. R14R2 preserves the model and trained tensors,
restores `parameter_count` to adapter-only, and publishes the real total in
`total_parameter_count`. The exact totals remain 278,667, 278,747, 279,819,
and 279,899, all below the frozen 330,000 ceiling.

## Operational correction

The portfolio process performs setup exactly once before any candidate starts.
It authenticates the runtime, wheelhouse, requirements lock, asset manifest,
submission admission, four allocated L40s, and the exact candidate/device map.
It then removes setup payloads, parses the allocation's exact four distinct
`CUDA_VISIBLE_DEVICES` tokens, and assigns token slots 0, 1, 2, and 3 to four
ordinary Python processes:

| Allocation-token slot | Candidate role |
|---:|---|
| 0 | `continuous-location-ou-k2` |
| 1 | `continuous-location-ou-smooth-climatology-k2` |
| 2 | `continuous-location-scale-ou-k2` |
| 3 | `continuous-location-scale-ou-smooth-climatology-k2` |

This is process-level portfolio concurrency, not DDP or collective training.
NCCL and `torchrun` are not used. Every process retains the exact R14 model,
objective, inputs, seeds, checkpoints, and selector stream. Each has an
exclusive durable result directory and exclusive job-local cache directories;
the environment and corpus are read-only after setup.

The portfolio fails closed if allocation exposes other than four unique L40s,
if a child does not see exactly one L40, if any mapping or candidate identity
drifts, if shared setup is not authenticated, if output/cache paths collide,
if any process exits nonzero, or if supervised cleanup cannot remove the exact
job-local root. A scientific child failure does not erase evidence from its
siblings: the launcher waits for all four processes, then fails the portfolio
if any failed. Scheduler signals still terminate the complete supervised tree.

## Scientific freeze

R14's science contract, portfolio contract, temporal contract, 188-metric
objective and scales, objective implementation, continuous and climate cores,
four candidate identities, model parameter counts, sites, windows, calendar
profile, seeds 147031/271828/314159, common random fields, selector, thresholds,
evidence profile, and science terminals remain byte-identical. The R14
continuous core is retained byte-for-byte as an inherited asset behind the
parameter-accounting interface wrapper; model construction, training,
objective evaluation, and scoring are unchanged. The daily OU
state remains continuous across month and year boundaries. Solar and protected
confirmation roles remain sealed.

Scientific terminals remain `A10M5R14-TEMPORAL-READY` and
`HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`.

## Calendar and missingness gate

The inherited Daymet preflight completes before either role is submitted. It
pins `daymet_official_365_v1_to_proleptic_gregorian_daily`, 5,844 normalized
rows, 5,840 observed core rows, the observed February 29 and structural-null
December 31 convention, leap/window-boundary fixtures, and mask-based month and
year eligibility. A complete normalized date axis is never treated as proof of
observational completeness.

## Resources and authorization

The fresh ceiling remains 995 GPU-minute equivalents: one 30-minute one-L40
control, one 240-minute four-L40 portfolio charged as 960 GPU-minutes, and one
five-minute one-L40 exact-node recovery reserve. Both primary roles have one
attempt and no retry. The xlarge-evidence profile remains unchanged. Execution
created fresh authority and staged the plan, but the admission failure occurred
before resource reservation or HPC submission.

## Predecessor gate

Execution requires an authenticated terminal R14R1 failure record proving the
node-local ENOSPC setup failure, charged attempts, retained evidence, and exact
cleanup disposition. The published scaffold deliberately does not manufacture
that record from mutable live state. `prepare_assets.py` and the authority
builder refuse execution until the exact published predecessor artifact and
its hash are materialized in this package.

## Execution outcome

R14R2 reached remote `VERIFIED` at source commit
`3a9f2aedab1f7be5202a141c7d32350d7fe6f5e3`, then aborted before the first
control submission. Its composed admission controller staged a distinct outer
`admission_checker.py` and delegated `inherited_admission_checker.py`, but the
inherited R14R1 self-check still resolved its identity through the outer
logical plan name. The exact differing SHA-256 identities were
`a152fbbc3b2865ff0f39195a8cd64adb13780c67923662bc9fba9839db95651d`
and `3c90ff10b2c3b4fe8c2c3e7ea3f90e018175455251dc6228c7abd1736f5565a5`.

The toolkit recorded zero attempts, the resource ledger remained at genesis,
no scheduler job or GPU minute was consumed, and the exact remote root was
removed. The authenticated terminal was
`LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION`. The initially proposed R14R2R1
package-local compatibility edit is deferred; A10M5O1R3 first adds a general
ordered composed-checker identity contract to the toolkit.
