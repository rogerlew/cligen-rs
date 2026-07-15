# A9a evidence-to-requirements ledger

Status: executed traceability authority
Date: 2026-07-15
Rule: exact repository-source identities are frozen in
[`authority-manifest-v1.json`](authority-manifest-v1.json). Quantitative
statements below come from linked accepted records. A9a design choices are
identified as derived decisions rather than empirical findings.

## Accepted evidence

| ID | Accepted source and finding | Boundary carried forward |
|---|---|---|
| E01 | [ADR-0001](../../../decisions/0001-source-code-authority-port.md): faithful CLIGEN is governed by the vendored Fortran precision map; extensions are explicit, versioned divergences with provenance. | A9 never modifies faithful numerics or consumes faithful RNG streams silently. |
| E02 | [ADR-0002](../../../decisions/0002-quality-metrics-authority.md): observed-climate and station-contract metrics, not similarity to faithful output, govern extensions. | Faithful distance is compatibility information; A9 selection uses a preregistered quality vector. |
| E03 | [ADR-0004](../../../decisions/0004-a5b-interannual-no-promotion.md): all seven A5b candidates failed complete climate gates; renewal requires analytic monthly-budget feasibility, variance reallocation, integrated daily precipitation, null-calibrated guards, intervention criteria, and eventual downstream evidence. | A9 cannot rescue or retune A5b and cannot treat added variance as automatically beneficial. Downstream work is deferred, not waived for promotion. |
| E04 | [A5f0](../../20260714-a5f0-annual-state-failure-attribution/package.md): the exact scalar-IID annual mechanism was retired; cross-month dependence supplied 70.6%/67.9% of positive H1 degradation, one component explained only 11.9–16.5% of fit-period feature variance, all 96 loadings responded with the expected sign, and no single seam met the localization rule. | Do not begin with one global scalar year state or assume runtime signal failure. A low-frequency state is conditional on residual evidence after daily/event calibration and must support richer structure if introduced. |
| E05 | [A5d0](../../20260714-a5d0-successor-feasibility-calibration/package.md): the selector effort held on an incomplete actual-library/reuse/calendar/common-prefix contract; later selector/count packages were cancelled by operator direction. | A9 excludes complete-year selector/count search and avoids making path construction a prerequisite for the model question. Reuse only the evidence-role and prospective-boundary lessons. |
| E06 | [A7a package](../../20260714-a7a-daily-precipitation-structure-baseline/package.md) and [report](../../../reports/a7a-daily-precipitation-structure-report.md): spell structure and higher-order occurrence qualified across required Daymet/faithful/GHCN breadth at both horizons. Wet-amount dependence ranked first by the fixed ordering but did not qualify the GHCN breadth guard; all daily-family/dispersion correlations were positive but noncausal. | A9 must score spells and occurrence, also retain amount dependence/tail/multiday metrics, and must not claim daily structure uniquely causes low-frequency dispersion. |
| E07 | [A7b](../../20260714-a7b-analytic-precipitation-feasibility/package.md): both registered forms were the same four-state process; each passed 192/204 corpus cells but only 31/36 mandatory development cells. Death Valley JJA had 14 adjacent-wet and 14 long-state exposures versus a minimum 25; April/December failed the tail bound. | Candidate classes need non-isomorphism review. Sparse/arid exposure and tail identification are first-class fit diagnostics; aggregate breadth cannot hide mandatory-regime failure. |
| E08 | [A8a](../../20260715-a8a-dry-regime-applicability/package.md): the metadata-first 20-station confirmation classified 15 integrated and five fallback; shortened-window agreement was 0.850; monsoonal and other-dry instability were both 0.1875. | Cover arid, monsoonal, other dry, humid, and cold regimes, but do not create a monsoon-only runtime branch or infer routing from generated output. Prior classifications are exposed development evidence, not A9 truth labels. |
| E09 | [A8b](../../20260715-a8b-secondary-year-fallback/package.md): the pooled EOF2/AR1 candidate failed before coefficients because El Centro had 30 identical zero June totals, making standardization undefined; the certified null retained legacy behavior. | The harness needs zero-scale/sparse-cell fixtures, fit-ineligible semantics, and pooling rules that do not drop, impute, or silently substitute failed cells after outcome access. |
| E10 | [A8c package](../../20260715-a8c-routed-daily-pilot/package.md), [review](../../20260715-a8c-routed-daily-pilot/artifacts/review.md), and [gate record](../../20260715-a8c-routed-daily-pilot/artifacts/gate-results.md): daily spell improvement was 0.251/0.207 and higher-order occurrence improvement 0.476/0.469 at 30/100 years, with 5/6 stations nonworse. Wet-amount means passed only 47/72 and 36/72 cells; every integrated time-to-peak median collapsed to zero; Boise dew point differed on 20,675 pooled rows and Alamosa wind speed on 29,670 because faithful consumers use wetness. | Preserve the demonstrated daily signal, but jointly calibrate monthly amounts and storm descriptors. Expose daily context to other variables and evaluate conditional behavior; do not demand exact downstream identity where wetness is an input. |
| E11 | [SOTA gap analysis](../../../lit-reviews/sota-climate-generator-gap-analysis.md): rank 2 coordinates tails, amount memory, persistence, and multiday extremes; rank 3 requires wet/dry-conditioned or joint multivariate dependence; rank 4 requires descriptor benchmarking before a true subdaily process; the architecture separates station model, profile engine, precipitation state, daily context, and event model. | A9 adopts the joint hierarchy and does not promote independently fitted precipitation components. High-resolution storm data are required for subdaily claims. |
| E12 | [Daily-source assessment](../../20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md): Daymet was selected for the exact A5 fit because it covered 30/30 years and all 17 stations; PRISM daily covered 29 years and 16 CONUS stations and was the preferred method sensitivity; gridMET monthly P/T largely inherit PRISM constraints and are useful chiefly for daily sequencing; Daymet/GHCN are not independent. | A9 uses variable-specific source decisions. Existing Daymet objects are development inputs, PRISM rights/period limits remain explicit, gridMET is not an independent monthly truth surface, and GHCN is a lineage sensitivity rather than independent confirmation. |
| E13 | [Scientific report standard](../../../standards/scientific-report-standard.md): hypothesis provenance, evidence classes, manifest identity, limitations, and review gates are mandatory for public experiment reports. | A9 packages distinguish exploratory tuning from preregistered confirmation and produce a public report only under the standard. |
| E14 | [Rust scientific coding standard](../../../standards/rust-scientific-coding-standard.md): no fast math, explicit extension profiles, fail-closed input, pinned faithful transcendentals, no unsafe code, and CRAP ≤30. | Any later A9 runtime follows these rules; the external harness cannot weaken faithful or production-code gates. |
| E15 | [A8c1](../../20260715-a8c1-routed-daily-retirement/package.md) returned `A8C-ROUTED-DAILY-RUNTIME-RETIRED` and removed the unshipped runtime while preserving the exact evidence. | A9 begins from the pre-A8c shared runtime shape and inherits no A8 runtime identifier, coefficient, route, or fallback. |
| E16 | NOAA's official [USCRN product page](https://www.ncei.noaa.gov/access/crn/qcdatasets.html), [`Subhourly01` documentation](https://www.ncei.noaa.gov/pub/data/uscrn/products/subhourly01/README.txt), and [station listing](https://www.ncei.noaa.gov/access/crn/station-listing) identify five-minute precipitation, temperature, solar radiation, relative humidity, wetness, and 1.5 m wind with explicit timestamps, missing values, and QC semantics. Exact retrieved-document hashes and metadata-only access are in [`confirmation-metadata-selection-v1.json`](confirmation-metadata-selection-v1.json). | A descriptor-level event model is feasible without claiming a native subdaily generator. Wind direction and 10 m wind remain unavailable; target station series remain unaccessed and inaccessible to development before A9d seals them. |

