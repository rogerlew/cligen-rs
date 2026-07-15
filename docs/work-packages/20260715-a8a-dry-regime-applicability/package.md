# A8a — Dry-Regime Applicability Boundary and Confirmation Corpus

Status: `EXECUTED-COMPLETE`
Date: 2026-07-15
Evidence mode: Mixed
Execution authorization: operator authorized scaffolding and execution on
2026-07-15

## Objective

Define and confirm a conservative station-level applicability partition for
the one unique A7b four-state daily precipitation mechanism. Select a disjoint
arid, semi-arid, monsoonal, and control panel before accessing new daily data;
then test whether an explicit `integrated_daily` versus fallback boundary is
stable enough to dispatch A8b. A8a changes no generator, station schema,
generation profile, or public interface and emits no candidate climate.

## Scope

Included:

- the eight already exposed A5a arid/monsoonal stations as development
  evidence only;
- a metadata-selected, hash-pinned confirmation panel from public `us-2015`
  station collection version `2026.07`, with at least four stations in each of
  hot-arid, cold-arid, non-monsoonal semi-arid, and monsoonal-transition
  strata plus at least four humid/cold negative controls;
- exact selected legacy parameter files and Daymet V4 R1 daily precipitation,
  Tmax, and Tmin for 1980--2025, with GHCN-Daily sensitivity where an exact
  U.S. Cooperative station identifier supplies adequate coverage;
- a prospective station-level classifier based on seasonal support,
  uncertainty, amount-tail/variance-retention margins, and monthly
  variance-reallocation slack;
- held-out confirmation behavior, ambiguity, shortened-record, year-block,
  and available Daymet/GHCN stability evidence; and
- analytic application of the single A7b second-order/log-quantile/Gaussian-
  copula construction to stations classified `integrated_daily`.

Excluded:

- candidate climate generation, Rust production code, runtime routing,
  station-schema/profile publication, WEPP execution, or promotion;
- changing A7b thresholds or treating its isomorphic O2/SM2 representations
  as different mechanisms;
- selecting stations after daily-data access, station substitution, hidden
  fallback, output-time path selection, count optimization, or repair; and
- designing or selecting the A8b interannual fallback.

## Authority

- [A7b](../20260714-a7b-analytic-precipitation-feasibility/package.md)
  supplies the closed whole-domain stop, the unique bounded daily mechanism,
  and the analytic budget equations. A8a is a new applicability-domain study,
  not an amendment or rescue of A7b.
- [ADR-0001](../../decisions/0001-source-code-authority-port.md) keeps faithful
  behavior governed by the vendored Fortran; A8a reads legacy monthly
  parameters but changes no faithful path.
- `artifacts/selection-contract-v1.json` and
  `artifacts/analysis-contract-v1.json` become package-local frozen contracts
  before selection and daily-source access, respectively.

## Plan

1. Inventory only the immutable `us-2015` catalog and parameter files; freeze
   descriptor calculations, strata, exclusions, geographic separation, and
   deterministic selection before any new daily record is accessed.
2. Select and identity-pin the confirmation panel and exact parameter bytes;
   then freeze the daily-source, classifier, uncertainty, analytic, and
   terminal contract.
3. Acquire immutable Daymet/GHCN source extracts, build the observed support
   evidence, classify stations, and run the frozen A7b analytic mechanism on
   every eligible confirmation station.
4. Recompute partition, stability, analytic, identity, and terminal evidence
   independently; perform scientific and public-safety review.
5. Run repository gates and close A8a on exactly one terminal disposition.

## Execution & dispatch

Execute locally on `main` from clean commit
`26f581b99b425ef9699ec85d9322ff72b0b8bdd3`; push only to `main` if the
operator separately requests publication. No side branch or pull request is
authorized.

