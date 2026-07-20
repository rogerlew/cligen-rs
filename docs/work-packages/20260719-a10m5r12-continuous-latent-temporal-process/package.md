# A10M5R12 — Continuous Latent Temporal Process Comparison

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Determine whether explicit continuously evolving stochastic state can close
the broad A10M5R11 realized temporal gap, and whether a distinct slow
multi-year process is necessary beyond a medium-timescale process.

## Scope

The matched candidates are `continuous_medium_latent_process-k2` and
`continuous_hierarchical_latent_process-k2`. Both use the frozen P2 daily
backbone, eight medium factors, continuous seasonal/static loading, three
seeds, and the complete inherited temporal protocol. The hierarchical arm
adds four slow factors. This package does not compare capacities, fit solar,
open confirmation, or change temporal thresholds.

Calendar month and year are aggregation bins only. The latent processes use
the exact daily transition of continuous-time stationary OU dynamics and have
no calendar-boundary reset. This directly incorporates the operator's concern
that natural climate variation is continuous rather than month-quantized.
The new loading network excludes the binary leap-year indicator. The frozen
matched P2 backbone still consumes that inherited feature, so the bounded claim
is continuous candidate state and smooth candidate loadings, not a fully
calendar-discontinuity-free composite model.
The inherited objective still observes that process through calendar-month and
calendar-year summaries, so this package does not claim scale invariance. If a
candidate qualifies, random-origin rolling-window sensitivity is required
before promotion.

## Authority

This is a research extension governed by
`SPEC-A10-CONTINUOUS-LATENT-TEMPORAL`. The operator's 2026-07-19 instruction
authorizes the development package. The source scaffold is published before
fresh package-scoped authority is created. The 395 GPU-minute ceiling covers
one 30-minute control job, two 180-minute candidates, and five minutes of
exact-node cleanup recovery.

## Plan

1. Freeze architecture, state-clock, data, objective, temporal, resource, and
   firewall contracts.
2. Publish and review the scaffold; create fresh authority from that commit.
3. Materialize exact controls, then train both candidates concurrently with
   one serialized environment bootstrap at admission.
4. Collect 288 candidate streams, generate comparators locally, and replay
   the source/receipt-bound leap-safe selector twice in isolated roots.
5. Close resources, review science, and reconcile roadmap/catalog/ExecPlan.

The inherited conditional-member daily NLL is diagnostic only (weight zero)
for both candidates. It is not a marginal mixture likelihood and would
otherwise pressure each latent member toward the observed day, counter to the
package's stochastic-dispersion objective.

Because the inherited eligibility bootstrap randomizes observation-year order,
the slow-process question also receives non-gating actual-series annual
location, dispersion, lag, and cross-field diagnostics with paired member
bootstrap and learned-time-scale reporting.

## Data calendar and missingness preflight

The package inherits `SPEC-A10-CORPUS` and `daymet_official_365_v1` for
1980--2009. Each point has 10,958 Gregorian-axis rows, 10,950 observed core
rows, eight unobserved December 31 leap-year rows, and observed February 29.
The committed corpus pin requires the canonical 224,040,960-byte archive and
safe single-prefix layout before authority or extraction. A package-local
revision-2 preflight scans all 1,440 eligible objects and commits the required
leap/missing-date/window fixture before authority. That full scan is an
authority-time corpus gate; it is not the compact control-job receipt. The
control job separately reproduces the inherited, predecessor-hash-bound
materializer expectation.

## Gates

- exact predecessor, corpus, control, source, staged asset, comparator binary,
  and per-site comparator provenance identities;
- continuous-core recurrence self-test and no calendar-boundary state reset;
- two candidates by three seeds by six sites by eight 100-year members;
- retained raw float32 daily streams and fitted adapter checkpoints with exact
  hash, support, and metric replay;
- inherited temporal eligibility and byte-identical selector replay;
- confirmation and solar firewalls;
- exact job-local/durable cleanup and resource settlement;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage/CRAP is not triggered because no production function under `crates/`
changes.

## Exit criteria

At least one eligible candidate yields `A10M5R12-TEMPORAL-READY`; all eligible
candidates continue. An empty set yields
`HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`. Any identity, execution,
evidence, replay, resource, or cleanup failure receives an exact
`HOLD-A10M5R12-*` terminal without scientific interpretation.
