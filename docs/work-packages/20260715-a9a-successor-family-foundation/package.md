# A9a — Stochastic Successor-Family Foundation

Status: `SCAFFOLDED`
Date: 2026-07-15
Evidence mode: Static and derived planning
Scaffolding authorization: operator authorized on 2026-07-15
Execution authorization: conditional on successful A8c1 retirement and a
separate operator dispatch

## Objective

Define a calibration-first stochastic climate-generator family that jointly
treats precipitation occurrence, wet-day amount, storm descriptors, and the
daily context consumed by other meteorological variables. Establish an
optimizer-neutral tuning harness, climate-regime coverage, fit/provenance
contract, and strict development-versus-confirmation boundary before any A9
candidate is fitted, generated, or implemented in production Rust.

A9a is the durable foundation record. Its requirements are derived explicitly
from accepted repository evidence rather than conversational context or agent
memory. It selects no model class and changes no generator behavior.

## Scope

Included:

- bind the accepted A5--A8 decisions, SOTA gap analysis, source assessment,
  quality authority, report standard, and faithful compatibility rules in an
  evidence-to-requirements ledger;
- define one family envelope with explicit seams for seasonal/latent context,
  occurrence/spell state, wet-amount body/tail/memory, storm descriptors, and
  precipitation-conditioned daily context;
- determine which components are mandatory in the first comparison and which
  are conditional extensions, including the rule that a year-level state is
  not introduced until a calibrated daily/event model leaves a measured
  low-frequency residual;
- define independent station-model, generation-profile, fit-artifact,
  optimizer, dataset, and output/provenance identities;
- define an external, optimizer-neutral calibration harness with synthetic
  recovery, deterministic common-random-number evaluation, hard feasibility
  constraints, multi-objective/Pareto diagnostics, resource bounds, and
  complete fit lineage;
- separate coefficient fitting, tunable development, gate calibration, and
  untouched confirmation by station, time, and source-object identity;
- require coverage of hot-arid, arid-boundary, monsoonal transition,
  non-monsoonal semi-arid, humid, and cold regimes without runtime climate
  classification or output-selected fallback;
- define observed-data requirements for daily precipitation and compound
  weather, plus high-resolution storm evidence or an explicit descriptor-data
  hold;
- define model-class independence/equivalence review before A9c comparison;
- specify the climate-only sequence through a possible Rust pilot while
  recording that production promotion still requires separately roadmapped
  downstream evidence under ADR-0004; and
- produce a reviewed successor specification and freeze-ready A9b handoff.

Excluded:

- implementing or running the calibration harness, optimizer, model fitter,
  candidate generator, station model, generation profile, or Rust runtime;
- choosing hyperparameters, weights, thresholds, stations, or candidate
  classes through outcome inspection;
- using A5--A8 exposed outcomes as untouched confirmation evidence;
- reviving an A5b/A5e0/A7b/A8c candidate, repairing A8c, relaxing a prior
  terminal, or treating the A7b O2/SM2 parameterizations as independent;
- complete-year selector/count search, path annealing, rejection to monthly
  targets, monthly-total conditioning, clipping, or post-generation repair;
- automatic runtime aridity/monsoon classification, hidden fallback, station
  substitution, or a separate monsoonal runtime branch;
- openWEPP, WEPPcloud, PyO3, observed-Parquet, multisite/spatial, future-
  scenario, or public-default work; and
- deprecated single-storm generation.

## Authority

- [ADR-0001](../../decisions/0001-source-code-authority-port.md) protects
  faithful behavior and requires explicit versioned divergence.
- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) makes the
  quality vector and observed climate authoritative for extensions.
- [ADR-0004](../../decisions/0004-a5b-interannual-no-promotion.md) requires a
  new prospective study, analytic monthly-budget feasibility, integrated daily
  precipitation behavior, null-calibrated guards, and eventual downstream and
  intervention criteria.
- [A5f0](../20260714-a5f0-annual-state-failure-attribution/package.md),
  [A7a](../20260714-a7a-daily-precipitation-structure-baseline/package.md),
  [A7b](../20260714-a7b-analytic-precipitation-feasibility/package.md),
  [A8a](../20260715-a8a-dry-regime-applicability/package.md),
  [A8b](../20260715-a8b-secondary-year-fallback/package.md), and
  [A8c](../20260715-a8c-routed-daily-pilot/package.md) supply the accepted
  mechanism-specific lessons and exposure boundary.
