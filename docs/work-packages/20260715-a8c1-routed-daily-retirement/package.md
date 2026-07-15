# A8c1 — Routed-Daily Runtime Retirement

Status: `EXECUTED-COMPLETE`
Date: 2026-07-15
Evidence mode: Mixed
Scaffolding authorization: operator authorized on 2026-07-15
Execution authorization: operator dispatched on 2026-07-15

## Objective

Remove the stopped, unpromoted `a8c_routed_daily_v1` experimental runtime from
current `main` while preserving the complete A8a--A8c scientific record,
historical reproducibility, and faithful CLIGEN behavior. This is retirement
hygiene before the A9 successor-family foundation; it does not repair A8c,
select a successor model, or change the public default.

## Scope

Included:

- audit crates.io, repository releases/tags, package version, and source
  history to determine whether any A8c profile, station-document revision 2,
  or model identifier shipped;
- freeze a baseline manifest covering every candidate removal surface and
  every A8a--A8c record that must retain its exact bytes;
- remove `a8c_routed_daily_v1`, `a8c_integrated_daily_v1`, the A8c fit IDs,
  revision-2 routed station payload, routed precipitation implementation,
  model-specific tests, and all closed-enum/schema combinations that exist
  only to admit the stopped profile;
- remove A8c-only branches from runspec resolution, generation, typed and
  Parquet output, provenance, and quality reporting;
- evaluate every touched seam independently and retain it only when a current,
  non-A8c contract and consumer are demonstrated;
- mark the A8c specification and registries as retired without rewriting the
  accepted experiment record;
- preserve the LFS evidence archive, manifests, analyses, decision, review,
  and all A8a/A8b parent evidence; and
- verify faithful golden identity, schema/runtime-mirror agreement, package
  contents, historical commit reachability, and all repository gates.

Excluded:

- deleting, regenerating, or editing A7/A8 scientific analyses, decisions,
  reports, retained streams, source-data archives, or frozen manifests;
- retaining a compatibility shim merely to make the A8c candidate available;
  if release exposure is found, execution stops for an explicit semver and
  deprecation decision;
- reusing A8c station document v2 as the A9 fit schema without A9a design and
  review;
- implementing the A9 family, calibration harness, candidate model, fit
  artifact, or generation profile;
- changes to faithful arithmetic, legacy `.par` interpretation, source RNG
  streams, defaults, or `reference/cligen532/`; and
- crate release, crates.io publication, openWEPP, WEPPcloud, PyO3, or other
  consumer integration.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) protects the
  faithful generator, precision map, and vendored-source authority.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) distinguishes
  faithful compatibility from scientific extension quality.
- [A8c](../20260715-a8c-routed-daily-pilot/package.md) and its
  [consolidated review](../20260715-a8c-routed-daily-pilot/artifacts/review.md)
  close the candidate on `STOP-A8-ROUTED-DAILY` and explicitly deny A8d,
  retuning, confirmation, or promotion.
- [A8a](../20260715-a8a-dry-regime-applicability/package.md) and
  [A8b](../20260715-a8b-secondary-year-fallback/package.md) remain immutable
  parent evidence; retirement must not reinterpret their analytic results.
- [A5f1](../20260714-a5f1-retired-a5e0-runtime-cleanup/package.md) supplies the
  accepted release-exposure, immutable-record, historical-reachability, and
  faithful-restoration retirement precedent.
- The [current roadmap](../../ROADMAP.md) orders A8c1 before A9a and requires
  compatibility axes to be dispositioned independently.
- The [Rust scientific coding standard](../../standards/rust-scientific-coding-standard.md)
  governs every production edit made during execution.

## Presumptive surface disposition

The static scaffold inventory is recorded in
[`artifacts/retirement-surface-inventory.md`](artifacts/retirement-surface-inventory.md).
It is not the execution baseline manifest. The presumptive rule is:

- remove A8c identifiers, coefficients, routes, runtime state, tests, and
  schema branches;
- retain the accepted A8a--A8c evidence bytes and historical commit;
- retain a generic helper only if execution records its independent contract,
  current consumer, tests, and reason that reimplementation would be harmful;
  and
- otherwise restore the affected source to its pre-A8c shape using history as
  a comparator, never by altering faithful numerical expressions from memory.

## Plan

1. Audit release exposure and capture the clean `fdd35f6` baseline, exact
   removal candidates, preserved-record hashes, and pre-A8c comparator commit.
2. Review the static inventory against compiler references, Cargo targets,
   published schemas, and package contents; classify each surface as remove,
   retain-generic, preserve-evidence, or hold-for-exposure.
3. Update retirement status and accepted schema registries before removing
   production branches; keep documentation history and runtime mirrors
   mutually consistent.
