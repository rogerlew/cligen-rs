# A5a — Quality Metrics v3 and Observed Target Corpus

Status: `EXECUTED-COMPLETE`
Date: 2026-07-12
Completed: 2026-07-13
Evidence mode: Mixed

## Objective

Extend the ADR-0002 quality instrument before any interannual generation
candidate is implemented. The package publishes metrics version 3, an
independently versioned and hash-pinned observed-target corpus, and the
pre-registered climate and downstream-WEPP evaluation protocol that A5b and
A5c must use.

## Scope

Included:

- keep `quality_report_schema_version = 2` and bump only
  `metrics_version = 3`;
- preserve the rendered-text `.cli` intake and run-emitted/post-hoc equality;
- extend interannual metrics to monthly precipitation totals, wet-day counts,
  wet-day mean amounts, and monthly mean Tmax/Tmin;
- add cross-month and cross-variable anomaly dependence, annual lag-one
  persistence, and a pinned low-frequency power summary;
- add directly comparable `prcp >= 1.0 mm` precipitation structure metrics,
  whole-stream spells that cross month/year boundaries, wet-amount
  persistence, and annual 1/3/5-day maxima;
- correct the historical quality-only `ip` naming to
  `peak_intensity_ratio`, add time-to-peak and peak-ratio distributions, and
  add their pairwise dependence with event depth and duration;
- add precipitation/freezing-temperature and air-temperature freeze/thaw
  proxies, explicitly distinct from snowpack, soil frost, runoff, and erosion;
- publish a separate downstream WEPP response-record contract and a pinned
  protocol; no WEPP state enters the `.cli` quality report;
- archive the exact Daymet primary raw objects and a newly versioned GHCN
  snapshot, publish their hashes, and derive fixed 1980–2025 targets with a
  1980–2009 fitting / 2010–2025 held-out split;
- pre-register 30- and 100-year candidate gates, aggregation order,
  replicate identities, uncertainty treatment, and no-regression guards;
- add complete validation/parsing for the public mutable quality-report DTO;
- retain all twelve faithful `.cli` byte-parity gates.

Excluded:

- any generation-profile, station-model, station-schema, runspec, Parquet,
  provenance, or faithful-generator behavior change;
- fitting or running the A5b candidate models;
- claiming `rng.burn` offsets are independent seeds;
- a true subdaily observed corpus or a new hyetograph model;
- executing WEPP against sibling-repository state. A5b/A5c must supply the
  pinned WEPP executable and input decks required by the protocol.

## Authority

- Extension authority: ADR-0002 and SPEC-QUALITY-REPORT revision 8.
- Observed-target authority: SPEC-OBSERVED-TARGET-CORPUS revision 1 and its
  archived source-object manifest.
- Campaign authority: SPEC-A5-EVALUATION revision 2 and the ratified sequence
  in `docs/ROADMAP.md`.
- Faithful behavior remains governed by ADR-0001 and
  `reference/cligen532/cligen.f`; this package observes rendered output only.

## Plan

1. Freeze the v3 metric definitions, observed-corpus contract, and A5
   evaluation protocol.
2. Archive and verify source objects; derive the corpus with a deterministic
   builder and validate it against the published schema.
3. Implement metrics v3 behind the unchanged quality-report envelope and
   add fail-closed DTO validation.
4. Add hand-computable edge vectors, legacy measurability, schema, parity,
   and deterministic-emission gates.
5. Execute the full Rust, schema, corpus-rebuild, parity, coverage, and CRAP
   gates; run an independent adversarial review.
6. Close the package, move A5a out of the active roadmap, and record A5b as
   ready only if every exit criterion is satisfied.

## Execution & dispatch

Execute from current `origin/main` and push only to `main` when the operator
requests publication. No side branch is authorized. A1 commit `80b6112` is
the starting dependency.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- all twelve faithful golden `.cli` outputs remain byte-identical;
- historical quality schemas remain byte-identical and independently valid;
- every new JSON document passes a real offline Draft 2020-12 validator;
- archived source hashes, builder hash, and derived-corpus hash verify;
- an offline corpus rebuild is byte-identical;
- generated v3 reports exercise 30- and 100-year horizons and every metric
  group without non-finite JSON values;
- independent review reports no unresolved P1/P2 finding.

## Exit criteria

`EXECUTED-COMPLETE` requires the versioned metric schema and implementation,
hash-pinned observed targets, fixed evaluation protocol, complete evidence
gates, and independent review. A hold is required if the primary Daymet raw
objects cannot be archived/rebuilt, faithful output changes, any production
function exceeds CRAP 30, or a P1/P2 review finding remains unresolved.

## Artifacts

- `artifacts/design-decisions.md` — metric and compatibility rulings.
- `artifacts/corpus/` — deterministic acquisition/build tooling, manifests,
  targets, and validation evidence.
- `artifacts/a5b-pre-registration.md` — fixed candidate matrix and gates.
- `artifacts/observed-bootstrap-v1.py` and
  `artifacts/observed-bootstrap-v1-golden.json` — executable observed-target
  uncertainty contract and golden vector.
- `artifacts/run-baseline-matrix.py`, `artifacts/verify-baseline-evidence.py`,
  and the baseline manifest/analysis/archive — admissible 544-run baseline
  evidence and independent verifier.
- `artifacts/verify-a5-climate-gate-metrics-v1.py` — semantic and mutation
  verifier for the version-1 scalar-cell manifest.
- `artifacts/wepp-response-protocol.md` — separate downstream-response
  protocol.
- `artifacts/gate-results.md` — executed evidence.
- `artifacts/review.md` — independent review and dispositions.
