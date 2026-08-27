# A11E6 Faithful Baseline Comparison ExecPlan

Status: executing

## Purpose

Coordinate the prospective scaffold, published-source execution, deterministic
replay, and closure of A11E6. The work-package and specification remain the
scientific authority.

## Progress

- [x] Freeze observed-target / faithful-control / circular-treatment framing.
- [ ] Publish source-bound scaffold on `origin/main`.
- [ ] Execute and replay the frozen 20-by-eight grid.
- [ ] Review findings, run gates, and close the package.

## Decisions

- Observations are the target; faithful is the operational control.
- Gaussian is retained only as historical diagnostic context.
- The source `.par` and `cligen` binary are both cryptographically identified.

## Discoveries

- The initial source-bound attempt failed before stream generation because the
  inherited adapter's annual weights are populated by `fit_regions`, not by
  `adapter_parameters`. The executor now materializes and records that frozen
  fit before scoring.
