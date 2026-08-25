# A11 forced stochastic generator ExecPlan

This living ExecPlan follows `.agent/PLANS.md` and coordinates the single
`20260825-a11-forced-monthly-annual-stochastic-generator` work package. It does
not split scientific stages into successor packages.

## Purpose / Big Picture

Deliver one inspectable, non-neural generator whose location climate is an
explicit forcing input and whose daily weather is sampled conditionally on
coherent annual/monthly targets. A successful end state is one sealed candidate
that passes integrated climate and WEPP development and then one untouched
confirmation. A failed scientific end state is equally complete: it identifies
which frozen family failed without launching another architecture campaign.

## Progress

- [x] 2026-08-25: inspected the A10/R15 terminal, roadmap, package catalog,
  governing ADRs/specifications, work-package template, and operator-supplied
  A11 thesis.
- [x] 2026-08-25: scaffolded the A11 package, revision-0 research
  specification, artifact inventory, roadmap/catalog entries, and this plan.
- [x] 2026-08-25: completed independent subagent review and dispositioned all
  three P1, two P2, and two P3 findings; no P0 finding was reported.
- [x] 2026-08-25: ratified revision 1 and published the strict evidence schema, design freeze,
  source manifest, calendar preflight, and resource/confirmation freezes before
  any candidate output.
- [x] 2026-08-25: attempted the forcing, target, and daily implementation; independent
  review rejected it for contract nonconformance before scientific evaluation.
- [x] 2026-08-25: retained attempt output only as invalid diagnostics and kept
  confirmation sealed.
- [x] 2026-08-25: completed independent review, repository gates, terminal, artifact/resource cleanup,
  and roadmap/catalog closeout.

## Surprises & Discoveries

- R2R5 produced an interpretable operational/scientific boundary: E0 completed,
  E1 became non-finite, E2C/E2 never started, and only 295 of the 616 authorized
  L40-minutes remained. An unchanged 515-minute study was not authorized.
- A10's pending next action was another E1 corrective package, while the new
  thesis explicitly removes neural training and GPU dependency. Treating A11
  as an R15 repair would therefore falsify both lineages.
- Existing repository authorities already cover PRISM input identity, Daymet
  calendar/missingness, observed climate metrics, and WEPP evidence lineage;
  A11 needs a new generator/forcing contract, not replacement copies of those
  surfaces.

## Decision Log

- Decision: close the planned R15 E1 corrective path at the existing R2R5 HOLD
  and begin A11 as a fresh research lineage. Rationale: A11 changes the model
  class, compute posture, and climate-interface thesis. Date/Author:
  2026-08-25, operator/Codex.
- Decision: keep all seven A11 stages inside one package and use incrementing
  operational attempt identities. Rationale: component promotion and
  administrative successor chains obscure coupled failures. Date/Author:
  2026-08-25, operator/Codex.
- Decision: make the revision-0 spec architectural but require revision-1
  numeric/schema ratification before output. Rationale: the supplied thesis
  fixes one architecture but does not provide safe numeric choices for every
  marginal, solver tolerance, estimator, threshold, or resource ceiling.
  Date/Author: 2026-08-25, Codex.
- Decision: preserve monthly means/variances and project an infeasible annual
  variance target to the nearest PSD-feasible boundary with an explicit
  receipt. Rationale: this is the stated prospective priority made total and
  fail-visible. Date/Author: 2026-08-25, Codex.
- Decision: implement the research candidate package-locally in Python 3.12.13
  with NumPy 2.3.5 Philox and binary64 linear algebra. Rationale: A11 has no
  production authority; this leaves faithful and public Rust behavior
  untouched while producing a reproducible scientific result. Date/Author:
  2026-08-25, Codex.
- Decision: use candidate-fit-only regional variation and daily texture with
  direct previously captured PRISM lookup at development coordinates.
  Rationale: no transferable site-specific variation product exists locally,
  and development target values may not masquerade as forcing. Date/Author:
  2026-08-25, Codex.
- Decision: retain the A5 WEPP response surface as mandatory even though its
  exact native executable/scenario materialization is absent locally.
  Rationale: compact prior responses cannot authenticate a new A11 climate
  substitution, and absence cannot be silently converted into a pass.
  Date/Author: 2026-08-25, Codex.

## Outcomes & Retrospective

