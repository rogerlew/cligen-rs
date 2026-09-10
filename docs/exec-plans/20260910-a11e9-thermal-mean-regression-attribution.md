# A11E9 Thermal Mean-Regression Attribution ExecPlan

Status: scaffolded

## Purpose / Big Picture

A11E9 determines whether enforcing a zero-mean annual thermal state repairs
A11E8's sole component-gate failure without sacrificing its annual benefit.

## Progress

- [x] 2026-09-10: freeze the four-arm attribution and decision rules.
- [ ] Publish exact prospective source and execute the bounded grid.
- [ ] Replay, review, run gates, and close records.

## Surprises & Discoveries

- A11E8 improved annual dispersion in 639/640 pairs but failed only the monthly
  mean gate among component metrics.

## Decision Log

- Centering is tested before any richer model.
- Exact zero-sum tenths separates latent drift from rendered quantization.
- Selector and precipitation behavior are out of scope.

## Outcomes & Retrospective

Pending execution.

## Context and Orientation

The package is
`docs/work-packages/20260910-a11e9-thermal-mean-regression-attribution/` and the
specification is
`docs/specifications/SPEC-A11-THERMAL-MEAN-REGRESSION-ATTRIBUTION.md`.

## Plan of Work

Generate the exact A11E8 faithful grid, authenticate inherited observations and
loadings, construct all arms, score, decide, publish a compact replay bundle,
then replay calculations independently from that bundle.

## Concrete Steps

Work on `main`, publish the scaffold, and invoke `execute.py --execute` with the
exact 40-character source commit. Preserve first scientific outputs, invoke
`--replay`, compare bytes, and close the package.

## Validation and Acceptance

Acceptance requires exact runtime/source identity, complete counts, valid
calendar preflight, byte-identical replay, confirmation=false, review GO, and
all repository gates.

## Idempotence and Recovery

Runtime directories must not pre-exist and are removed in `finally`. Execution
publishes atomically only after complete validation. Replay never regenerates
CLIGEN streams.

## Artifacts and Notes

Raw climates remain temporary. The compact bundle retains only the monthly
matrices, loadings, states, and their provenance required for replay.

## Interfaces and Dependencies

No public interface or production function changes.

## Revision Note

2026-09-10: initial prospective scaffold.
