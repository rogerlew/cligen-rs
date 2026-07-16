# A9c3 claim and evidence ledger

Status: frozen after canonical evaluation and independent extraction, before
report drafting

Report ID: `a9c3-two-site-grouped-observed-comparison`

Question: Can either registered successor class produce a selectable research
candidate on the frozen exposed six-regime development surface after replacing
only A9c's hot-arid storm support floors with the equal-weight two-site
estimator?

## Hypothesis/outcome crosswalk

| ID | Provenance | Decision rule | Outcome | Evidence |
|---|---|---|---|---|
| H1 | preregistered | Both actual classes produce at least one valid fresh fit and remain structurally non-isomorphic. | Supported: four alternating-renewal and two latent-regime configurations were fit-valid; the structural audit passed. | E02, E06, E07 |
| H2 | amended | All four equal-weight two-site hot-arid storm estimators are finite; precision and power are reported without a roster floor. | Supported: all estimators were finite from 136 Yuma and 97 Stovepipe Wells development events; 2,000 bootstrap replicates and 14 thresholds were recorded. | E02, E03, E05 |
| H3 | preregistered | The frozen selector identifies at most one class after rejecting hard failures, incomplete mandatory evidence, and material degradation. | Supported as a selector-safety claim: all six short-screen candidates had a hard support failure, so zero advanced and zero were selected. This does not support model adequacy. | E02, E04, E09, E15 |
| H4 | preregistered | Zero locked confirmation station-year target series are accessed. | Supported as recorded; confirmation metadata remained available to enforce the firewall. | E01, E02, E09, E11 |

## Accepted claims

| Claim | Class | Statement | Evidence | Scope guard |
|---|---|---|---|---|
| C01 | Ran | Grouped calibration retained actual development event counts of 136 for Yuma and 97 for Stovepipe Wells, with equal 0.5 station weights. | E03, E05 | The 149/118 fit-period counts have a different role and are not substituted. |
| C02 | Ran | Candidate-blind calibration completed 2,000 grouped bootstrap replicates and 14 family/horizon thresholds with finite estimators. | E05 | Power is diagnostic, not a selection gate or roster floor. |
| C03 | Ran | Eight fresh configurations were fit; four renewal and two three-state latent configurations were eligible, while two four-state latent configurations were ineligible at station `ca042713`. | E06 | Fit ineligibility is not a class-wide failure. |
| C04 | Ran | The two retained classes passed the package structural non-isomorphism and recovery audit, and all eight fit records passed registered monthly reconciliation. | E06, E07 | This is harness evidence, not proof of physical adequacy. |
| C05 | Ran | A fresh Rust `faithful_5_32_3` comparator build produced 160 100-year station/burn runs; every baseline replay, provenance, calendar, and support check passed. | E08 | A9c3 did not execute a new Fortran comparator; faithful semantics remain governed by E14. |
| C06 | Ran | Six fit-valid configurations entered the 30-year short screen over 20 development sites and two burns, producing 240 candidate attempt records and all 31 objective IDs per configuration. | E02, E09, E15 | No candidate reached the 100-year full-development or eight-burn Pareto-replay stage. |
| C07 | Ran | Every candidate prefix failed the registered calendar/support invariant; the parent 100-year validation records sum to 609,654 violations. Retained examples include negative solar radiation, negative wind speed, and humidity outside 0--100 percent. | E09, E12, E15 | Every attempt's first retained failure occurs within 112 days. The total is not a 30-year count, unique-day count, or complete type census. |
| C08 | Ran | The terminal is `HOLD-A9C3-NO-SELECTABLE-CANDIDATE`; full-development count, Pareto-replay count, selected candidate count, and candidate freezes are all zero. | E09 | This is a bounded short-screen result, not a general impossibility claim about either class. |
| C09 | Ran | Locked confirmation target-series access remained zero. | E01, E09, E11 | Confirmation roster metadata were accessed; use the qualified wording. |
| C10 | Interpretation | Before new output, decompose the 19 unavailable mandatory rows by observed, faithful, and candidate cause and establish whether the frozen surface can yield completeness. Then correct context support structurally; holding other mechanisms fixed is diagnostic isolation, not an adequacy judgment. | E09, E12, E15 | The 8--18 degradation rows remain unresolved. No realized-output clipping, runtime fallback, or automatic unchanged-surface rerun is authorized. |

## Evidence identities

E01--E15, their repository paths, roles, and SHA-256 identities are frozen in
`report-evidence-freeze-v1.json`. The same object registers R01--R04 and their
authority scopes. Exact numeric results come from E05--E09; external sources
provide product and network context only.

## Residual uncertainty before drafting

- The two-site storm estimator is spatially limited to Yuma and Stovepipe
  Wells; equal station weight does not make it representative of hot-arid
  climates generally.
- Daymet is a 1-km gridded estimate and USCRN is a point observation. The
  storm comparison is a frozen unpaired group comparison, not a co-located
  daily/event observation.
- A9c3 stopped after the 30-year, two-burn screen. It provides no 100-year
  full-development or eight-burn Pareto evidence for either candidate.
- The short-screen hard failure is sufficient to explain non-promotion.
  Mandatory unavailable cells and degradation counts are incomplete-stage
  diagnostics, not final selector outcomes.
- All eight monthly-reconciliation summaries record `pass`, but their
  per-month-length moments, Monte Carlo standard errors, and applied tolerances
  are hash-bound rather than persisted. Independent audit therefore requires
  deterministic re-execution of that calculation.
- Recorded access boundaries and deterministic program inputs are not an
  operating-system forensic audit.