A11 closed before scientific evaluation. Although the candidate-free calendar
preflight passed and attempt 0002 emitted 48 diagnostic streams, review found
that the implementation was not authenticated by its named commit, omitted the
annual state and mandatory oracle/evaluation surfaces, did not reconcile the
post-PRISM covariance, altered wet-count targets outside the frozen law, and
did not compute the frozen bootstrap gate. The recorded ratios are therefore
non-authoritative. Both attempt slots are spent; correction would require a new
prospective science contract rather than a relabeled retry. Confirmation
remained sealed, no target was accessed, and no production behavior changed.

## Context and Orientation

The owning authority is
`docs/work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/package.md`.
The research interface is
`docs/specifications/SPEC-A11-FORCED-STOCHASTIC-GENERATOR.md`. Required
artifacts are cataloged under the package's `artifacts/README.md`.

The implementation is expected to add an explicitly declared research path in
the appropriate `crates/` module only after revision-1 ratification. Faithful
code remains source-authority behavior and is not edited to host the extension.
Before implementation, inspect `crates/`, existing profile routing, generated
row/provenance types, quality measurement, PRISM orchestration, and WEPP
artifact producers; name exact files and seams in the revision-1 plan update.

## Plan of Work

### Milestone 1 — Ratified contract and preflight

Promote the research spec from revision 0 to revision 1. Add strict JSON
schemas and canonical positive/mutation examples for every cross-process
record. Build candidate-blind design, predecessor, forcing-source,
resource, and confirmation freezes. Complete the `SPEC-A10-CORPUS` calendar
and missingness preflight for every consumed Daymet object. Verify PRISM cell
coverage and exact bundle hashes. Freeze all marginal laws, latent contrasts,
numeric solvers/tolerances, RNG domains, region pooling, station roles,
replicates, evidence cells, thresholds, and WEPP inputs before producing a
candidate stream.

Acceptance is a byte-stable freeze whose verifier rejects missing identities,
role leakage, calendar mistakes, non-finite values, schema mutations,
confirmation access, and an unfrozen resource or decision field.

### Milestone 2 — Forcing and annual/monthly targets

Implement typed forcing input, requested/effective separation, deterministic
PSD reconciliation, and annual/monthly target sampling. Unit tests cover the
feasible interval, projection rule, singular matrices, dry/zero-variance
months, temperature weights, canonical serialization, RNG replay, and moment
recovery. A Monte Carlo verification uses only synthetic fixtures and
candidate-fit forcing; no development output informs parameter choices.

Acceptance is exact fixture replay and statistical recovery inside the frozen
tolerances with no malformed input accepted and no faithful-path change.

### Milestone 3 — Conditional daily oracle

Implement the exact-count first-order occurrence bridge, total-preserving
positive wet amounts, conditioned mean temperature and positive range, storm
descriptors, and secondary context. Preserve cross-month state explicitly.
Test every wet-count edge, zero-probability paths, amount normalization,
short/degenerate temperature months, support, compound conditions, and random
domain separation.

Acceptance is a complete daily stream whose realized monthly targets are
structural, whose replay and nested prefixes are exact, and whose support has
zero repair events because repair code does not exist.

### Milestone 4 — Integrated development

Materialize the exact four comparator arms for the frozen site roster and all
replicates as nested 100-year streams. Derive 30-year prefixes rather than
running separate paths. Score every frozen climate cell, then run the complete
pinned WEPP matrix for all mandatory arms. Keep component diagnostics visible,
but compute one integrated development decision.

Acceptance is a complete, hash-bound evidence matrix and exactly one `PASS` or
`FAIL` development result. Any missing mandatory cell, comparator-integrity
failure, or resource overrun is not a scientific pass.

### Milestone 5 — Conditional confirmation and closeout

On development `PASS`, seal the exact candidate, forcing/fit rules, evaluator,
WEPP surface, and confirmation manifest; atomically consume locked target bytes
once; execute the unchanged protocol; and emit pass or final failure. On
development `FAIL`, prove confirmation remained sealed and emit the final
development terminal. Reconcile every attempt and resource, run independent
review and repository gates, update the package/spec/plan, move completed A11
work out of the roadmap, and preserve large/restricted evidence by manifest.

Acceptance is one honest package terminal with zero unresolved P1/P2 findings,
verified cleanup, and no implicit production authorization.

## Concrete Steps

Run from `/Users/roger/src/cligen-rs` on current `origin/main`, pushing only to
`main`.

