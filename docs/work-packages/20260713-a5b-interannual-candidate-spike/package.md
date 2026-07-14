# A5b Interannual Candidate Spike

Status: `EXECUTED-COMPLETE`
Date: 2026-07-13
Evidence mode: Mixed

## Objective

Execute the prospectively registered seven-candidate interannual experiment
against the accepted A5a corpus and baseline. Produce deterministic,
production-format coefficient-augmented station bundles, a separately
versioned experimental runtime and run record, the complete 1,904-run climate
matrix, the fixed climate-gate and uncertainty analysis, and pinned downstream
WEPP response evidence. A5b is evidence for A5c; it does not promote a public
generation profile.

## Scope

Included:

- the exact 17-station Daymet V4 R1 fit corpus, structurally limited to
  1980--2009 and mapped with the A5a `noleap_365` transform;
- seven fixed candidates: rank-one monthly SD, full monthly covariance,
  Fourier/EOF, vector AR, two-state Gaussian HMM, spectral random phase, and
  the Fourier/EOF plus daily precipitation counterfactual;
- one strict coefficient-augmented station bundle per station, embedding the
  revision-1 fixed-monthly station document and all separately identified
  candidate payloads;
- an A5b-only typed-row overlay executable, independent extension RNG, strict
  plan/run-record schemas, and post-hoc envelope-2/metrics-3 quality reports;
- the 17 x 2 x 8 x 7 = 1,904 candidate climate matrix and the unchanged A5a
  scientific/conditioned baselines;
- deterministic gate analysis, report-only 2,000-replicate observed-target
  uncertainty, parameter/runtime/failure reporting, and pinned WEPP runs; and
- independent review and disposition before closure.

Excluded:

- changing faithful generation, legacy `.par` syntax, provenance v1, typed
  output v1, or the public runspec/profile vocabulary;
- promoting any candidate (A5c owns that decision and any public runtime
  integration);
- PRISM or gridMET fitting in the primary matrix; and
- refitting through the 2010--2025 held-out interval.

## Authority

- Faithful input trajectories remain governed by
  `reference/cligen532/cligen.f` through the accepted Rust port and A5a
  baseline.
- Candidate/evidence behavior is governed by
  `docs/specifications/SPEC-A5B-CANDIDATES.md`,
  `docs/specifications/SPEC-A5-EVALUATION.md` revision 3, and the hash-pinned
  A5a executable contracts.
- The source decision is
  `../20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md`.

## Prospective freeze

This package, `SPEC-A5B-CANDIDATES` revision 1, its JSON schemas, the copied
A5a executable-contract artifacts, and the WEPP campaign contract are frozen
and conformance-tested before any candidate output is inspected. Candidate
execution may write sealed output while workers run; analysis does not open
candidate reports until the complete matrix, hashes, and schemas validate.
Later WEPP-format and climate-analysis contract failures required independently
versioned successor tools. Their candidate response/metric inspection is
disclosed in the retained amendments, so the final model-selection evidence
is exploratory rather than fully prospective.

## Outcome

A5b completed all fit, climate, uncertainty, and downstream work: 17 stations,
seven candidates, 1,904 candidate climates, a 2,000-replicate observed-target
bootstrap, and 2,176 validated WEPP response/execution records. All repository
and package gates pass, and the independent review is accepted with no open
finding.

None of the seven candidate versions passes all climate Gates 1--6 at both
horizons. Gate 7 passes after attachment of the complete WEPP campaign, but
does not cure those climate failures. No model/profile is promoted. The exact
results and exploratory-boundary disclosure are in
[`artifacts/results.md`](artifacts/results.md); the machine-readable analysis
identities are in
[`artifacts/analysis-evidence-v1.json`](artifacts/analysis-evidence-v1.json).
A5c may now record the conservative no-promotion adjudication.

## Plan

1. Revalidate the accepted A5a baseline and reproduce all five climate and
   three WEPP contract identities byte-for-byte. Add the carried order-
   sensitive and non-divisor bootstrap vectors.
2. Freeze candidate mathematics, identifiers, parameter counts, fit/runtime
   failure rules, independent RNG domains, station bundle, plan, run-record,
   evidence, analysis, and WEPP campaign contracts.
3. Fit all seven payloads at all 17 stations through the structurally bounded
   Daymet reader; emit source/fit manifests, diagnostics, goldens, mutations,
   and byte-repeat evidence.
4. Build and test the A5b-only overlay tool. Prove faithful inputs/goldens are
   unchanged and extension draws cannot perturb faithful streams.
5. Generate and seal all 1,904 candidate climates and post-hoc quality reports;
   validate exact matrix closure before analysis.
6. Regenerate the required baseline climates, execute the pinned WEPP matrix,
   validate every response record, and complete the sole candidate-manifest
   lifecycle transition.
7. Execute the frozen climate analyzer and observed-target bootstrap against
   that post-WEPP manifest, then attach downstream comparisons. Report every
   gate at both horizons without promoting a candidate.
8. Run repository and package gates, commission an independent review,
   disposition findings, and close the package honestly.

## Execution & dispatch

Execution starts from current `origin/main` in
`/Users/roger/src/cligen-rs`; the target branch is `main`. No side branch is
created. Subtasks share the same worktree and may not commit or push.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- 12 faithful `.cli` goldens remain byte-identical.
- All accepted A5a artifact hashes and offline verifiers pass.
- Fit sources are exactly the 17 archived objects; every fit has 30 complete
  years and no post-2009 contribution.
- Repeated fits and augmented station bundles are byte-identical.
- Fit/runtime/station/run/evidence schemas reject duplicate keys, nonfinite
  tokens, unknown fields, and the registered semantic mutations.
- Matrix closure is exactly 1,904 unique candidate records, 272 per candidate.
- Every report is envelope 2 / metrics 3 and defines the frozen baseline-
  eligible cell set.
- All seven fixed climate gates are evaluated at both horizons.
- WEPP records pass the pinned schema and semantic verifier, or the package
  closes on an explicit downstream hold without an A5c eligibility claim.

## Exit criteria

`EXECUTED-COMPLETE` requires complete fit, climate, uncertainty, and downstream
evidence; a deterministic per-candidate gate table at 30 and 100 years; an
independent accepted review; and no public profile promotion. A genuine
downstream-executable/deck failure closes as
`EXECUTED-HOLD-WEPP-EVIDENCE`, naming the exact missing asset and first
follow-on action. A fit, matrix, schema, or analysis defect closes under an
equally specific hold rather than a partial success claim.

## Artifacts

- `artifacts/freeze/` -- pre-output contracts and copied executable pins.
- `artifacts/fit/` -- deterministic fitter, source/fit manifests, station
  bundles, diagnostics, goldens, and mutation evidence.
- `artifacts/runtime/` -- plan/run-record/evidence tooling and conformance.
- `artifacts/climate/` -- sealed candidate evidence archive and analysis.
- `artifacts/wepp/` -- pinned executable/decks/adapter and response evidence.
- `artifacts/results.md` -- complete climate/downstream results and
  interpretation.
- `artifacts/analysis-evidence-v1.json` -- retained canonical analysis
  identities.
- `artifacts/gate-results.md` -- exact commands and terminal results.
- `artifacts/review.md` -- independent review and dispositions.