## Derived requirements

### Model requirements

| Requirement | Statement | Evidence |
|---|---|---|
| RQ-MODEL-001 | The family jointly represents occurrence/spell state, wet-amount body/tail/memory, storm descriptors, and an explicit daily context. | E06, E10, E11 |
| RQ-MODEL-002 | Monthly wet fraction, wet-amount moments, and total mean/variance are analytic feasibility targets before stochastic climate scoring; no variance is simply added on top of the legacy budget. | E03, E07, E10 |
| RQ-MODEL-003 | Storm duration, time-to-peak, peak ratio, season, and depth dependence are modeled/evaluated jointly enough to prevent the A8c time-to-peak collapse. | E10, E11 |
| RQ-MODEL-004 | Wetness/event context is an explicit input contract for downstream daily variables; exact faithful identity is not a scientific guard for wetness-conditioned consumers. | E02, E10, E11 |
| RQ-MODEL-005 | A low-frequency/year state is absent from the first mandatory core unless A9 development demonstrates a residual after daily/event calibration; any later state must not be scalar-IID by default. | E04, E06 |
| RQ-MODEL-006 | Candidate classes compared in A9c must have distinct state/probability semantics and pass an equivalence/isomorphism review before outcome ranking. | E07 |
| RQ-MODEL-007 | No complete-year selector, fixed-count search, rejection to targets, clipping, monthly-total conditioning, or post-generation repair is part of the family. | E05, E07, E09 |
| RQ-MODEL-008 | Family semantics are common across regimes, while fitted artifacts may be station-specific, regional, or hierarchically pooled with declared lineage and fit-ineligible outcomes. | E07, E08, E09 |

