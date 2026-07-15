# A7a — Daily Precipitation-Structure Baseline

Status: `EXECUTED-COMPLETE`
Date: 2026-07-14
Evidence mode: Mixed
Execution authorization: operator authorized scaffolding and execution on
2026-07-14

## Objective

Measure whether CLIGEN's generated daily precipitation structure differs
materially from the existing 17-station Daymet/GHCN corpus, rank the exposed
gap families, and determine whether a bounded analytic precipitation-model
feasibility study is warranted. This package changes no generator behavior and
tests no candidate model.

## Scope

Included:

- the existing 17 A5a station parameters and archived 1980–2025 Daymet targets,
  with the eight available GHCN stations used only as sensitivity evidence;
- the eight established burn offsets, 30- and 100-year horizons, and both
  `faithful` and `qc_filter: off` arms;
- seasonal R1mm wet/dry spell distributions, second-order occurrence
  residuals, adjacent wet-day amount dependence, seasonal wet-day upper tails,
  annual 1/3/5-day maxima, and monthly/annual precipitation dispersion;
- reuse of all hash-identical A5a quality reports and regeneration of only the
  nested 100-year daily streams needed for new sequence metrics;
- a deterministic trajectory-spread null, ranked gap families, GHCN
  sensitivity, QC-arm comparisons, and noncausal propagation diagnostics; and
- a public scientific report under the active report standard and protocol.

Excluded:

- a candidate precipitation mechanism, coefficient fit, station-file change,
  generation profile, public quality schema, production Rust change, WEPP run,
  or promotion claim;
- post-generation repair, selector/count optimization, annual latent state,
  storm-descriptor evaluation, or winter-process adjudication; and
- causal claims that a daily gap produces monthly or annual dispersion error.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) keeps faithful
  generation governed by the vendored Fortran. A7a observes rendered output
  and changes no faithful path.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) requires
  measurement before model adjudication.
- [A5a](../20260712-a5a-quality-v3-observed-corpus/package.md) supplies the
  hash-pinned corpus, station parameters, quality-v3 reports, horizons, and
  burn membership.
- `artifacts/measurement-contract-v1.json` is the frozen package-local
  measurement and decision contract. It is not a public schema.

## Plan

1. Scaffold the package, contract, analyzer, verifier, and evidence freeze
   before generating or inspecting any new A7a-derived outcome.
2. Rebuild the release binary, extract the exact A5a station parameters, and
   regenerate 272 nested 100-year streams; obtain each 30-year analysis as the
   exact prefix of its corresponding stream.
3. Cross-check all overlapping rederived metrics against the 544 retained A5a
   quality reports, then derive the new higher-order and seasonal evidence.
4. Apply the frozen trajectory-null and decision rule, rank gap families, and
   render canonical analysis, decision, and findings artifacts.
5. Apply the scientific-report protocol's independent extraction and review
   lenses, disposition findings, run mechanical/repository gates, and close
   with exactly one terminal roadmap decision.

## Execution & dispatch

Execute locally on `main`, starting from clean commit
`d27a008e91a4853044aed5207d02a3aeb631ac8c` and targeting `main` only when the
operator separately requests publication. No side branch or pull request is
authorized.

The A7a derivation and decision contract are frozen before new A7a output, but
the parent A5a data and related quality-v3 summaries were already exposed.
Claims must therefore describe the exact A7a calculations as prospectively
specified without calling the parent evidence independently sealed.

## Gates

- all frozen source, corpus, archive, analyzer, verifier, and contract hashes
  match the pre-analysis freeze;
- exactly 272 100-year streams are regenerated and yield 544 nested horizon
  records: 17 stations × 2 QC arms × 8 burns × 2 horizons;
- every daily stream has the expected Gregorian row count and deterministic
  replay identity;
- all overlapping spell, dependence, tail, maxima, and dispersion values
  agree with the retained quality-v3 reports within the frozen numeric rule;
- all observed raw-source identities and overlapping observed-target values
  match A5a;
- the decision and ranking follow the frozen contract without threshold
  amendment after outcome access;
- the report verifier, independent review lenses, public-safety checks, and
  package verifier pass with no open P1/P2 finding;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage and CRAP gates are not applicable because A7a changes no production
function under `crates/`.

## Execution result

Terminal scientific disposition: `DAILY-PRECIPITATION-GAP-MEASURED`.

- The analyzer regenerated all 272 nested 100-year streams and derived 544
  30-/100-year records. All 24,480 retained-quality-report overlap checks and
  1,125 observed-target overlap checks passed.
- `spell_structure` and `higher_order_occurrence` crossed the Daymet-off,
  faithful, and GHCN-off breadth guards at both horizons. A7b is permitted but
  remains unscaffolded and requires separate operator dispatch.
- Internal extraction found three calculation defects after the first result:
  pooled severity aggregation, zero-null severity handling, and unmatched
  observed/null component support. Amendment 005 corrected and fully reran the
  analysis. The rank order, qualifying families, and terminal disposition did
  not change; corrected output identities are bound by
  `post-analysis-freeze-v2.json`.
- The reference audit preserved the frozen R04 identity and added the GHCN
  dataset and official Daymet guide through reference-corpus amendment 006.
- The public report and three-lens review are accepted with zero open P1/P2
  findings. Package, report, repository, and public-safety gates pass.

## Exit criteria

`EXECUTED-COMPLETE` requires complete source integrity, reproducible analysis,
accepted review/report records, all gates passing, and exactly one terminal
scientific disposition:

- `DAILY-PRECIPITATION-GAP-MEASURED` permits the separately dispatched A7b
  analytic feasibility package; or
- `NO-DAILY-STRUCTURE-PRIORITY` closes the roadmapped A7 precipitation line.

Missing or mismatched A5a evidence holds
`EXECUTED-HOLD-PARENT-EVIDENCE`; analysis or review defects hold
`EXECUTED-HOLD-ANALYSIS-DEFECT`. A7a itself never implements A7b.

## Artifacts

- `artifacts/design.md` — interpretation and access boundary.
- `artifacts/measurement-contract-v1.json` — frozen metrics, comparisons, and
  decision rule.
- `artifacts/analyze-a7a.py` — deterministic generator/analysis pipeline.
- `artifacts/verify-a7a.py` — freeze, arithmetic, scope, and reproduction gate.
- `artifacts/pre-analysis-freeze-v1.json` — pre-output identities.
- `artifacts/pre-analysis-freeze-v2.json` through
  `artifacts/pre-analysis-freeze-v4.json` — bounded pre-analysis correction
  and component-availability history.
- `artifacts/pre-analysis-amendment-001.md` through
  `artifacts/analysis-amendment-003.md` — prospective amendment records.
- `artifacts/post-analysis-amendment-004.md` and
  `artifacts/post-analysis-freeze-v1.json` — first-result renderer correction
  and preserved canonical identities.
- `artifacts/post-analysis-amendment-005.md` and
  `artifacts/post-analysis-freeze-v2.json` — internal-review arithmetic and
  same-support correction.
- `artifacts/reference-corpus-amendment-006.md` — stable reference-ID and
  citation-corpus amendment.
- `artifacts/a7a-analysis-v1.json` — canonical complete analysis.
- `artifacts/a7a-decision-v1.json` — terminal decision and ranked families.
- `artifacts/findings.md` — concise generated findings.
- `artifacts/claim-evidence-ledger.md` — frozen report claim ledger.
- `artifacts/review.md` — consolidated independent review and dispositions.
- `artifacts/gate-results.md` — exact commands and outcomes.
- `../../reports/a7a-daily-precipitation-structure-report.md` — accepted public
  scientific report.
