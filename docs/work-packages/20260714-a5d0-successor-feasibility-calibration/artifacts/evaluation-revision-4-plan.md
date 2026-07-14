# A5 Evaluation Revision 4 Calibration Record

Status: `EXECUTED-HOLD-EVALUATION-UNCALIBRATED`
Evidence mode: Derived and static
Current authority: SPEC-A5-EVALUATION revision 3

## Versioning decision

Revision 3 is an accepted A5b/A5c input whose exact bytes are locked by A5c.
It must not be edited in place. A successor contract must receive a new
versioned file and executable artifact set, provisionally
`SPEC-A5D-EVALUATION` with new metric, schema, bootstrap, and verifier
identities. No revision-4 normative file is created by this held package.

## Calibration boundary

Permitted evidence comprised accepted A5a/A5b development results, faithful
and QC-off baseline evidence, the accepted advisory, and deterministic
synthetic fixtures. No A5d candidate confirmation metric or WEPP response was
generated or read.

## Gate-by-gate disposition

| Gate | Retain | Required prospective change | Freeze status |
|---|---|---|---|
| G1 observed improvement | Joint composite and low-frequency improvement at both horizons; regime and station coverage | Replace the exposed 17-station sign component with a powered confirmation design; repair undefined bootstrap aggregates and set an empirically demonstrated minimum availability | HOLD |
| G2 independent source | Point-record sensitivity cannot replace primary gridded evaluation | Freeze a new long-record station set, record-quality rules, and noninferiority margin before candidate access | HOLD |
| G3 monthly contract | Hard preservation of fitted monthly surface | Use absolute deviations normalized by parameter/observation uncertainty, plus physical hard bounds; do not divide by a near-zero faithful residual | HOLD |
| G4 daily precipitation | Spell, persistence, and multiday-extreme preservation | Use observation-scaled absolute distances and a complete bootstrap surface; positive-trace remains distinct | HOLD |
| G5 descriptors | Time-to-peak and peak-ratio coverage | Calibrate a paired maximum-statistic or excursion allowance from faithful-clone null matrices rather than an unmeasured zero-excursion rule | HOLD |
| G6 winter | Explicit air-temperature proxy plus downstream physical snow/freeze responses | Apply the same null and missingness calibration; do not relabel proxies as physical partition or state | HOLD |
| G7 evidence/response | Complete hash-bound climate and WEPP evidence | Register an executable WEPP reference and numeric response rule; add intervention-rate criteria | HOLD |

## Faithful-clone calibration requirement

The fixture calculates the one-sided 95% Clopper–Pearson upper bound on a null
failure probability after zero observed failures:

```text
upper(n) = 1 - 0.05^(1/n).
```

With eight null trials, the upper bound is 0.3123. At least 59 independent null
trials with zero failures are required to put the upper bound below 0.05; 59
gives 0.04951. A5b's eight generated replicates and min–max descriptor envelope
therefore cannot calibrate a familywise five-percent false-failure claim.

The successor calibration should separate:

1. a calibration set large enough to select maximum-statistic or paired-cell
   thresholds; and
2. at least 59 independent audit null matrices not used to choose those
   thresholds if the acceptance claim is “familywise false failure below 5%.”

Burn offsets are empirical faithful trajectory spread, not independent seeds.
The null contract must state exactly what independence claim is available and
must not use binomial confidence language for overlapping burn streams.

## Gate 1 station component

The current rule “at least 11 of 17 stations improve” has one-sided null sign
probability 0.16615 and is not independently decisive. The smallest exact sign
design with null probability at most 0.05 and at least 80% power when the true
station improvement probability is 0.75 is 23 stations with 16 improvements.
A balanced four-regime design of 28 stations with 19 improvements has null
probability 0.04358 and power 0.86155 under that planning alternative.

These computations justify a minimum planning floor, not the final station
count: the composite effect-size distribution, spatial clustering, multiple
gates, winter subset, and regime medians still require a frozen simulation or
bootstrap power analysis on calibration-only evidence.

## Bootstrap availability

Revision 3 produced usable corpus aggregates for only 221/2,000 Gate 1
resamples (11.05%) and 8/2,000 Gate 4 resamples (0.4%). A successor cannot
declare an uncertainty interval decision-supporting unless its definition is
available on a predeclared large majority of null-calibration resamples.

A provisional design target of at least 90% usable aggregates is reasonable
for engineering, but it is not frozen here: the revised cell membership,
fallback/missingness rules, and observed uncertainty scale have not been
implemented, so the target has not been demonstrated without candidate data.
Failure to meet the eventual minimum must invalidate the evaluation surface;
it must not count as a candidate pass or failure.

## Gates 3 and 4 scaling

The proposed form is an absolute noninferiority statistic:

```text
Z_cell = abs(generated - target) / U_cell,
```

where `U_cell` is a prospectively pinned, strictly positive uncertainty scale
derived from observed/parameter estimation—not the faithful residual. A
separate hard physical bound prevents a large observational uncertainty from
making preservation vacuous. The definition of `U_cell`, its floor, cell
aggregation, hard bounds, and null distribution remain uncalibrated.

## WEPP response and intervention rule

Revision 3 registered no numeric downstream bound. A closeness rule to
faithful output would conflict with ADR-0002 because faithful is not observed
truth. A scientifically stronger option is a pinned `hybrid_observed_pt` WEPP
reference with explicit limits, but the current evidence does not establish a
valid storm/intensity reference or numeric noninferiority margin. Consequently,
WEPP cannot yet adjudicate a candidate.

For the preferred block-preserving class, new physical-value intervention has
a proposed hard limit of zero: no precipitation clips, temperature-order
repairs, or dewpoint caps attributable to selection. Date/index bookkeeping is
reported separately. This invariant can be frozen only after the selector
contract exists.

## Disposition and first follow-on action

Disposition: `HOLD-EVALUATION-UNCALIBRATED`.

The first calibration action is to author a separate versioned A5d evaluation
contract and executable null-calibration package that, before any A5d
candidate output:

- implements observation-scaled G3/G4 statistics and demonstrates the chosen
  bootstrap-availability floor;
- calibrates G5 and the full gate vector on faithful-clone matrices with a
  defensible independence model;
- pins an observed/hybrid WEPP reference or explicitly blocks promotion; and
- emits new metric manifests, schemas, verifier, golden fixtures, and immutable
  identities without changing revision 3.
