# A10 Climate-Normal Residual Architecture

This living ExecPlan follows `.agent/PLANS.md`. It coordinates A10M5R9 without
replacing the package, specification, machine contract, or toolkit evidence.

## Purpose

A10M5R8 showed that aggregate stochastic training pressure is informative but
that P1 entangles climate location with variability. A10M5R9 asks the smallest
new architecture question: does a candidate-fit-only monthly baseline plus a
small persistent stochastic residual outperform the identical baseline without
that residual while preserving P1-level location/proper fit?

## Progress

- [x] (2026-07-19) Operator authorized the next science architecture package.
- [x] (2026-07-19) Froze baseline-only, baseline-plus-residual, exact P1
  context, calendar, roles, objective, and decision surface.
- [ ] Implement and pass local architecture/calendar/decision fixtures.
- [ ] Publish source, initialize authority, and execute one bounded L40 run.
- [ ] Authenticate all-240 comparison, close resources and cleanup, and record
  the scientific disposition.

## Decisions

- The baseline is a six-regime by twelve-month distribution-head table plus a
  shared latitude/longitude/elevation correction. This is transferable to
  fit-validation without target lookup.
- The residual state updates monthly, not daily. The frozen hypothesis concerns
  monthly and annual stochastic dispersion; monthly state is the least complex
  timescale that can test it.
- Residuals perturb only occurrence and core location heads. Scale parameters
  and baseline weights remain owned by the baseline.
- Member innovations are centered and arm-paired so the residual represents
  variability rather than an unconstrained second location surface.
- Solar remains downstream of a passing core architecture.

## Surprises & Discoveries

Pending execution.

## Outcomes & Retrospective

Pending execution.

## Execution boundary

One fresh revision-2 toolkit authority permits a single 60-minute, one-L40
primary and one five-minute exact-node cleanup contingency. Candidate-fit is
the only gradient/normal source. Fit-validation is checkpoint/final scoring
only. Development-selection and confirmation remain sealed. No retry, extra
seed, member increase, weight edit, or alternate latent dimension is permitted.
