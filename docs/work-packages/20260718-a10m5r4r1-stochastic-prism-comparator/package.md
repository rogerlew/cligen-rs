# A10M5R4R1 — Stochastic PRISM Localized-`.par` Comparator

Status: `SCAFFOLDED`
Date: 2026-07-18
Evidence mode: Static specification and source review; implementation pending
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

- one immutable external bundle containing the 36 official PRISM Norm91m
  1991--2020 CONUS 4 km monthly ppt/Tmax/Tmin archives, manifest, and
  attribution;
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
  confirmation evidence, public generation-profile promotion, changes to the
  faithful generator, silent live-network fallback, terrain downscaling, or a
  claim that PRISM supplies daily/subdaily climate truth.

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

1. Publish the deterministic external PRISM source bundle and pin its release
   asset, byte count, archive SHA-256, 36 member hashes, license terms, and
   attribution in a strict manifest.
2. Implement explicit sync/acquisition and local raster queries with atomic
   cache publication, `--from` air-gap support, and network-prohibition tests
   on the generation path.
3. Implement the frozen station selector and emit a ten-candidate ranking
   receipt for every request.
4. Implement six-row lexical `.par` mutation, reparse it through SPEC-PAR,
   retain all untouched bytes, and emit requested-versus-encoded values.
5. Build the faithful runspec, execute cligen-rs, and atomically publish the
   complete artifact set.
6. Run formula/differential/end-to-end/Monte Carlo acceptance, repository
   gates, and an independent review before closing the package.
7. Scaffold a fresh realized temporal-adjudication package only after this
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
unresolved high/medium independent-review finding. It authorizes only a fresh
realized temporal-adjudication package.

Legitimate holds are `HOLD-A10-PRISM-DISTRIBUTION`,
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
- future `artifacts/prism-bundle-manifest.json` — published payload identity;
- future strict request/query/selection/mutation/manifest schemas;
- future executable package verifier and acceptance records; and
- future independent review and disposition.