The local station cache may be read before the selection freeze only after its
catalog hash matches the public collection manifest. New Daymet or GHCN daily
records may not be requested, opened, or inspected until the exact station
panel and analysis contract are frozen. A retrieval failure may record a
source as unavailable but may not substitute another station.

## Gates

- selection uses only the hash-pinned station catalog and parameter bytes and
  represents all five registered strata at their minimum breadth;
- exact station identifiers, coordinates, parameter hashes, source URLs,
  record periods, and no-substitution rules are frozen before daily access;
- all archived source hashes, logical-record hashes, calendars, coverage, and
  licenses/attribution boundaries verify offline;
- every classification and analytic cell follows the frozen estimator,
  uncertainty, fit, tail, variance-retention, and monthly-budget rules;
- held-out and stability guards yield exactly one terminal disposition;
- review has zero open P1/P2 findings;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage and CRAP gates are not applicable because A8a changes no production
function under `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires reproducible selection, archived sources,
classification and analytic evidence, accepted review, passing repository
gates, and exactly one terminal:

- `CONTINUE-A8B-DRY-PARTITION` confirms one explicit applicability partition
  and the scoped eligible-domain daily mechanism; or
- `STOP-DRY-REGIME-PARTITION` means the classifier or mechanism is not stable
  enough for explicit routed development.

Input/freeze defects hold `EXECUTED-HOLD-PARENT-EVIDENCE`; acquisition defects
that leave the registered primary panel incomplete hold
`EXECUTED-HOLD-SOURCE-ACQUISITION`; calculation/review defects hold
`EXECUTED-HOLD-ANALYSIS-DEFECT`.

## Execution result

A8a returned `CONTINUE-A8B-DRY-PARTITION`. The frozen confirmation result is
15 `integrated_daily` stations and five `legacy_daily_fallback` stations; all
eight terminal guards pass. The dry/transition subset contains 11 integrated
and five fallback stations, all four negative controls are integrated, and
all eight exposed development classifications reproduce A7b. Full-record to
shortened-window agreement is 0.850. Monsoonal and other-dry instability are
both 0.1875, so no monsoonal-specific successor is justified.

The official GHCN station-list metadata exposed one pre-outcome parser defect:
station names are UTF-8 rather than ASCII. Amendment 001 and successor freeze
v2 record that the failure occurred before any Daymet or GHCN station series,
source manifest, or outcome existed and changed only strict station-list
decoding plus freeze provenance. All 20 fixed Daymet primary series were then
archived; two of three exact Cooperative matches met the descriptive GHCN
coverage rule. Independent verification reproduced every result byte and the
consolidated review accepted the evidence with zero open P1/P2 findings.

No climate was generated and no production function, runtime route, schema,
profile, or public default changed. A8b is now the next roadmapped package and
must accept this explicit partition without reopening it.

## Artifacts

- `artifacts/inventory-stations.py` — metadata-only station descriptor census.
- `artifacts/selection-contract-v1.json` — frozen strata and deterministic
  panel-selection rules.
- `artifacts/station-inventory-v1.json` and `artifacts/panel-v1.json` — complete
  descriptor census and selected station identities.
- `artifacts/analysis-contract-v1.json` — frozen sources, classifier,
  stability, analytic, and terminal rules.
- `artifacts/pre-analysis-freeze-v1.json`,
  `artifacts/pre-analysis-amendment-001.json`, and
  `artifacts/pre-analysis-freeze-v2.json` — prospective boundary and bounded
  UTF-8 source-parser amendment chain.
- `artifacts/acquire-a8a.py` and `references/observed/a8a-v1/` — immutable
  observed-source acquisition and archive.
- `artifacts/analyze-a8a.py` and `artifacts/verify-a8a.py` — canonical analysis
  and independent verification.
- `artifacts/a8a-analysis-v1.json`, `artifacts/a8a-decision-v1.json`, and
  `artifacts/findings.md` — reproducible result.
- `artifacts/review.md` and `artifacts/gate-results.md` — closure evidence.
