# A5d Validation Corpus and Power Record

Status: `EXECUTED-HOLD-CONFIRMATION-CORPUS`
Evidence mode: Static inventory and derived power calculations

## Inventory result

The repository's A5 observed corpus contains 17 Daymet station extracts and
eight matched GHCN station extracts. Every station, period, target, and result
was exposed during A5a/A5b and is therefore development or calibration
evidence. The input lock records the corpus config and complete derived target
hash. No untouched A5d confirmation station, raw target object, qualification
manifest, or sealed metric artifact exists.

The inventory is recorded in
[`data-role-inventory-v1.json`](data-role-inventory-v1.json). File names were
listed and existing corpus metadata/results inspected; raw Daymet and GHCN
value rows were not opened during A5d0.

## Frozen role policy for a follow-on

| Role | Permitted use | Current evidence |
|---|---|---|
| Coefficient fit | Estimate Fourier/EOF representation, constrained selection weights, transition parameters, and pooling hyperparameters | Existing Daymet fit data; exposed |
| Development | Architecture choice, solver debugging, feasibility, numerical bounds, and effect-size planning | All A5a/A5b stations and results |
| Null calibration | Faithful-clone false-failure, bootstrap availability, and gate thresholds without A5d candidate output | Not generated |
| Confirmation | One frozen candidate and registered baselines under fixed gates | None |
| Independent sensitivity | Long-record point observations under frozen rules | Existing eight are exposed; new set required |

No target may move from development to confirmation by relabeling it.

## Provisional sign-test planning floor

The exact sign calculation shows that 23 stations with 16 improvements is the
smallest design meeting one-sided null probability at most 0.05 and at least
80% power when the true station improvement probability is 0.75. Because the
study requires four primary climate regimes, a useful provisional planning
floor is:

- 28 primary confirmation stations;
- seven each in arid, monsoonal, humid, and `cold` climate regimes;
- at least 19/28 station composites improved;
- one-sided null sign probability 0.04358;
- planning power 0.86155 at true improvement probability 0.75.

This only powers an independent Bernoulli sign component. It is not a powered
confirmation minimum. A calibration-only spatial/composite simulation must
determine the actual acquisition and confirmation count after accounting for
spatial dependence, metric effect dispersion, regime medians, GHCN
availability, and the winter subset. A5b's fixture site does not count toward a
new confirmation minimum. The `cold` climate-regime token remains distinct
from the downstream WEPP cold/snow-domain site family.

## Qualification rules to freeze before acquisition

The follow-on corpus package must select stations using metadata and
predeclared rules without inspecting confirmation target metrics:

- station/source identity, coordinates, elevation, and regime assignment;
- spatial separation and exclusion of every A5a/A5b station or duplicate
  record;
- exact Daymet product/release, fit/evaluation periods, grid extraction, and
  calendar transform;
- minimum complete-year and aligned-variable requirements;
- GHCN flags, missingness, relocation/homogeneity policy, and mapping distance;
- primary raw/detrended status and all sensitivity roles;
- licenses, retrieval commands, raw response hashes, normalized object hashes,
  and third-party notices;
- sealed target construction performed by a script that reports identities and
  qualification counts without printing metric values.

Daymet may remain the coefficient source, but station-level coefficients should
use hierarchical/regional pooling rather than estimating a 36-dimensional
annual structure independently from 30 years. The exact pooling unit is a
development choice and must be frozen before confirmation scoring.

## Replicate and null power requirements

- Candidate climate replicates cannot inherit A5b's count of eight without a
  paired-effect power analysis.
- A familywise null-failure claim below 5% needs at least 59 independent audit
  null trials after zero failures; burn offsets alone do not justify the
  independence model.
- WEPP replicate count follows the still-unregistered downstream response
  criterion and cannot be selected here.
- Both 30- and 100-year horizons and complete downstream evidence remain
  mandatory for eligibility.

## Disposition and first follow-on action

Disposition: `HOLD-CONFIRMATION-CORPUS`.

The first action is a dedicated, pre-value-access corpus package that uses 28
only as the initial independent-sign planning floor, runs the spatial/composite
power analysis to determine the actual minimum, then freezes metadata-only
selection and qualification rules, official source retrievals, immutable
hashes, sealed target-builder behavior, and an independent long-record
sensitivity set. Until that package closes, A5d confirmation fitting or
scoring is prohibited.