- The [SOTA gap analysis](../../lit-reviews/sota-climate-generator-gap-analysis.md)
  supplies the ranked model, architecture, data, and validation requirements.
- The [daily-source assessment](../20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md)
  bounds what Daymet, PRISM, gridMET, and GHCN can support and prevents source
  independence claims unsupported by lineage.
- The [scientific report standard](../../standards/scientific-report-standard.md)
  and [authoring protocol](../../standards/scientific-report-authoring-protocol.md)
  govern any later public experiment report.
- The package-local
  [evidence-to-requirements ledger](artifacts/evidence-to-requirements-ledger.md)
  is the traceability authority for A9a. If a foundation claim lacks a ledger
  source, execution must add and review the source before making it normative.

## Foundation requirements

### Model envelope

The family is hierarchical and joint at its declared dependency seams:

```text
seasonal / optional latent climate context
    -> occurrence and spell-duration state
    -> wet-day amount body, tail, and temporal memory
    -> event duration, time-to-peak, and peak-ratio descriptors
    -> explicit wetness/event context for daily meteorological consumers
```

The first A9 comparison must not bolt a new occurrence path onto an unchanged
amount and storm model. Monthly wet fraction, wet amount, total mean/variance,
spell structure, amount dependence/tails, and storm descriptors must be
co-calibrated or analytically reconciled at the model-distribution level. This
does not require the first candidate to replace every temperature, dew-point,
radiation, or wind algorithm; it does require an explicit context interface,
observed conditional metrics, and no exact-identity assumption for variables
whose faithful paths already consume wetness.

### Climate-regime applicability

“One family across regimes” means one semantic model family with explicitly
identified fitted parameter sets, not one global coefficient vector or runtime
classification rule. The fitter may use hierarchical or regional partial
pooling with complete lineage. Every station fit must return either a valid
fit with diagnostics or a declared fit-ineligible result. Any runtime fallback
must be explicit in the fit/station artifact and frozen before generation;
output inspection can never select it.

### Calibration versus adjudication

The harness is allowed to tune on fit/development evidence. It is not allowed
to tune against locked confirmation outcomes. A9a must define:

- data-role partitions that are disjoint by registered station/time/source
  rules and exact hashes;
- optimizer inputs, search bounds, stopping rules, resource budgets, and
  deterministic replay identities;
- separate fit, optimizer, parameter-member, and simulation RNG identities;
- hard analytic/physical feasibility constraints versus scored stochastic
  climate objectives;
- multi-objective and Pareto output before any scalar selection rule;
- a frozen selection rule for A9c and a one-shot confirmation rule for A9d;
- a complete exposure ledger and amendment policy; and
- synthetic-recovery and adverse-fixture tests before observed-data tuning.

### Evidence and promotion boundary

All A5--A8 stations, periods, source objects, metrics, and candidate outcomes
already inspected are development evidence. They may seed requirements,
fixtures, and regression tests but cannot be represented as untouched A9
confirmation. A9a must identify how a confirmation corpus can be selected from
metadata before its target series are accessed.

The A9 sequence is climate-generator research only. A successful climate
confirmation may authorize a Rust pilot, not a production default. ADR-0004's
eventual downstream-response requirement is deferred to a separately
roadmapped package, not waived.

## Plan

1. Hash and classify the exact accepted authority set; complete the
   evidence-to-requirements ledger and exposure inventory without computing a
   new candidate result.
2. Define source-variable coverage, calendar/unit rules, regime strata,
   fit/development/gate-calibration/confirmation partitions, missingness, and
   confirmation selection without target access.
3. Specify the model-family envelope, component interfaces, parameter support,
   partial-pooling/failure semantics, RNG ownership, and at least two genuinely
   distinct candidate-class slots with an equivalence-review gate.
4. Specify the optimizer-neutral harness, fit-artifact schema, synthetic
   recovery suite, objective registry, common-random-number matrix, resource
   budgets, determinism, provenance, and exposure/amendment rules.
5. Define analytic feasibility constraints and the climate evaluation vector
   at 30 and 100 years, including availability, uncertainty, baseline-zero,
   regime-stratified, winter, storm, and conditional-dependence treatment.
6. Author or amend the A9 foundation specification and machine schemas needed
   for A9b research artifacts only; do not add a production profile or station
   model to accepted runtime enums.
7. Conduct accuracy, scientific-validity, non-isomorphism, data-leakage,
   numerical-contract, and consistency reviews; close on a freeze-ready A9b
   handoff or one named hold.