### Harness requirements

| Requirement | Statement | Evidence |
|---|---|---|
| RQ-HARNESS-001 | Fit/development/gate-calibration/confirmation roles are explicit and confirmation is inaccessible to tuning and model selection. | E03, E05, E13 |
| RQ-HARNESS-002 | Fit RNG, optimizer RNG, parameter/member identity, and simulation RNG are separate, domain-identified, and reproducible. | E01, E11, E14 |
| RQ-HARNESS-003 | Hard support/moment constraints are separated from stochastic objective scores; multi-objective/Pareto evidence precedes any frozen scalar selection. | E03, E07, E10 |
| RQ-HARNESS-004 | Synthetic recovery and adverse fixtures include sparse exposure, zero scale, tail support, candidate equivalence, nonfinite input, calendar, determinism, and resource exhaustion. | E07, E09, E14 |
| RQ-HARNESS-005 | Common random numbers, multiple burns, nested 30/100-year horizons where claimed, and complete configuration hashes make candidate comparisons repeatable. | E02, E10 |
| RQ-HARNESS-006 | The optimizer is replaceable and never defines the station-model or generation-profile schema. | E01, E11 |
| RQ-HARNESS-007 | Search bounds, stopping rules, evaluation budget, wall-time/memory ceilings, failures, and all attempted configurations are retained. | E05, E13 |

### Data and evaluation requirements

| Requirement | Statement | Evidence |
|---|---|---|
| RQ-DATA-001 | Existing A5--A8 stations, periods, products, and outcomes are development-only; A9 confirmation selection precedes target access. | E03, E05, E08, E10 |
| RQ-DATA-002 | The corpus includes hot-arid, arid-boundary, monsoonal transition, non-monsoonal semi-arid, humid, and cold strata without a runtime classifier. | E07, E08 |
| RQ-DATA-003 | Product lineage is variable-specific: Daymet may be a development source, PRISM a licensed/method sensitivity, gridMET a daily-sequencing source, and GHCN a non-independent point sensitivity. | E12 |
| RQ-DATA-004 | Daily precipitation alone cannot support true subdaily claims; duration/time-to-peak/intensity fitting requires named high-resolution observations or an explicit hold. | E10, E11 |
| RQ-EVAL-001 | The objective vector includes spells, higher-order occurrence, wet-amount mean/variance/dependence/tails, zero-month frequency, monthly/annual dispersion, 1/3/5-day extremes, storm descriptors, conditional weather dependence, and winter proxies. | E06, E10, E11 |
| RQ-EVAL-002 | Metrics define units, aggregation, completeness, unavailable values, baseline-zero behavior, uncertainty, and regime aggregation before candidate outcome access. | E02, E09, E13 |
| RQ-EVAL-003 | A climate-confirmed candidate may proceed to an internal Rust pilot, but production promotion still requires separately roadmapped downstream/intervention evidence. | E03 |

### Foundation design decisions

These decisions resolve the scaffold's open choices. They are prospective
research-contract choices derived from accepted evidence; they are not claims
that a model or threshold has performed well.

