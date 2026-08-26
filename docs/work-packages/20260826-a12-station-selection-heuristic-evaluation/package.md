# A12 — Station Selection Heuristic Evaluation

Status: `SCAFFOLDED`

Date: 2026-08-26

Evidence mode: observed fit-validation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether the current cligen-rs PRISM station heuristic is preferable
to geographic closest-station selection on the registered 240-location
`fit_validation` corpus, while treating a WEPPpy-style elevation/PRISM
heuristic as a separately named reference rather than an authority.

## Scope

Included: prospective selector definitions and decision gates, authenticated
PRISM and `us-2015` inputs, complete calendar/role/missingness preflight,
station-parameter comparison with observed Daymet structural descriptors,
deterministic replay, independent review, station-selection receipt provenance
hardening, and end-user CLI documentation.

Execution consumes the exact registered `us-2015-2026.07.tar.gz` bytes,
verifies their size and SHA-256, and scores from a fresh isolated extraction.
It verifies every PRISM runtime file used against the registered grid and
auxiliary hashes before opening the observed corpus.

Excluded: confirmation targets, fitting on `fit_validation`, selector-weight
tuning after results, production default changes, user-defined station runtime
implementation, generator changes, faithful arithmetic changes, and claims
about wind, radiation, dew point, or subdaily intensity that Daymet cannot
evaluate.

## Authority

- [SPEC-A12-STATION-SELECTION-EVALUATION](../../specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md)
- [SPEC-A10-STOCHASTIC-PRISM-COMPARATOR](../../specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md)
- [SPEC-A10-CORPUS](../../specifications/SPEC-A10-CORPUS.md)
- WEPPpy is reviewed prior art only; no behavioral identity is presumed.

## Frozen hypothesis

The current heuristic is appropriate only if its paired site-composite error
is lower than closest selection with a 95% site-bootstrap upper bound below
zero, it wins at more than half of the 240 sites, and none of six structural
families has a median error more than 5% above closest. The elevation/PRISM
reference is judged by the same rule. If neither heuristic passes, closest is
preferred by the frozen simplicity rule. No outcome changes the runtime default
inside this package.

## Data calendar and missingness preflight

The package consumes the 240 A10 `fit_validation` objects under
`daymet_official_365_v1`, 1980-01-01 through 2009-12-31 inclusive. Each object
must have 10,958 normalized axis labels, 10,950 observed rows, and exactly the
eight masked leap-year December 31 dates. Descriptor eligibility is based on
the explicit `source_observed` mask; it is never inferred from the axis.
Confirmation roles and target series remain unopened.

## Plan

1. Freeze the specification, manifest, evaluator, schema, tests, and runtime
   provenance amendment.
2. Independently review and publish the prospective source to `origin/main`.
3. Build the exact release binary, authenticate all inputs, execute the
   240-location selector comparison, and replay it byte-identically.
4. Independently review the completed evidence, run repository gates, and
   reconcile the package, catalog, specification registry, and roadmap.

## Gates

- exact 240-object role/calendar/missingness preflight;
- exact PRISM bundle, station collection, source `.par`, and cligen executable
  SHA-256 identities;
- source/toolchain/Cargo.lock-bound `--locked` release build receipt and an
  end-to-end runtime probe requiring the selection receipt and artifact
  manifest executable hashes to agree;
- strict selector/evaluator manifest and synthetic tests;
- complete finite six-family evidence for all three policies and 240 sites;
- deterministic evidence/decision replay;
- independent review with no unresolved P0/P1;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` and
  `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`;
- `git diff --check` and changed-document relative-link validation.

## Exit criteria

`EXECUTED-COMPLETE` requires one of the frozen scientific dispositions plus
complete cryptographic provenance, replay, review, and gates. Identity,
calendar, role, numerical, or evidence failure closes on an explicit HOLD.

## Artifacts

- prospective manifest, schema, evaluator, and synthetic tests;
- calendar/input preflight, selector evidence, decision, and execution receipt;
- independent review and gate record.
