# A10M3 — Model, Training, Generation, and Selector Freeze

Status: `EXECUTED-COMPLETE`
Date: 2026-07-17
Evidence mode: Mixed
Starting branch and push target: clean `main` at `53d0e14`, push `main`

## Objective

Freeze the complete prospective A10 neural candidate, fitting, checkpoint,
generation, evaluation, runtime-benchmark, applicability, selector, and finite
resource contracts before any neural candidate is trained or scored.

## Scope

Included are research-only schemas, executable fail-closed validators and test
vectors, one bounded model family and grid, corpus-role and normalization
bindings, checkpoint/restart rules, stateless nested generation, B0/B1
comparators, candidate-blind score calibration, runtime boundaries, selector
ordering, and the A10M4 resource handoff.

Excluded are candidate fits or outputs, corpus target-byte reads, GPU jobs,
development scoring, confirmation access, public generation profiles, and any
change to faithful CLIGEN.

## Authority

A10M1 terminal `A10M1-CORPUS-READY`, A10M2 terminal
`A10M2-COMPUTE-READY`, toolkit terminal `LEMHI-TOOLKIT-FOUNDATION-READY`, and
Python smoke terminal `A10-LEMHI-PY311-SMOKE-READY` satisfy entry. The study
plan and accepted review define the scientific surface. This package binds
canonical configuration `lemhi-a10-py311-l40-v1` and semantic SHA-256
`0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`.
Python 3.8 is legacy explicit-only. The accepted A10M1 v2 manifests are the
only corpus identities. Confirmation target access remains prohibited.

## Plan

1. Hash and bind every predecessor, corpus, objective, null-calibration, and
   compute authority without reading candidate or confirmation targets.
2. Publish specifications and strict schemas before their executable consumer.
3. Freeze the bounded model/grid, training, checkpoint, generation, benchmark,
   objective, applicability, selector, and resource contracts.
4. Execute positive, malformed, missingness, comparator, selector, and exact
   5x/10x boundary vectors; prove finite configuration and resource limits.
5. Run repository gates, review the freeze, record the terminal, reconcile the
   roadmap/catalog, and hand the exact contract to A10M4.

## Gates

- every schema and executable validator fails closed on missing/additional
  fields and unknown identities;
- selector vectors cover both horizons, B0/B1 paired differences, strictly
  positive margins, noninferiority, missing B1, breadth, and deterministic tie
  breaks;
- exactly 5x is `WARN` and exactly 10x is `FAIL`;
- grid, promotion counts, GPU-hours, storage, job resources, members, burns,
  horizons, checkpoints, benchmark repetitions, and absolute limits are finite;
- canonical configuration ID and semantic hash agree everywhere;
- no candidate fit/output or confirmation target is accessed;
- authored Python compiles; JSON parses; `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass. Coverage/CRAP is not triggered because production Rust is
  unchanged.

## Exit criteria

`A10M3-DESIGN-FROZEN` requires every gate above and authorizes only A10M4's
bounded single-GPU qualification. Any incomplete schema, unbounded resource,
ambiguous missingness, inaccessible comparator identity, or post-output design
change yields `HOLD-A10-DESIGN-INCOMPLETE`.

## Result

Terminal: `A10M3-DESIGN-FROZEN`

The package froze a 12-configuration ceiling, one screen seed, at most four
full-development promotions and two finalists, three finalist training seeds,
stateless nested generation, six-regime representative benchmarking, a 0.10
standardized material-improvement margin against both B0 and B1, four
noninferiority guards, four-of-six minimum breadth, and a 560 L40 GPU-hour A10
ceiling. All executable vectors and repository gates passed. No candidate,
GPU, development series, or confirmation target was accessed.

## Artifacts

- `artifacts/design-freeze.md` — human-readable prospective freeze;
- `artifacts/model-training-generation-v1.json` — architecture, fit,
  checkpoint, generation, and finite resource contract;
- `artifacts/selector-benchmark-v1.json` — comparator, objective,
  applicability, selector, and benchmark contract;
- `artifacts/candidate-blind-calibration-v1.json` — pre-candidate numeric
  margins and inherited null-scale evidence;
- `artifacts/authority-manifest-v1.json` — immutable inputs;
- `artifacts/verify-a10m3.py` — executable verification;
- `artifacts/gate-results.md`, `review.md`, `terminal.md`, and
  `a10m4-handoff.md` — closure and successor evidence.
