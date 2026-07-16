# A9c post-acceptance operator disposition

Date: 2026-07-15
Affected report: `a9c-observed-development-availability`, revision 1
Prior accepted report SHA-256:
`6a4d500225f34e83c63259d566725ef79d054549a0c9b5b83e44ec8c2483032b`

## Finding

The registered 150- and 200-event station minima correctly produced A9c's
`HOLD-A9C-GATE-CALIBRATION` terminal, but the closeout overinterpreted those
prospective rules as support targets that a successor roster should be made to
meet station by station. The observed counts of 136 and 97 are the realized
rates at these two sites over the seven-year development window under A9c's
frozen six-hour event and QC definition. The count floors were design choices;
A9c did not empirically calibrate them as minimum sample sizes for those
stations.

## Operator decision

The operator directs the successor campaign to increase the number of frozen
hot-arid development locations and evaluate event descriptors through a
prospectively frozen, station-balanced group design. The successor will derive
availability from candidate-blind precision and power behavior at the actual
site/event design instead of requiring every hot-arid station to clear the
former 150/200 counts.

## Immutable A9c boundary

- A9c's frozen rules, event counts, failed-cell arithmetic, access history,
  and `HOLD-A9C-GATE-CALIBRATION` terminal do not change.
- The five completed fits, null thresholds, and all A9c objects remain exposed
  development evidence; they are not relabeled as successor results.
- A9c still makes no candidate-quality claim.
- The locked 18-site A9 confirmation roster remains metadata-only and its
  station-year series remain prohibited.
- A9b and its handoff remain immutable historical authorities.

## Disposition

Revise the accepted A9c report to revision 2, describing the hold as a
registered design-rule mismatch rather than an intrinsic lack of hot-arid
observations. Scaffold A9c2 as a fresh campaign with a new identity, expanded
metadata-selected hot-arid roster, grouped storm evaluation, candidate-blind
support calibration, complete refitting, and complete comparison. A9c2 is
scaffolded only; its observed-series execution requires separate dispatch.
