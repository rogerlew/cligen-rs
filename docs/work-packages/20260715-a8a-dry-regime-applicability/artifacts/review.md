# A8a consolidated review

Verdict: **ACCEPT**

Review date: 2026-07-15

## Scope and evidence boundary

A8a answers a bounded applicability question for the one unique A7b
four-state precipitation construction. It does not reverse A7b's whole-domain
stop, generate candidate climate, add runtime routing, change a station schema
or generation profile, or modify faithful or extension production code.

The 20-station confirmation panel was selected from 2,765 public `us-2015`
records using only the hash-pinned SQLite catalog and legacy parameter bytes.
The five strata contain four stations each, no A5a development station was
reused, and every within-stratum pair exceeds the frozen 150 km separation.
Inventory, panel, and selected-parameter artifacts reproduce byte for byte.

The first acquisition attempt read only the official GHCN station-list
metadata and stopped because its station-name field contains UTF-8 characters
while the parser required ASCII. Amendment 001 records the source identities,
zero Daymet and zero GHCN station archives, absence of a source manifest and
outcomes, and the exact before/after script hashes. Successor freeze v2 binds
strict UTF-8 decoding and output-freeze provenance. It does not change a
station, period, source, classifier, bootstrap, analytic equation, threshold,
guard, or terminal rule. The amendment is therefore bounded and prospective
with respect to all daily station data and outcomes.

## Coverage

- 20/20 primary Daymet V4 R1 series are available for the fixed 1980--2025
  no-leap period, each with exactly 16,790 records.
- Three deterministic U.S. Cooperative identifiers mapped to official GHCN
  stations within 25 km; two met the frozen 90% precipitation-coverage rule.
  GHCN was prospectively descriptive and non-terminal.
- The analysis evaluated 20 confirmation and eight previously exposed
  development stations: 28 full records, 336 monthly analytic cells, 80
  shortened station windows, and 1,000 year-block support replicates per full
  station.
- The independent verifier checked both freeze records and the amendment,
  all archived source identities, input identities, classification logic,
  development reproduction, every terminal guard, transition row sums,
  stationary distributions, wet-fraction preservation, and amount/moment
  budgets. A second run reproduced the analysis, decision, and findings bytes
  exactly.

## Accuracy and numerical review

All eight exposed development classifications reproduce the frozen A7b
dispositions: five fallback and three integrated. All four humid/cold negative
controls classify integrated. Across the 16 dry/transition confirmation
stations, 11 classify integrated and five fallback, satisfying both frozen
breadth guards.

For the 180 feasible monthly cells belonging to the 15 integrated confirmation
stations, the worst wet-amount variance retention is 0.2761 against a 0.25
floor, the largest tail log error is 0.6078 against a 0.7 ceiling, the largest
relative monthly-variance reconstruction error is `3.43e-13`, and the largest
stationary wet-fraction error is `6.95e-14`. The five fallback stations fail
closed for registered reasons: sparse seasonal wet/transition support, a
degenerate legacy wet month, required wet-amount variance increase, or tail
error. No failed cell is repaired or reclassified from generated output.

Full-record versus shortened-window classification agrees in 68/80 cases
(0.850). Monsoonal-transition and other-dry instability are both 0.1875, so
their difference is zero against the frozen 0.25 maximum. The two eligible
GHCN sensitivity stations agree with Daymet on point-support disposition.

## Consistency and public-safety review

The result is internally consistent with the roadmap and A7b. It confirms an
explicit evidence-time applicability partition; it does not certify a single
whole-domain mechanism. The class is station metadata to be published before
generation, not a runtime aridity estimate or output-dependent switch. A8b may
therefore study only the secondary year-to-year fallback while accepting the
eligible-domain daily construction and this partition without reopening
either.

The equal monsoonal and other-dry instability rates do not trigger a separate
monsoonal sequence. Monsoonal stations remain a mandatory stratum in the
shared A8 sequence.

Archived observations are isolated under `references/observed/a8a-v1/`, carry
a third-party data notice and primary citations, and are covered by Git LFS
attributes. The notice does not relicense Daymet or GHCN data under the
repository's Apache-2.0 license and confines GHCN redistribution claims to the
archived U.S. Cooperative records.

## Findings and dispositions

No P1 or P2 finding remains open.

| ID | Priority | Observation | Disposition |
|---|---|---|---|
| A8A-REV-001 | P3 | Only two exact Cooperative matches support the Daymet/GHCN sensitivity result. | Keep the 2/2 agreement descriptive and non-terminal; make no grid-versus-point generalization. |
| A8A-REV-002 | P3 | The registered strata use legacy precipitation/temperature climatology screens, not a PET-based physical aridity index. | Limit the result to the explicit descriptor strata and station declarations; do not infer a national runtime classifier. |
| A8A-REV-003 | P3 | Six stations account for 12 shortened-window disagreements, including five full-record integrated stations. | Bind any future station class to its registered evidence period and retain the fail-closed lower-support rule; do not infer from an arbitrary short record. |
| A8A-REV-004 | P3 | There is no external ground-truth label for `integrated_daily`; "accuracy" is operationalized by development reproduction, controls, analytic feasibility, and stability. | Describe the result as applicability confirmation, not predictive classification accuracy. |

## Decision

The frozen decision returns `CONTINUE-A8B-DRY-PARTITION`: 15 confirmation
stations are `integrated_daily`, five are `legacy_daily_fallback`, every
integrated station passes all 12 analytic cells, and all eight terminal guards
are true. The evidence is accepted for dispatching A8b within its roadmapped
scope.