## Execution & dispatch

A9a may execute only after A8c1 returns
`A8C-ROUTED-DAILY-RUNTIME-RETIRED`. Its kickoff must name the then-current
clean `origin/main` commit and target `main`; no side branch or pull request is
authorized by this scaffold.

No candidate coefficient, fit, generated climate, confirmation target, or
optimizer result may be produced during A9a. Metadata-only confirmation-corpus
selection is allowed only under a recorded access barrier. A9b remains
unscaffolded until A9a closes `FOUNDATION-READY-A9B` and receives separate
operator authorization.

## Gates

- every normative requirement maps to an accepted repository source or a
  clearly labeled new operator decision in the evidence ledger;
- exact authority hashes and an exposure ledger distinguish exposed
  development evidence from untouched confirmation candidates;
- model envelope covers occurrence, spells, wet-amount body/tail/memory,
  monthly moments, event descriptors, and daily meteorological context without
  silently requiring every consumer variable to be replaced at once;
- at least two candidate-class slots have distinct probability laws/state
  semantics and a planned equivalence/non-identifiability test before A9c;
- fit, development, gate-calibration, and confirmation roles are executable,
  disjoint, hashable, and protected by a one-shot confirmation rule;
- climate strata include hot-arid, arid-boundary, monsoonal transition,
  non-monsoonal semi-arid, humid, and cold cases, with no runtime classifier;
- Daymet/GHCN dependence, Daymet calendar handling, PRISM rights/period limits,
  gridMET lineage, and variable-specific data gaps are explicit;
- fit-artifact and harness contracts record datasets, periods, units,
  missingness, detrending, estimators, optimizer/version, fit seed, objective
  version, parameter bounds, diagnostics, uncertainty, and exact hashes;
- synthetic recovery, invalid-support, sparse-arid, zero-scale, equivalence,
  nonfinite, calendar, determinism, and resource-bound fixtures are specified;
- objective registry distinguishes hard feasibility from stochastic scores and
  defines availability/baseline-zero rules without outcome-time repair;
- 30-/100-year horizons, multiple burns, common prefixes where claimed, and
  regime-stratified uncertainty are retained;
- no A9 runtime ID, accepted public profile, station model, default, candidate
  coefficient, generated climate, or downstream consumer surface is created;
- review has zero open P1/P2 findings;
- all links and registry entries resolve;
- `git diff --check`;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage/CRAP is not triggered unless A9a execution changes a production
function under `crates/`, which this scaffold does not authorize.

## Exit criteria

`EXECUTED-COMPLETE` with `FOUNDATION-READY-A9B` requires a reviewed and
internally consistent model envelope, source/data plan, tuning-harness
contract, fit/provenance contract, objective registry, prospective evidence
boundary, computational bounds, and freeze-ready A9b implementation handoff.
It does not select a candidate or authorize climate generation.

Legitimate holds are:

- `EXECUTED-HOLD-EVIDENCE-INCOMPLETE` — a normative model or evaluation
  requirement lacks authoritative support;
- `EXECUTED-HOLD-DATA-PARTITION` — required variables/regimes or an untouched
  confirmation design cannot be identified without leakage;
- `EXECUTED-HOLD-MODEL-ENVELOPE` — joint dependencies, fit failure, pooling,
  or candidate-class independence remains underspecified;
- `EXECUTED-HOLD-CALIBRATION-PROTOCOL` — tuning could observe confirmation,
  lacks deterministic provenance/resource bounds, or cannot distinguish hard
  constraints from scores; or
- `EXECUTED-HOLD-EVALUATION-CONTRACT` — metrics, availability, uncertainty,
  or prospective selection/confirmation rules remain non-executable.

Every hold names the first corrective action. No hold permits A9b scaffolding,
candidate substitution, or model implementation.

## Artifacts

- `artifacts/evidence-to-requirements-ledger.md` — accepted findings and their
  exact successor requirements.
- `artifacts/model-family-envelope.md` — component hierarchy, interfaces,
  regime semantics, fit failure, RNG, and candidate-class boundaries.
- `artifacts/tuning-harness-contract.md` — optimizer-neutral development
  platform and development/confirmation firewall.
- `artifacts/data-and-evaluation-plan.md` — observed sources, data roles,
  strata, metrics, horizons, availability, and confirmation design.
- During execution: authority/exposure manifests, foundation specification,
  fit-artifact and objective schemas, fixture plan, A9b handoff, consolidated
  review, and gate results.