4. Remove only the model-specific runtime, station, profile, provenance,
   quality, output, and test surfaces authorized by the final inventory.
5. Verify source absence, immutable-record identity, historical reachability,
   faithful byte parity, accepted schema combinations, and full repository plus
   coverage/CRAP gates; conduct one consolidated retirement review.

## Execution & dispatch

When separately dispatched, execute locally on `main` from current
`origin/main`, beginning with commit
`fdd35f60241f25663614db46142bfe3683c6ce5f` or a documented descendant, and
push only to `main` if the kickoff authorizes publication. Do not create or
adopt a side branch. A9a may remain scaffolded but may not execute until A8c1
closes successfully.

The release-exposure decision precedes destructive source edits. If the A8c
surface shipped, stop at `EXECUTED-HOLD-RELEASE-EXPOSURE`; do not infer that an
experimental label makes removal semver-safe.

Execution began from clean `main` at
`49a67775d22f0452bbf65f0a1ad35435e0d340f9`, a documented descendant of the
A8c implementation commit. The exposure audit returned `REMOVAL-SUPPORTED`.
All A8c-specific runtime surfaces were removed, shared files were restored to
the exact pre-A8c comparator, and publication was not requested by this
dispatch.

## Gates

- official registry/release/tag audit supports removal;
- baseline hashes cover every removed file and every preserved A7/A8 record;
- no A8c profile, model, fit, route, station-document-v2, runtime, schema,
  output, quality, or test surface remains unless the reviewed inventory gives
  a specific independent-retention justification;
- the A8c implementation commit and retained LFS object remain reachable and
  content-verifiable;
- all preserved A8a--A8c scientific records retain baseline hashes;
- documentation and runtime schema mirrors agree and contain no accepted A8c
  profile/model combination;
- faithful `.cli` goldens and existing revision-1/legacy station inputs remain
  byte-identical;
- `cargo metadata` and `cargo package --list` expose no retired runtime target;
- review has zero open P1/P2 findings;
- `git diff --check`;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`;
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`; and
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
  --fail-above`.

## Exit criteria

`EXECUTED-COMPLETE` requires a supported unshipped-removal decision, complete
model-specific cleanup, independently justified generic retention only,
unchanged scientific records, faithful parity, review acceptance, and all
gates passing. Its terminal is `A8C-ROUTED-DAILY-RUNTIME-RETIRED` and it
authorizes A9a execution only.

Legitimate holds are:

- `EXECUTED-HOLD-RELEASE-EXPOSURE` — a shipped surface requires a separate
  deprecation/semver decision before source removal;
- `EXECUTED-HOLD-RECORD-INTEGRITY` — a preserved A7/A8 record or LFS identity
  cannot be verified;
- `EXECUTED-HOLD-FAITHFUL-REGRESSION` — faithful output or legacy/revision-1
  intake changes; or
- `EXECUTED-HOLD-SURFACE-AMBIGUITY` — a seam cannot yet be classified as
  A8c-specific or independently generic.

No hold authorizes partial retirement, A8c repair, or A9 implementation.

## Execution result

`EXECUTED-COMPLETE` with terminal
`A8C-ROUTED-DAILY-RUNTIME-RETIRED`.

- 27 current-interface surfaces were dispositioned: four A8c-only files were
  deleted, 22 shared/current files were restored byte-for-byte to the pre-A8c
  comparator, and the specification registry now retains only a retired
  historical A8c entry.
- All 148 frozen A7/A8, observed-source, LFS-configuration, public-report, and
  A9a scaffold records retain their exact baseline identities.
- The accepted A8c archive remains Git-LFS-managed and content-verifiable; the
  implementation commit remains reachable.
- Faithful golden parity, revision-1 station parity, Cargo package-surface,
  full repository, coverage, and CRAP gates pass.
- Consolidated review found zero open P1/P2 findings.

A9a remains scaffolded and unexecuted. This terminal satisfies its predecessor
condition but does not constitute its separate execution dispatch.

## Artifacts

- `artifacts/retirement-surface-inventory.md` — scaffold-time static map and
  execution classification rules.
- `artifacts/release-exposure-audit.md` — official registry, tag, release,
  package-version, and semver evidence produced during execution.
- `artifacts/capture-a8c1-baseline.py` and `artifacts/a8c1-baseline-v1.json` —
  pre-removal source and preserved-record identity manifest.
- `artifacts/removal-inventory.md` — reviewed final disposition of every
  surface.
- `artifacts/verify-a8c1.py` — source absence, record preservation, historical
  reachability, schema, and package verifier.
- `artifacts/review.md` — correctness, compatibility, and scope review.
- `artifacts/gate-results.md` — executed commands and outcomes.
