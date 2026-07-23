# Lemhi GPU capacity policy

Status: `EXECUTED-COMPLETE`
Date: 2026-07-22
Evidence mode: Mixed

## Objective

Make one/two L40s the toolkit's canonical capacities and make three/four-L40
allocation fail closed without a frozen, measured concurrency justification.

## Scope

Amend the authoritative capability specification, the multi-L40 provider, and
the toolkit plan validator. This does not alter a frozen study topology,
reserve capacity, submit a job, or inspect confirmation data.

## Authority

[ADR-0008](../../decisions/0008-lemhi-gpu-capacity-policy.md) and
`SPEC-LEMHI-MULTI-GPU-CAPABILITY` revision 3.

## Plan

1. Declare canonical and exceptional counts in the provider contract.
2. Require every exceptional job to freeze its baseline measurement, projected
   benefit, and a distinct evidence asset; reject exceptional recovery capacity.
3. Exercise two/three/four-L40 validation fixtures and reconcile the
   specification and roadmap.

## Data calendar and missingness preflight

Not applicable: this package consumes no calendarized observations and does
not reserve compute.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `python3 -m unittest research.a10.lemhi_toolkit.tests.test_hardening`

## Exit criteria

One/two L40s plan normally; three/four L40s require a valid frozen
justification; malformed or absent justification fails before remote mutation.

## Artifacts

- `package.md` -- scope, policy authority, and validation record.
