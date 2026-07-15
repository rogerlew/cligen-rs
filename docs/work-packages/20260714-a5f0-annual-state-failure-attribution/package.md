# A5f0 — Annual-State Failure Attribution

Status: `EXECUTED-COMPLETE`
Date: 2026-07-14
Evidence mode: Mixed
Execution authorization: operator authorized scaffolding and execution on
2026-07-14

## Objective

Explain the unfavorable exploratory A5e0 climate result using only its retained
inputs and products, then decide whether to retire the exact
`a5e0_direct_annual_state_v1` scalar-IID mechanism or justify one narrowly
bounded future seam ablation. This package does not repair A5e0's prospective
boundary and does not promote, refit, or implement a climate model.

## Scope

Included:

- hash verification of the committed A5e0 coefficients, analysis, campaign
  record, and retained `target/a5e0` matrix products;
- decomposition of positive H1 degradation by its four frozen score families;
- reconstruction of the 1980–2009 Daymet annual-feature geometry used by the
  A5e0 fitter;
- regression of realized candidate annual features on the recorded annual
  states to distinguish runtime response from model structure;
- comparison of baseline and candidate annual-feature SD distance from the
  2010–2025 Daymet evaluation surface at occurrence, amount, Tmax, and Tmin
  seams; and
- one frozen, descriptive decision rule ending in
  `RETIRE-SCALAR-IID-MECHANISM` or `JUSTIFY-ONE-BOUNDED-ABLATION`.

Excluded:

- new climate generation, new random states, coefficient refitting, threshold
  tuning, parameter repair, new ablation output, or confirmation data;
- modification of production Rust, the A5e0 implementation, public schemas,
  profiles, defaults, or provenance;
- causal or population significance claims from three exposed development
  stations; and
- retirement of annual-state modeling in general. A retirement decision is
  scoped only to the exact A5e0 direct rank-one scalar-IID mechanism and fit.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) keeps faithful
  generation governed by the vendored Fortran. A5f0 does not touch that path.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) makes the
  quality vector authoritative for extension evaluation.
- [ADR-0004](../../decisions/0004-a5b-interannual-no-promotion.md) keeps all
  successor evidence non-promotional without a prospective study.
- The immutable
  [A5e0 package](../20260714-a5e0-direct-annual-state-pilot/package.md), its
  committed coefficient/analysis/campaign artifacts, and its retained
  hash-indexed raw matrix are the only empirical inputs.
- `artifacts/attribution-contract-v1.json` is the package-local frozen analysis
  and decision contract. It is a research artifact, not a public interface.

## Plan

1. Scaffold the package, analysis contract, analyzer, and verifier without
   reading derived seam-attribution outcomes.
2. Freeze their hashes together with the exact A5e0 input identities in
   `pre-analysis-freeze-v1.json`.
3. Verify the full retained matrix and derive the H1-family, feature-geometry,
   runtime-response, and seam-distance evidence without generating climates.
4. Apply the frozen decision priority and render machine-readable and concise
   human-readable findings.
5. Review scope, arithmetic, reproducibility, and claim strength; run package
   and repository gates; then update the roadmap and catalog.

## Execution result

A5f0 executed against all 48 retained A5e0 runs and verified 288 indexed
products. The frozen rule returned `RETIRE-SCALAR-IID-MECHANISM` under
`RETIRE_STRUCTURAL_OVERCOUPLING`:

- cross-month dependence supplied 70.6% and 67.9% of summed positive H1-family
  degradation at 30 and 100 years respectively;
- the leading component represented only 16.5%, 14.5%, and 11.9% of
  standardized fit-period annual-feature variance at the dry, cold, and wet
  stations;
- all 96 active station-month loadings had the expected realized response
  sign, with global median realized/expected slope ratio 0.994; and
- no parameter seam was the same uniquely worst evaluation-period
  annual-feature SD-distance seam in the required five of six station-horizon
  cells. The counts were occurrence 0, amount 1, Tmax 0, and Tmin 0.

This triangulation attributes the unfavorable exploratory result to the exact
mechanism's shared rank-one annual coupling rather than to absent runtime
signal or one isolated parameter seam. It is descriptive attribution on the
exposed development surface, not causal proof. No follow-on package is
authorized or queued.

## Execution & dispatch

This package executes locally in the shared repository on `main`, starting
from commit `1ca40bbe006ed5d823d2dd8e373f720f20d60ba0`. No side branch, external
executor, or push is authorized by this dispatch.

The freeze is prospective only with respect to A5f0's derived attribution
algorithm. A5e0 outcomes and the three development stations were already
observed. The freeze therefore must not be described as an independent or
prospective climate test.

## Gates

- every frozen source and A5e0 input hash matches the freeze manifest;
- all matrix products consumed by the analyzer match the A5e0 matrix index;
- exactly 48 A5e0 run records are present: three stations × two arms × eight
  replicates, each with 30- and 100-year products;
- rerunning the analyzer reproduces the committed attribution, decision, and
  findings byte-for-byte;
- the decision follows the priority and thresholds in the frozen contract;
- no new `.cli`, coefficient, production, or public-interface file is created;
- review checks scope, arithmetic, consistency, and causal-claim restraint;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage and CRAP gates are not applicable because this package changes no
production function in `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires complete retained-input integrity, deterministic
derived artifacts, a contract-valid terminal decision, review acceptance, and
passing repository gates. `EXECUTED-HOLD-INPUT-INTEGRITY` is required if any
retained product is absent or mismatched; its first follow-on is recovery from
the hash-pinned A5e0 producer, not partial analysis. A calculation or contract
defect produces `EXECUTED-HOLD-ANALYSIS-DEFECT` and no scientific disposition.

Neither terminal scientific decision authorizes implementation. A bounded
ablation requires a new operator-dispatched, prospectively frozen package.
Retirement closes only further investment in the exact A5e0 mechanism.

## Artifacts

- `artifacts/design.md` — scope and interpretation boundary frozen before
  derived attribution.
- `artifacts/attribution-contract-v1.json` — exact inputs, calculations,
  thresholds, and decision priority.
- `artifacts/pre-analysis-freeze-v1.json` — source and input identities.
- `artifacts/analyze-a5f0.py` — deterministic derived-only analyzer and
  findings renderer.
- `artifacts/verify-a5f0.py` — freeze, matrix, decision, and reproduction gate.
- `artifacts/a5f0-attribution-v1.json` — complete derived evidence.
- `artifacts/a5f0-decision-v1.json` — narrow terminal disposition.
- `artifacts/a5f0-findings.md` — concise human-readable interpretation.
- `artifacts/review.md` — accuracy, consistency, and scope review.
- `artifacts/gate-results.md` — commands and results.
