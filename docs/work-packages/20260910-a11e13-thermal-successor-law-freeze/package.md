# A11E13 — Thermal Successor-Law Freeze

Status: `EXECUTED-COMPLETE — AR1_FEASIBLE_TRANSFER_REQUIRED`

Date: 2026-09-10

Evidence mode: retrospective design retirement plus oracle feasibility;
confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Retire the failed IID rank-one thermal law and determine whether one minimal
station-fitted AR(1) successor is feasible enough to justify parameter-transfer
research.

## Scope

Included: explicit IID retirement, conditioned-IID rejection, frozen AR(1)
oracle, 640 paired reconstructions, overall/cohort gates, replay, review, and
records. Excluded: new CLIGEN runs, parameter-transfer implementation,
selectors, hydroclimate coupling, confirmation, and production.

## Authority

- [SPEC-A11-THERMAL-SUCCESSOR-LAW-FREEZE](../../specifications/SPEC-A11-THERMAL-SUCCESSOR-LAW-FREEZE.md)
- A11E10 rejection and A11E12 no-common-loading result
- operator authorization to scaffold and execute A11E13

## Plan

1. Freeze retirement, AR(1) law, and decision gates.
2. Publish exact source, execute and replay the authenticated analysis.
3. Review, run gates, and reconcile the campaign.

## Data calendar and missingness preflight

Reuse and authenticate A11E10's completed Daymet preflight and bundle. Load no
new calendarized data and keep confirmation=false.

## Gates

- exact input identities and retirement record;
- deterministic AR(1), centering, normalization, and balancing tests;
- complete 640-pair overall/four-cohort decision;
- byte-identical replay, repository gates, links, and diff check.

## Exit criteria

Close feasible-transfer-required, retire-thermal-campaign, or exact integrity
HOLD. No result directly authorizes production.

## Artifacts

- `artifacts/execution-manifest-v1.json`, `analyze.py`, `test_analyze.py`.
- `artifacts/review.md` — pending execution review.

## Outcome

Execution and byte-identical replay completed from exact published commit
`7e1d2919483b52d990286653f54dcc80030018a6`. The two IID thermal identifiers
are retired, and horizon-conditioned IID is rejected as selector-like.

The station-fitted AR(1) oracle passed overall and in every cohort. Overall
annual-dispersion error fell to `0.11424` of faithful, lag-one error to
`0.56854`, low-frequency error to `0.71612`, and monthly mean remained exactly
preserved. All four cohorts passed every frozen metric bound; 639/640 pairs
improved annual dispersion. Fitted `phi` ranged from `-0.06658` to `0.64078`.

Disposition: `AR1_FEASIBLE_TRANSFER_REQUIRED`. This authorizes only a package
to find a legitimate non-oracle source for `phi`; it does not authorize public
integration, confirmation, production, or defaults.
