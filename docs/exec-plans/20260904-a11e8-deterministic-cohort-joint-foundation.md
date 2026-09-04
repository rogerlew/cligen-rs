# A11E8 Deterministic Cohort Joint-Model Foundation ExecPlan

Status: scaffolded

## Purpose / Big Picture

A11E8 should show whether one temperature-only rank-one annual residual makes
faithful CLIGEN demonstrably better against observed development data and
whether a completely deterministic cohort selector adds value beyond the
underlying model. A model cannot pass by producing one lucky selected member.

## Progress

- [x] 2026-09-04: freeze the research question, model boundary, deterministic
  cohort semantics, burn cohorts, gates, and disposition vocabulary.
- [x] 2026-09-04: add the manifest/schema and executable deterministic
  contract vectors.
- [x] 2026-09-04: implement and synthetically validate the package-local fit,
  overlay, scoring, execution, evidence, and replay-ready provenance tools
  before candidate-output access.
- [ ] Publish exact execution source to `origin/main` and execute from that
  forty-character commit.
- [ ] Replay, review, run gates, and close the package and campaign records.

## Surprises & Discoveries

- A5f0 already retired a scalar IID state shared across four precipitation and
  temperature seams. A11E8 must remain temperature-only and explicitly test
  cross-month dependence; otherwise it would repeat a closed mechanism.
- A11E7 shows QC removal is material but far too small to close the structural
  deficit. Faithful QC remains the A11E8 base.

## Decision Log

- The end architecture is incrementally joint, but each component must earn
  retention against faithful before the next component is added.
- A11E8 adds only the thermal component. Hydroclimate state, coupling, memory,
  and seasonal expansion remain distinct possible successors.
- Model retention uses the complete unselected cohort. Selection is a separate
  runtime-algorithm question and cannot rescue a failed model.
- Cohorts use four explicit groups of eight existing A11E7 burns. Extension
  states use a domain-separated seed; parallel scheduling never enters the
  result.
- Integer-quantized lexicographic scores and faithful-first/index tie-breaking
  are frozen to make selection bit-reproducible and scientifically legible.
- The observed selector target is an oracle development input. A later
  transfer package must establish a legitimate runtime parameter source.

## Outcomes & Retrospective

Pending execution. Closure must compare the result with the goal of a simple,
nested joint model and state whether the component and selector independently
earned continuation.

## Context and Orientation

The specification is
`docs/specifications/SPEC-A11-DETERMINISTIC-COHORT-JOINT-FOUNDATION.md`.
The package is
`docs/work-packages/20260904-a11e8-deterministic-cohort-joint-foundation/`.
Its `artifacts/execution-manifest-v1.json` owns exact scientific constants;
`artifacts/contract.py` is the executable reference for manifest identity,
seed derivation, quantization, and selection.

A11E7 artifacts provide the faithful/QC evidence and exact station lineage.
A11E2 loads the normalized development observations. A11E5 supplies the
registered temperature metrics. A5f0 supplies the negative predecessor
boundary that prevents accidental revival of the overcoupled A5e0 mechanism.

## Plan of Work

Milestone 1 is the completed scaffold. Running the contract tests must show
that all 32 burns occur exactly once, seed vectors are pinned, selection is
input-order invariant, eligibility precedes scoring, and ties prefer faithful
then lower candidate index.

Milestone 2 is the scaffolded prospective executor. It first repeats the A10 calendar
preflight and authenticates dependencies. It then generates 640 faithful
streams, computes the frozen rank-one station loadings without candidate
output, derives 640 annual-state vectors, transforms only Tmax/Tmin/dewpoint,
and writes complete candidate and cohort manifests. Implementation and tests
must be published before this milestone executes against candidate output.

Milestone 3 scores all unselected records, selects one mixed-model and one
faithful-only record per station/cohort, applies the independent model and
selector gates, and emits the decision and cryptographic receipt. Expected
observable counts are 640 faithful streams, 640 derived candidates, 1,280
score records, and 80 selections of each selector scope.

Milestone 4 reruns from the same exact source commit in a clean deterministic
runtime. The loading bundle, latent states, score records, selections,
scientific evidence, and decision must be byte-identical. Review and repository
gates then close or honestly hold the package.

## Concrete Steps

Work from `/Users/roger/src/cligen-rs` on `main`. Before execution, fetch and
confirm `HEAD == origin/main`, run the prospective tests, commit the scaffold
with an imperative subject, push `main`, and record the exact commit.
Invoke the future executor only with that complete source commit. Do not use
confirmation data or amend the contract after candidate output.

After the first complete run, preserve its scientific artifacts outside the
package directory, rerun once in a fresh deterministic runtime, compare exact
bytes, and write a replay receipt. Record elapsed time separately because it
is operational, not scientific.

## Validation and Acceptance

Run the package Python tests and strict manifest validation, then the standard
Cargo formatting, lint, and test gates. If production functions are changed,
also run workspace LLVM coverage and CRAP with threshold 30. Validate every
JSON artifact, its self-hash where defined, the full stream/candidate/selection
hash chain, all changed Markdown links, and `git diff --check`.

Acceptance requires a contract-valid terminal disposition, complete
calendar/source/cohort identity, independent model and selector decisions,
confirmation=false, byte-identical replay, and review with no unresolved
P0/P1.

## Idempotence and Recovery

Execution writes into one deterministic package runtime under `target/` and
must refuse a pre-existing directory. It publishes scientific JSON atomically
only after the full grid validates and deletes the runtime in a `finally`
path. A failed or partial run publishes no decision and may be retried only
after the defect is corrected, the new source is committed and pushed, and a
new exact source commit is recorded.

## Artifacts and Notes

Committed compact evidence will include the calendar preflight, loading
bundle, cohort manifest, development evidence, decision, execution receipt,
cryptographic provenance receipt, replay receipt, review, and gate results.
Raw climates remain reproducible package runtime products unless a later
integrity finding requires retaining a bounded counterexample.

## Interfaces and Dependencies

No public interface is added. The research candidate and selector identifiers
are accepted only by package-local tools. A future public cohort CLI requires
its own specification, end-user documentation, failure semantics, and
provenance-schema revision after scientific support and parameter-transfer
evidence exist.

## Revision Note

2026-09-04: the initial scaffold was completed as runnable prospective source,
with architecture-pinned numerics and fail-closed ambiguous eigenpairs added
while preserving the original one-component scientific scope.
