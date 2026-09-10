# A11E10 Centered Thermal Prospective Validation ExecPlan

Status: scaffolded

## Purpose / Big Picture

Validate the A11E9 correction on fresh stochastic identities before any
parameter-transfer or model-expansion work.

## Progress

- [x] 2026-09-10: freeze fresh identities, component, and stability gates.
- [ ] Publish and execute exact source.
- [ ] Replay, review, run gates, and close records.

## Surprises & Discoveries

- A11E9 isolated finite-sample state-mean drift and showed quantization was not
  a material blocker.

## Decision Log

- Use 32 burns disjoint from A11E8/A11E9 and a new seed domain.
- Require all four cohorts to pass; do not introduce a selector.

## Outcomes & Retrospective

Pending execution.

## Context and Orientation

The package lives at
`docs/work-packages/20260910-a11e10-centered-thermal-prospective-validation/`.

## Plan of Work

Generate fresh faithful controls, fit station loadings before candidate
construction, generate centered balanced candidates, score, decide, replay,
and reconcile records.

## Concrete Steps

Publish the scaffold on `main`; execute with its exact 40-character commit;
preserve scientific outputs; replay from the authenticated bundle; compare and
close.

## Validation and Acceptance

Require exact source/runtime/data identity, complete counts, overall and cohort
gates, byte-identical replay, confirmation=false, review GO, and repository
gates.

## Idempotence and Recovery

The runtime refuses pre-existence and is removed in `finally`. Outputs publish
only after the complete grid validates. Replay performs no CLIGEN generation.

## Artifacts and Notes

Raw climates are temporary; the compact bundle retains the replay-sufficient
monthly evidence and complete hashes.

## Interfaces and Dependencies

No public interface or production function changes.

## Revision Note

2026-09-10: initial prospective scaffold.
