# A5d1b Finite-Path Realization Diagnosis

Status: `EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`
Date: 2026-07-14
Evidence mode: Mixed

## Objective

Resolve the first corrective action from A5d1 by determining whether its
30-/100-year finite-prefix failures arise from discrete year-count feasibility,
from bounded count construction, or from ordering/dependence construction.
If the count surface is feasible, prospectively test one count-first complete-
year path algorithm under the unchanged A5d1 contract.

## Scope

Included:

- reuse the accepted A5d1 256-year stationary weights, year features, and
  faithful-off development libraries at the same 17 exposed stations;
- decompose the 153 eligible A5d1 paths into order-independent count failures
  and order-dependent January-transition, boundary, and dependence failures;
- solve a joint nested 30-/100-year integer-count problem with exact calendar
  totals, positive stationary support, maximum reuse two, and the unchanged
  A5d1 preservation and centered annual rules;
- independently replay every solver certificate with the nonlinear centered
  calculations used by A5d1;
- only if all 17 stations pass count replay, construct and test 51 ordered paths
  across the three inherited seeds;
- preserve daily physical rows exactly and retain strict 30-year prefixes;
- issue a reviewed structural-selector result or the narrowest supported hold.

Excluded:

- changing any A5d1 tolerance, target, station, seed, library realization, or
  physical-value rule;
- inspecting or generating confirmation climate or WEPP output;
- changing production code, faithful generation, public schemas, station
  models, generation profiles, provenance, or output formats;
- promoting a candidate or authorizing A5d4/A5d5;
- treating bounded solver failure as a proof that all selector families are
  impossible.

## Authority

- [A5d1 contract v4](../20260714-a5d1-selector-feasibility/artifacts/selector-feasibility-contract-v4.json)
  remains immutable and governs all replayed climate, path, and invariant
  rules.
- [A5d1 decision](../20260714-a5d1-selector-feasibility/artifacts/a5d1-decision-v1.json)
  requires diagnosis under the valid 256-year stationary weights before a new
  path algorithm is introduced.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) governs quality
  measurement for extensions. [ADR-0001](../../decisions/0001-source-code-authority-port.md)
  and the vendored Fortran remain authoritative for unchanged faithful pool
  generation.
- The package introduces no interface surface and therefore no specification
  revision.

## Hypotheses and outcome classes

- **H1 (prospective):** all 17 pool-256 stationary solutions admit nested
  integer count vectors whose order-independent 30- and 100-year replays pass
  every frozen preservation and centered-annual rule.
- **H2 (prospective, conditional on H1):** the frozen count-first ordering
  algorithm passes the complete A5d1 path contract at all 17 stations and all
  three inherited seeds.
- **H3 (prospective):** exact physical rows, Gregorian calendar classes,
  maximum reuse, cooldown, positive support, and common-prefix invariants pass
  for every constructed path.

A mixed-integer solver status is diagnostic and is not described as a proof of
mathematical infeasibility because this package has no independently checkable
integer-infeasibility certificate. If the joint solve produces no witness,
separate 30- and 100-year solves localize the obstruction. Any absent witness
closes as a bounded count/common-prefix search hold. H2 failure after H1 passes
is a bounded ordered-path hold. These are scoped results, not universal
impossibility claims.

## Plan

1. Hash-lock A5d1 authorities, input manifests, target feature/certificate
   identities, tools, strict contract, source commit, and zero-confirmation
   exposure ledger before A5d1b outcomes.
2. Pass synthetic feasibility, infeasibility, nesting, determinism, calendar,
   reuse, and strict-replay fixtures.
3. Decompose the 153 inherited eligible paths by count-only and order-only
   gates.
4. Run the frozen joint nested integer-count solver at all 17 stations and
   independently replay each certificate.
5. If and only if all 17 count certificates pass, execute the 51-cell ordered
   path matrix and audit physical identity independently.
6. Finalize aggregate evidence, a machine decision, scientific report,
   consolidated review, closure manifest, gates, and roadmap/catalog status.

## Execution result

The inherited decomposition closed 153/153 eligible cells: 151 finite-prefix
first failures included a count-dependent failure, and only two existing
multisets passed count-only replay at both horizons. The controlling v5 count
run independently accepted every available incumbent and produced one exact
joint nested witness (`wy485345`) of the required 17. Separate diagnostics for
the other 16 stations produced no 30-year incumbent and 14 exact 100-year
witnesses. The all-station count gate therefore failed and the 51-cell ordering
matrix was skipped.