| Decision | Frozen choice | Derivation |
|---|---|---|
| D01 | The first comparison has two research class slots: `alternating_renewal_marked_v1`, whose observed wet/dry spells are explicit alternating semi-Markov durations, and `latent_regime_marked_v1`, whose hidden semi-Markov states emit joint zero-inflated daily marks and do not equal observed spell state. Degenerate parameter regions that collapse one into the other are excluded. | E06, E07, E11; RQ-MODEL-001/006 |
| D02 | The first family has no runtime fallback. A failed or ineligible fit stops generation for that artifact. Any later fallback requires a separate profile/version and prospective evidence. | E08, E09, E10, E15; RQ-MODEL-007/008 |
| D03 | USCRN `Subhourly01` is the first descriptor/compound source. Events use the frozen six-hour dry-separation rule; the result remains descriptor-only. | E10, E11, E16; RQ-MODEL-003 and RQ-DATA-004 |
| D04 | Daymet fitting uses `daymet_official_365_v1`: leap years retain 29 February and lack 31 December. No imputation occurs; incomplete observed months/years follow the objective registry. PRISM is licensed method sensitivity only after rights clarification, gridMET is a sequencing sensitivity, and GHCN is shared-lineage sensitivity. | E12; RQ-DATA-003 |
| D05 | All 37 station IDs and 10 source records in the exposure manifest are development-only. The exact 18-site USCRN metadata roster has three sites in each of six mandatory strata, a 75 km exposed-site exclusion, a 150 km within-stratum separation, and no substitution. Target bytes remain unaccessed. | E03, E08, E10, E13, E16; RQ-HARNESS-001 and RQ-DATA-001/002 |
| D06 | Objectives remain multi-objective. A paired 500-replicate, maximum-statistic null at familywise alpha 0.05 calibrates thresholds before candidate access; the full Pareto set precedes the frozen lexicographic rule in SPEC-A9. Baseline-zero cells use absolute or two-part rules. | E02, E03, E09, E13; RQ-HARNESS-003/005 and RQ-EVAL-002 |
| D07 | Development uses staged resource ceilings: at most 4,096 analytic proposals, 256 short-screen configurations, 64 full-development configurations, and eight final Pareto replays per class. Final development uses eight burns; one-shot confirmation uses twelve. Each burn is one 100-year run whose first 30 years are the paired prefix. | E05, E10, E13; RQ-HARNESS-005/007 |
| D08 | No year-level latent state is in either first-core slot. A later low-frequency extension requires a measured residual after the selected daily/event model and a separate prospective class/version. | E04, E06; RQ-MODEL-005 |
| D09 | The research common-random-number field is counter-based Philox4x32-10 with component/date/slot indexing and independent fit, optimizer, parameter-member, and simulation domains. It does not touch faithful streams or prejudge a production RNG. | E01, E11, E14; RQ-HARNESS-002/005 |

## Exposure consequences

- The 17-station A5/A7 corpus, eight GHCN sensitivities, A8a 20-station panel,
  A8c six-station pilot, 1980--2009 fit period, 2010--2025 evaluation period,
  and all published metrics are exposed.
- These records are valuable for requirements, regression tests, objective
  debugging, and tunable development. They are not untouched confirmation.
- A9a execution must inventory exact overlaps rather than assuming that a new
  source download makes an exposed station/time target independent.

## Resolution of scaffold-time open decisions

All six scaffold-time questions are resolved prospectively by D01--D09 and
the linked contracts:

1. two non-isomorphic class slots are frozen, without coefficients or fits;
2. USCRN supports the descriptor-level source boundary;
3. pooling and minimum exposures are fixed in the model/data plans and remain
   fail-closed;
4. normalization, null calibration, Pareto reporting, and the selection rule
   are fixed in the objective registry and SPEC-A9;
5. the metadata-only confirmation roster, products, periods, burn derivation,
   and threshold-calibration algorithm are fixed without target access; and
6. no fallback is part of the first family.

The only values intentionally deferred are hashes that cannot exist before a
future artifact is acquired or implemented: normalized confirmation target
hashes, candidate source/schema hashes, fit parameters, calibrated numeric
threshold values, and simulation seeds derived from a future campaign hash.
Their derivations and pre-access freeze points are fully specified; absence of
one at the required future gate is a hold, not discretion.
