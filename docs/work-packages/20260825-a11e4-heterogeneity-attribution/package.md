# A11E4 — Forcing Heterogeneity Attribution

Status: `SCAFFOLDED`

Date: 2026-08-25

Evidence mode: prospective analysis of closed development evidence

Starting branch and push target: current `origin/main`, push `main`

## Objective

Test whether A11E3's station-level heterogeneity has a stable simple association
with nearest-candidate distance or station/candidate climate-regime agreement,
without reading raw observations or changing the generator or selector.

## Scope

Included: exact A11E3/A11E2 source and evidence authentication, strict 20x8
roster reconstruction, station-level both-improvement fractions, two frozen
metadata tests, deterministic replay, independent review, repository gates,
and terminal reconciliation.

Excluded: raw observed data, weather generation, generator or forcing-model
fitting, selector changes, thresholds learned from results, additional or
post-result attribution predictors, causal claims, confirmation, nomination,
promotion, or production changes. The frozen joint attribution regression is
included.

## Authority

- [SPEC-A11-HETEROGENEITY-ATTRIBUTION](../../specifications/SPEC-A11-HETEROGENEITY-ATTRIBUTION.md)
- closed A11E3 development evidence and decision
- closed A11E2 selector receipt

## Frozen decision

A joint station-level model adjusts ranked distance and regime mismatch for
station-regime fixed effects and for each other. Exact within-regime permutation
enumerates 1,327,104 assignments and uses max-|t| familywise adjusted p-values
at 0.05. A predictor also must retain its strict coefficient sign in all eight
leave-one-member-out and twenty leave-one-station-out fits. The four possible
association/no-association dispositions are fixed in the specification. A valid
non-signal result is complete evidence, not a HOLD.

## Data calendar and missingness preflight

No calendarized source data is read. A11E4 authenticates and audits only the
closed A11E3 aggregate metric rows and A11E2 selector metadata. The inherited
A11E3 calendar receipt remains authoritative and confirmation remains sealed.

## Plan

1. Freeze the manifest, schema, exact analysis arithmetic, and synthetic tests.
2. Independently review and publish prospective source to `origin/main`.
3. Authenticate closed evidence, reconstruct the exact station/member grid,
   join selector metadata, and run the two attribution tests.
4. Replay scientific outputs byte-identically, independently review, run gates,
   and reconcile package/catalog/spec/roadmap records.

## Gates

- strict manifest/schema and synthetic arithmetic/boundary tests;
- exact published source and A11E2/A11E3 closure/source/evidence identities;
- exact 20-station x eight-member grid and one-to-one selector join;
- finite metrics, zero invariants, and confirmation=false;
- exact two-test decision table and deterministic replay;
- independent review with no unresolved P0/P1;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
- `git diff --check` and changed-document link validation.

No production Rust function changes occur, so coverage/CRAP is not triggered.

## Artifacts

- `artifacts/analysis-manifest-v1.json` and strict schema
- `artifacts/analyze.py` and `artifacts/test_analyze.py`
- attribution evidence, decision, execution receipt, review, and gate record