1. Re-read `AGENTS.md`, ADR-0001, the scientific coding standard, this plan,
   the package, and the revision-0 spec before implementation.
2. Inventory exact implementation seams with `rg` and record them in this plan.
3. Add schemas, canonical examples, and a package-local scaffold/design
   verifier; run it before any generator output.
4. Run the calendar/forcing preflight and record its exact command and receipt.
5. Implement milestones 2 and 3 with focused fixture tests preceding integrated
   use.
6. Run focused tests, then the full repository and coverage/CRAP gates.
7. Execute development only from a published source identity under the frozen
   resource ledger; append rather than replace attempt records.
8. Execute confirmation only if the machine development decision opens the
   firewall.
9. Close the package, plan, roadmap, catalog, review, gates, artifacts, and
   resources in the same terminal change.

The presently executable repository and closeout commands are:

```sh
git status --short --branch
git rev-parse HEAD
rg --files crates docs/specifications docs/work-packages | sort
rg -n "generation_profile|qc_filter|provenance|PRISM|WEPP" crates docs/specifications
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
git diff --check
```

The first four commands must show the expected branch/source identity and name
the exact implementation seams before code changes. The Cargo commands must
exit zero; coverage/CRAP becomes mandatory with the first production-function
change. `git diff --check` must be silent. Revision-1 ratification must replace
steps 3--8 above with exact package-local script paths, commands, inputs, and
expected receipts before candidate output; revision 0 does not invent commands
for nonexistent tools.

## Validation and Acceptance

Validation follows the package gates. In addition to schema and scientific
fixtures, every production function change triggers workspace coverage and
CRAP checks from its first introduction. The implementation must demonstrate
that faithful golden fixtures remain byte-identical, the new profile cannot be
selected implicitly, malformed forcing fails closed, and repeated execution
from identical state is byte-reproducible.

The climate evaluator must prove full cell enumeration and candidate-blind
threshold identity. WEPP records must bind climate, executable, inputs, parser,
and extraction definitions. Confirmation validation must prove the target was
unread before the atomic consume receipt and that no code/data identity changed
after the candidate seal.

## Idempotence and Recovery

Schema, fixture, preflight, and verifier commands are read-only or write only
to fresh package-local scratch paths. Canonical artifacts are replaced only
after hash verification and review. Generated candidate attempts use fresh
roots and incrementing IDs. Failed attempts are never deleted, relabeled, or
made to look scientifically complete; resource use accumulates.

Operational corrections remain in this package only while they preserve the
science-contract hash and aggregate resource ceiling. A correction that would
change science closes A11 at an honest terminal and requires new operator
authority. Confirmation access is not retryable after a scientific consume;
an ambiguous transition fails closed until the custodian record is reconciled.

## Artifacts and Notes

Commit bounded specifications, schemas, canonical examples, source, tests,
sanitized receipts, compact evidence, manifests, reviews, and terminal
summaries. Do not commit credentials, private absolute paths, raw locked target
series, large generated streams, or large WEPP outputs. Record their hashes,
byte counts, roles, storage class, retention state, and cleanup receipts.

Every evidence claim is labeled `Ran` or `Static`. A command transcript names
the source commit, tool versions, working directory, exit status, and output
identity without exposing sensitive environment details.

## Interfaces and Dependencies

The planned dependency surface is Rust/Cargo plus existing repository quality,
PRISM, station, corpus, and WEPP tooling. The candidate must not require
PyTorch, CUDA, a GPU, a mutable training service, or network access during
generation. Any new numerical dependency, optimizer, or distribution library
is pinned in Cargo and adjudicated for determinism before use.

Initial inputs are the immutable PRISM Norm91m runtime/source manifests, a
revision-1-frozen transferable variation product where one exists, the
role-correct A10M5R15R1/Daymet `candidate_fit` surfaces used only to construct
or fit authorized estimators and pooled texture, existing faithful/QC-off/PRISM
comparators, observed evaluation targets, and a pinned WEPP executable/input
matrix. Development and confirmation coordinates may query only an already
frozen transferable product; their target series cannot construct forcing.
A11 outputs remain research-only until a separately authorized promotion
changes public profile, runspec, provenance, and schema registries.

Revision note (2026-08-25): created the fresh A11 one-package plan and closed
the planned R15 numerical-corrective path without changing the R2R5 HOLD.
