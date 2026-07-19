# A10M5R4R2 — Realized Temporal-Dispersion Adjudication

Status: `FROZEN-ALLOCATABLE`
Date: 2026-07-18
Evidence mode: Prospective temporal/resource freeze; no generated-output access
Starting branch and push target: `main` after A10M5R4R1, push `main`

## Objective

Adjudicate realized generated calendar-month and interannual behavior for the
A10M5R3R1 P1/P2 capacity pair against observations, unmodified faithful
CLIGEN, and accepted `stochastic_prism_localized_par_v1`.

## Entry authority and boundaries

A10M5R4R1 issued `A10M5R4R1-STOCHASTIC-PRISM-READY`; its immutable release,
embedded distribution identity, preprocessing contract, and generic
acceptance evidence are inputs. The original A10M5R4 hold remains immutable.

The exact observation sites, P1/P2 output identities, PRISM requests,
estimands, tolerances, uncertainty procedure, role access, resource ceiling,
and cleanup plan are now frozen in `artifacts/temporal-contract.json` and
`artifacts/sites.json`. This authorizes only the six registered
single-attempt reconstruction/generation jobs and the local faithful/PRISM
arms. Development-selection and confirmation remain sealed.

## Plan

1. Reauthenticate A10M5R3R1's accepted P1/P2 pair and the A10M1 observational
   transfer without opening generated outputs.
2. Freeze calendar-month and interannual estimands and bind three comparator
   arms: observations, faithful CLIGEN, and stochastic PRISM revision 1.
3. Freeze protected-role access and confirmation rules before allocation.
4. Generate or access only the declared P1/P2 streams, compute the frozen
   matrix, and retain exact artifact/provenance identities.
5. Decide the retained capacity set or issue an evidence-specific hold, perform
   exact cleanup, reconcile the roadmap/catalog, and authorize A10M5R5 only
   if the temporal gate passes.

## Gates

- every stochastic-PRISM artifact verifies against the A10M5R4R1 bundle and
  preprocessing identities;
- observations, faithful CLIGEN, and stochastic PRISM remain distinct arms;
- no PRISM monthly input is represented as daily observational truth;
- P1/P2 identities and all roles are frozen before generated-output access;
- all calendar-month/interannual metrics and decision thresholds are
  prospective; and
- repository, toolkit, allocation, cleanup, and package-verifier gates pass.

## Exit criteria

Execution must end in a typed temporal decision naming the retained capacity
set and A10M5R5 authority, or an honest hold with the exact failed gate and
smallest corrective successor. Every temporally eligible capacity continues
to A10M5R6; final architecture selection remains downstream of spatial
evidence.

## Frozen execution record

- `artifacts/design-freeze.md` — human-readable prospective boundary;
- `artifacts/temporal-contract.json` — models, streams, metrics, thresholds,
  uncertainty, decision, and resource contract;
- `artifacts/sites.json` — value-blind six-regime observation roster and exact
  A10M1 identities;
- `artifacts/jobs/` — deterministic model reconstruction, generated-stream
  summarization, and shared temporal-metric implementation; and
- `artifacts/verify_freeze.py` — fail-closed pre-output verifier.
