# A11E10 — Centered Thermal Prospective Validation

Status: `EXECUTED-COMPLETE — CENTERED_THERMAL_COMPONENT_REJECTED`

Date: 2026-09-10

Evidence mode: prospective fresh-burn development validation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Test whether the centered, exactly balanced rank-one thermal component retains
A11E9's benefit on fresh stochastic identities and across four cohorts.

## Scope

Included: 20 stations, 32 new burns, new thermal seeds, prospective loading
fits, 640 paired scores, overall and cohort-stability gates, calendar preflight,
cryptographic provenance, replay, review, gates, and reconciliation.

Excluded: old burns, selector behavior, precipitation state, added factors,
confirmation, public integration, production, and defaults.

## Authority

- [SPEC-A11-CENTERED-THERMAL-PROSPECTIVE-VALIDATION](../../specifications/SPEC-A11-CENTERED-THERMAL-PROSPECTIVE-VALIDATION.md)
- A11E9 `CENTERING_REMEDY_SUPPORTED`
- operator authorization to scaffold and execute A11E10

## Plan

1. Freeze specification, identities, executor, and tests.
2. Publish exact source to `origin/main` and execute 640 fresh streams.
3. Replay scientific calculations from the authenticated compact bundle.
4. Review, run gates, and close all records.

## Data calendar and missingness preflight

Repeat the SPEC-A10-CORPUS profile before generation and require the exact
A11E9 counts, masks, roles, and confirmation=false.

## Gates

- new burn and thermal-state identities disjoint from A11E8/A11E9;
- exact zero-sum rendered tenths and complete 20x32 paired grid;
- full component and four-cohort stability decisions;
- byte-identical scientific replay and SHA-256 chain;
- review without unresolved P0/P1;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
- `git diff --check` and changed-document link validation.

Coverage/CRAP applies only if a production function under `crates/` changes.

## Exit criteria

Close retained-for-transfer, rejected, or on an exact integrity HOLD. No
outcome directly authorizes confirmation or production.

## Artifacts

- `artifacts/execution-manifest-v1.json` — frozen identities and gates.
- `artifacts/execute.py`, `test_execute.py` — prospective tools.
- `artifacts/review.md` — pending execution review.

## Outcome

Execution and replay completed from exact published commit
`fa14a5d6b30104c0e9299b34bca02d735ff8b996`. All 640 fresh pairs were complete,
balanced, finite, and confirmation-sealed.

The overall component gate passed: annual-dispersion error was `0.15558` of
faithful, 639/640 pairs improved, monthly mean was exactly preserved, and every
other overall ratio was noninferior. The frozen cohort-stability gate failed.
Cohort 2 had annual lag-one ratio `1.13411`; cohort 3 had annual lag-one
`1.05175` and low-frequency `1.20651`, all above `1.05`. The disposition is
therefore `CENTERED_THERMAL_COMPONENT_REJECTED`.

The result rejects this IID rank-one annual-state formulation despite its
strong dispersion correction. It authorizes no transfer, selector,
hydroclimate expansion, confirmation, production, or default change.