The package closes `EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`. This is a bounded
construction result, not a proof of integer infeasibility. No structural
algorithm, public candidate, A5d4 execution, or confirmation access is
authorized. The first follow-on is a prospective count-feasibility localization
package that audits row scaling and work allocation and compares an alternative
integer formulation before attempting nonlinear replay or ordering.

Two pre-result serialization amendments and two post-outcome corrections are
retained append-only. The v3 result was invalidated after review identified
discarded time-limit incumbents; the v4 certificates were invalidated after an
aggregate-only missing import. The controlling v5 run, invalidated histories,
and zero-confirmation exposure are all hash-bound.

## Execution & dispatch

Execution starts from source commit
`08db78cb5365b2f961599421826a600dae1c765a` on `main` in
`rogerlew/cligen-rs`; the working and push target is `main`. No side branch is
created. The lead alone edits artifacts, freezes the contract, opens A5d1b
outcomes, dispositions findings, and closes the package.

The scientific authoring protocol supplies independent read-only evidence,
methods, and authority extraction before drafting, followed by independent
accuracy, scientific-validity, and consistency/public-safety review. No agent
may edit, commit, push, access confirmation data, or change the frozen contract
after A5d1b outcomes exist.

## Gates

Repository gates:

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

Package-specific gates:

- strict JSON/schema validation, duplicate/nonfinite mutation rejection, and
  pre-outcome freeze identity;
- all inherited A5d1 hashes, all 17 feature files, and all 17 pool-256 marginal
  certificates reconcile;
- synthetic fixtures pass and deterministic repeats are byte-identical apart
  from explicitly excluded runtime fields;
- the diagnostic matrix contains exactly 153 inherited eligible cells and the
  count matrix exactly 17 station cells;
- every claimed feasible count certificate passes independent exact replay;
- ordered execution is absent unless all 17 count certificates pass;
- if ordered execution runs, it contains exactly 51 unique cells and every
  claimed pass independently satisfies the complete A5d1 contract and physical
  identity;
- zero confirmation exposure and zero production/public-surface changes;
- independent review has no open P1/P2 finding;
- `git diff --check` and local-link/public-safety checks pass.

Coverage/CRAP is not applicable unless production functions under `crates/`
change; such changes are outside this package's authority.

## Exit criteria

- `EXECUTED-COMPLETE-STRUCTURAL-SELECTOR`: H1–H3 pass for all registered cells;
  the selected structural algorithm may proceed to A5d4 only after A5d2 and
  A5d3 also close successfully.
- `EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`: the registered joint count search does
  not produce an exact nonlinear witness at every station.
- `EXECUTED-HOLD-COMMON-PREFIX-SEARCH-BOUNDED`: separate exact 30- and 100-year
  witnesses exist but the registered joint nested search produces no witness.
- `EXECUTED-HOLD-ORDERING-SEARCH-BOUNDED`: exact count replay passes all 17
  stations, but at least one frozen ordered-path search produces no complete
  witness.
- `EXECUTED-HOLD-RESOURCE`: the registered resource ceiling prevents matrix
  closure.
- `EXECUTED-HOLD-EXPOSURE`: any confirmation object is accessed.

Every hold names the first failed stage and the next corrective action. No hold
authorizes tolerance changes or confirmation access.

## Artifacts

- `artifacts/finite-path-realization-contract-v1.json` and strict schema —
  prospective experiment contract.
- `artifacts/evidence-lock-inputs-v1.json`, `pre-outcome-freeze-v1.json`, and
  `exposure-ledger.md` — immutable input and access boundary.
- `artifacts/pre-outcome-freeze-v2.json`, `pre-outcome-freeze-v3.json`,
  `corrected-execution-freeze-v4.json`, `corrected-execution-freeze-v5.json`,
  and four append-only amendments — complete execution chronology.
- `artifacts/*-results-v1.json` — synthetic, diagnostic, count, path, and
  aggregate evidence.
- `artifacts/count-witness-replay-audit-v1.json`,
  `resource-audit-v1.json`, and `next-action-disposition-v1.json` — independent
  replay, resource interpretation, and reviewed successor action.
- `artifacts/invalidated-v3-*`, `artifacts/invalidated-v4-*`, and
  `artifacts/history/` — preserved invalidated outcomes and frozen tool bytes.
- `../../reports/a5d1b-finite-path-realization-report.md` and manifest — public
  scientific report.
- `artifacts/review.md`, `gate-results.md`, and `closure-evidence-v1.json` —
  reviewed terminal record.
