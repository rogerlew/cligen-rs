# A5b Coefficient-Source Assessment

Status: `EXECUTED-COMPLETE`
Date: 2026-07-13
Evidence mode: Static

## Objective

Select and justify the daily gridded time-series source most suitable for
fitting production-format Fourier/EOF interannual coefficients for A5b, with a
focused comparison of Daymet V4 R1, PRISM AN daily, and gridMET. The result is
an input-data decision record for the later A5b scaffold; it does not select,
fit, or promote a generation model.

## Scope

Included:

- official product documentation and primary method literature for Daymet,
  PRISM, and gridMET;
- A5b-specific comparison of temporal lineage, coverage, calendar/day
  semantics, reproducibility, access rights, and suitability for monthly
  precipitation/Tmax/Tmin covariance and EOF estimation;
- compatibility with the fixed A5a corpus, 1980–2009 fit, and 2010–2025
  held-out evaluation;
- a ranked recommendation, required fit provenance, implementation work, and
  pre-fit decisions for production-format augmented station files.

Excluded:

- changing the A5 pre-registration or evaluation specification;
- acquiring new PRISM or gridMET data;
- defining the Fourier/EOF estimator, coefficient schema, station-model ID,
  or generation profile;
- fitting coefficients, producing candidate output, or reading A5b candidate
  results;
- changing faithful generation or the legacy `.par` contract.

## Authority

- A5 evidence contract:
  `docs/specifications/SPEC-A5-EVALUATION.md` and
  `docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/a5b-pre-registration.md`.
- A5 source-byte and coverage evidence:
  `docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/`
  and `references/observed/a5a-v1/`.
- Comparative claims: the official product records and primary papers linked
  in `artifacts/daily-source-assessment.md`, accessed 2026-07-13.
- This package is informational. It introduces no interface or generation
  behavior and therefore does not amend a specification.

## Plan

1. Restate the fixed A5b fit, held-out, station, and provenance constraints.
2. Establish each product's construction, coverage, calendar, revision model,
   rights, and source of monthly versus daily temporal variability.
3. Evaluate consequences for Fourier/EOF coefficients rather than generic
   daily-data quality.
4. Rank the products and define the minimum production fit contract,
   sensitivities, and implementation work.
5. Record unresolved pre-fit decisions without altering the fixed A5 record.

## Execution & dispatch

Executed on `main`; started from current `origin/main`; push target is `main`
if the operator later requests publication. Codex synthesized the report.
Parallel read-only assessments covered PRISM (`/root/prism_assessment`),
Daymet (`/root/daymet_assessment`), and gridMET
(`/root/gridmet_assessment`). No agent modified source data or generator code.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- Every product fact is supported by official documentation or primary
  literature; report inferences are identified as such.
- The recommendation is evaluated against the fixed A5b fit window and all 17
  A5 stations, not a generic CONUS use case.
- Product choice, evaluation target, station schema, coefficient schema,
  estimator, generation profile, and output schema remain independently
  versioned concepts.
- No A5b candidate output is produced or read.

The coverage/CRAP gates do not apply because this package changes no
production function under `crates/`.

## Exit criteria

Achieved 2026-07-13: the report ranks all three products, recommends a primary
and sensitivity role, identifies the calendar and finite-sample decisions that
must be frozen before fitting, and defines the lineage needed for
production-format coefficients. The report does not claim that the recommended
source is point-observation truth or authorize model promotion.

## Artifacts

- `artifacts/daily-source-assessment.md` — source-cited comparison,
  recommendation, and A5b implementation requirements.
- `artifacts/gate-results.md` — repository and static-evidence gate record.

