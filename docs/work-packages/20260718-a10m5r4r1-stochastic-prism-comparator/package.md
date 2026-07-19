# A10M5R4R1 — Stochastic PRISM Localized-`.par` Comparator

Status: `EXECUTED-COMPLETE`
Date: 2026-07-18
Evidence mode: Ran implementation, distribution, and generic acceptance
Starting branch and push target: `main` at the A10M5R4 hold, push `main`

## Objective

Build and validate the stochastic-plus-PRISM comparator required before
realized A10 temporal adjudication: longitude, latitude, and years select a
PRISM-normal-localized station `.par`, then unchanged faithful CLIGEN produces
the stochastic stream with complete provenance.

## Operator guidance captured

- Required scientific request: longitude, latitude, and number of years.
- Query monthly PRISM precipitation, Tmax, and Tmin normals and write an
  artifact with source and extraction provenance.
- Select the source station by a deterministic `wepppy`-style rank heuristic
  over distance, latitude, and monthly normals.
- Replace `.par` precipitation and temperature locations; recalculate
  P(wet|wet) and P(wet|dry); adjust `MX .5 P` half-hour intensities.
- Review the existing `wepppy` implementation for sanity rather than treating
  it as unexamined authority.
- Redistributing the normals maps is acceptable.

The exact revision-1 interpretation is frozen by
`SPEC-A10-STOCHASTIC-PRISM-COMPARATOR` and `artifacts/design-freeze.md`.

## Scope

Included:

- one immutable query-optimized runtime bundle plus a separately preserved
  exact-source bundle for the 36 official PRISM Norm91m 1991--2020 CONUS 4 km
  monthly ppt/Tmax/Tmin archives, manifests, receipt, and attribution;
- the public Cargo-installed `cligen prism sync | query | run` surface while
  retaining `faithful_5_32_3` as the downstream generation profile;
- explicit hash-verified sync and local-only point-query behavior;
- deterministic `us-2015` station selection with a full candidate receipt;
- localized legacy `.par`, field-level mutation/provenance receipt, and
  unchanged faithful cligen-rs execution;
- tests for extraction, selector ranking, wet/dry algebra, intensity scaling,
  fixed-width rendering, untouched-record identity, deterministic generation,
  and expected monthly behavior; and
- bounded A10 evaluation inputs only after the generic mode passes.

Excluded:

- neural training or generated-output access, P1/P2 scoring, protected roles,
  confirmation evidence, a new generation profile, changes to the faithful
  generator, silent live-network fallback, terrain downscaling, or a claim
  that PRISM supplies daily/subdaily climate truth.

## Authority

- ADR-0005 and SPEC-A10-REFINEMENT-TRAJECTORY require the separately
  versioned stochastic-plus-PRISM comparison.
- SPEC-PAR governs the source and localized legacy files;
  `faithful_5_32_3` remains the generator identity.
- PRISM Group Norm91m supplies only the monthly ppt/Tmax/Tmin locations.
- `wepppy` commit `3ee74d02df445a30968ef92975e5e3e2f6084669` is reviewed prior art,
  not port authority. Exact file hashes and findings are in
  `artifacts/wepppy-sanity-review.md`.

## Plan

1. Publish deterministic runtime and exact-source PRISM bundles and pin their
   release assets, byte counts, archive SHA-256 values, 36 source/member
   hashes, producer receipt, terms, and attribution in a strict embedded
   distribution manifest.
2. Implement explicit sync/acquisition and local raster queries with atomic
   cache publication, `--from` air-gap support, and network-prohibition tests
   on the generation path.
3. Implement the frozen station selector and emit a ten-candidate ranking
   receipt for every request.
4. Implement six-row lexical `.par` mutation, reparse it through SPEC-PAR,
   retain all untouched bytes, and emit requested-versus-encoded values.
5. Build the faithful runspec, execute cligen-rs, and atomically publish the
   complete artifact set.
6. Run formula/differential/end-to-end/Monte Carlo acceptance and repository
   gates before closing the package.
7. Scaffold a fresh realized temporal-adjudication package after this
   comparator reaches its ready terminal.

## Gates

- all 36 source archives and embedded rasters are exact, finite, attributed,
  and reconstructable from the registered bundle;
- request validation fails closed outside coordinate/year domains and PRISM
  coverage;
- selector candidates, component ranks, weights, tie-breaks, and selected par
  exactly match the frozen contract;
- wet-day frequency, transition probabilities, precipitation mean, Tmax,
  Tmin, and `MX .5 P` exactly match registered algebra vectors before and
  after fixed-width encoding;
- untouched `.par` records/tail are byte-identical and the localized file
  passes SPEC-PAR;
- the generation path is network silent and exact-repeatable;
- realized ensemble monthlies meet prospectively frozen tolerances around the
  encoded `.par` targets;
- no neural output, protected role, or allocation is accessed by setup work;
- package verifier, Python/JSON parsing, `git diff --check`, `cargo fmt
  --check`, `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass;
  and
- if production functions are added or changed under `crates/`, workspace
  llvm-cov and CRAP gates also pass with no production function above 30.

## Exit criteria

`A10M5R4R1-STOCHASTIC-PRISM-READY` requires a published hash-pinned normals
bundle, complete generic implementation, green acceptance evidence, and no
unresolved high/medium implementation-review finding. It authorizes only a fresh
realized temporal-adjudication package.

Disposition: `A10M5R4R1-STOCHASTIC-PRISM-READY`.

Both registered bundles were published and independently reproduced; the
Cargo surface, air-gap sync, strict local query, deterministic selector,
six-row localization, artifact receipts, and unchanged faithful execution
passed. Independent Rasterio extraction agreed for all 36 values at the
registered interior vector, complete repeat runs were byte-identical, and the
prospectively frozen 100-year ensemble gate passed all 36 monthly cells. The
fresh temporal-adjudication successor is A10M5R4R2.

Legitimate holds were `HOLD-A10-PRISM-DISTRIBUTION`,
`HOLD-A10-PRISM-EXTRACTION`, `HOLD-A10-SELECTOR-CONTRACT`,
`HOLD-A10-PAR-LOCALIZATION`, or `HOLD-A10-COMPARATOR-CALIBRATION`, each with
the exact failed condition and gathered evidence.

## Artifacts

- `artifacts/design-freeze.md` — prospective request/data/selection/mutation
  and output identity;
- `artifacts/wepppy-sanity-review.md` — source-pinned review and adopted or
  rejected behavior;
- `artifacts/prism-distribution-plan.md` — redistribution and attribution
  decision;
- `artifacts/verify_scaffold.py` — fail-closed structural scaffold check;
- `artifacts/scaffold-gates.md` — executed hold/scaffold/repository gates;
- `artifacts/build_prism_bundles.py` — strict deterministic bundle producer;
- `artifacts/prism-bundle-manifest.json` — published payload identity;
- `artifacts/monte-carlo-contract.json` and `monte-carlo-result.json` —
  prospective ensemble gate and result;
- `artifacts/acceptance-report.md` — extraction, repeatability, localization,
  and end-to-end evidence;
- `artifacts/implementation-review.md` — post-implementation safety and claim
  review;
- `artifacts/gate-results.md` — repository and package gates; and
- `artifacts/verify.py` — fail-closed executed-package verifier.
