# A7b — Analytic Precipitation-Model Feasibility

Status: `EXECUTED-COMPLETE`
Date: 2026-07-14
Evidence mode: Mixed
Execution authorization: operator authorized scaffolding and execution on
2026-07-14

## Objective

Compare two bounded daily precipitation mechanisms motivated by A7a's
qualifying spell/occurrence gaps, certify their stationary monthly and
wet-amount moment budgets before generator integration, and select exactly one
mechanism for a separately dispatched A7c pilot or stop the precipitation
line. This package changes no production Rust, station model, generation
profile, or public schema and emits no CLIGEN candidate climate.

## Scope

Included:

- the hash-pinned 17-station A5a Daymet corpus over 1980--2025 and the exact
  fixed-monthly station parameters retained by A5a;
- one second-order binary occurrence kernel and one two-phase semi-Markov
  occurrence kernel, each seasonally fitted and monthwise recentered to the
  legacy stationary wet-day fraction;
- one shared occurrence-conditioned wet-amount model: a positive log-quantile
  spline with explicit p95/p99 knots and one Gaussian-copula persistence state
  that resets after a dry day;
- deterministic quadrature of wet-amount moments/covariances and exact
  finite-window occurrence matrices for 28-, 30-, and 31-day monthly-total
  mean/variance budgets;
- fit-identifiability, probability/support, wet-amount variance-retention,
  tail-fidelity, stationary-kernel, deterministic-RNG-ownership, and
  no-post-repair gates; and
- the three A7c development stations as a mandatory surface, with the full
  17-station/204-month-cell corpus as breadth evidence.

Excluded:

- generator integration, candidate `.cli` output, station-schema/profile
  publication, Rust production code, WEPP execution, or promotion;
- path selection, fixed-count optimization, post-generation repair, annual
  latent state, selector libraries, or month-total conditioning; and
- a claim that analytic feasibility predicts climate improvement.

## Authority

- [A7a](../20260714-a7a-daily-precipitation-structure-baseline/package.md)
  authorizes A7b through `DAILY-PRECIPITATION-GAP-MEASURED`; its accepted
  result does not select a mechanism.
- [ADR-0001](../../decisions/0001-source-code-authority-port.md) keeps faithful
  behavior governed by the vendored Fortran. A7b reads the legacy monthly
  precipitation contract but changes no faithful path.
- `artifacts/feasibility-contract-v1.json` is the package-local frozen
  candidate, analytic, and selection contract. It is not a public interface.

## Plan

1. Freeze the candidate identities, seasonal fits, monthly recentering,
   moment-budget equations, quadrature, identifiability bounds, RNG ownership,
   and selection rule before producing any candidate-specific result.
2. Reconstruct exact f32-widened legacy wet-day fraction/amount targets and
   the archived Daymet daily sequences for all 17 stations.
3. Fit both occurrence shapes and the common wet-amount shape by season;
   recenter each occurrence kernel and reallocate wet-amount variance for all
   204 station-month cells without increasing the legacy amount variance.
4. Apply the frozen admissibility and lexicographic selection rule, producing
   canonical analysis, decision, and concise findings artifacts.
5. Independently recompute matrix arithmetic and key invariants, run package
   and repository gates, and close A7b with exactly one terminal disposition.

## Execution & dispatch

Execute locally on `main`, starting from clean commit
`3e18728b4c63c17be922e98199948c1b7da8002e` and target `main` only if the
operator separately requests publication. No side branch or pull request is
authorized.

The parent A7a/A5a evidence is already exposed. Candidate-specific seasonal
fits, recentered kernels, moment budgets, ranking, and terminal decision are
frozen prospectively relative to new A7b output. Parser or implementation
defects discovered before outcome access require bounded amendments; outcome-
time threshold changes are prohibited.

## Gates

- all contract, analyzer, verifier, parent-input, and source identities match
  the pre-analysis freeze;
- exactly 17 stations, 68 station-season amount fits, 136 candidate-season
  occurrence fits, and 408 candidate station-month cells are represented;
- every available monthly kernel matches its legacy stationary wet fraction;
- every feasible cell has finite positive wet amounts, no probability outside
  the frozen guard, no wet-amount variance increase, and a monthly-total
  variance error within the frozen tolerance;
- deterministic RNG ownership uses a fixed two draws per calendar day with
  domain-separated occurrence and amount streams and no path/count repair;
- selection follows the frozen mandatory-development/corpus breadth and
  lexicographic rule, yielding exactly one terminal disposition;
- the independent package verifier and review have no open P1/P2 finding;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage and CRAP gates are not applicable because A7b changes no production
function under `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires reproducible analysis, accepted review, all gates
passing, and exactly one terminal scientific disposition:

- `SELECT-O2-LOGQSPLINE-GAUSSIAN-COPULA-A7C` selects the second-order kernel;
- `SELECT-SM2-LOGQSPLINE-GAUSSIAN-COPULA-A7C` selects the two-phase
  semi-Markov kernel; or
- `STOP-PRECIPITATION-LINE` means neither mechanism met the frozen feasibility
  surface and A7c is not authorized.

Input/freeze defects hold `EXECUTED-HOLD-PARENT-EVIDENCE`; calculation or
review defects hold `EXECUTED-HOLD-ANALYSIS-DEFECT`. A7b itself never
implements A7c.

## Result and disposition

The authoritative analysis returned `STOP-PRECIPITATION-LINE`. Each registered
parameterization had 192/204 feasible corpus cells, above the 184-cell breadth
floor, but only 31/36 mandatory development cells rather than 36/36. All five
development failures were at Death Valley: April and December exceeded the
tail-log-error bound, while June--August inherited the JJA fit's 14 adjacent
wet pairs and 14 long-wet-state exposures, both below the frozen minimum of 25.

Review found that the second-order and registered two-phase semi-Markov state
systems are algebraically equivalent under relabeling. A7b therefore tested
one unique four-state occurrence mechanism through two parameterizations, not
two independent model classes. The correction does not change the stop: the
infeasible cells are identical, neither parameterization qualifies, and no
A7c mechanism is selected. The stored ranking is not interpreted.

The first invocation stopped before candidate-data access because it queried
the wrong A7a terminal key. Pre-analysis amendment 001 records the one-token
schema-path correction, original and amended hashes, and absence of outcome
artifacts. The amended freeze, independent calculation/reproduction verifier,
scope-corrected review, and all repository gates pass. No generator climate,
production function, schema, profile, or public interface was created.

## Artifacts

- `artifacts/design.md` — model equations and interpretation boundary.
- `artifacts/feasibility-contract-v1.json` — frozen candidates and gates.
- `artifacts/analyze-a7b.py` — deterministic fit and certification pipeline.
- `artifacts/verify-a7b.py` — freeze, arithmetic, identity, and reproduction
  verifier.
- `artifacts/pre-analysis-freeze-v1.json` — source and input identities.
- `artifacts/pre-analysis-amendment-001.json` — bounded parent-key correction
  before candidate-data access.
- `artifacts/a7b-analysis-v1.json` — canonical fits and cell evidence.
- `artifacts/a7b-decision-v1.json` — candidate summaries and terminal result.
- `artifacts/findings.md` — concise generated findings.
- `artifacts/post-analysis-equivalence-review.md` — occurrence-state
  isomorphism proof and scope correction.
- `artifacts/verify-equivalence.py` — reproducible paired-parameterization
  review check.
- `artifacts/review.md` — independent calculation and scope review.
- `artifacts/gate-results.md` — exact commands and results.
