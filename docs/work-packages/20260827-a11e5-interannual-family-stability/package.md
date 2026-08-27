# A11E5 — Full Interannual Family Stability

Status: `SCAFFOLDED`

Date: 2026-08-27

Evidence mode: observed development; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Compare circular-block and Gaussian annual/monthly laws across eight members
and the full registered interannual diagnostic family while holding nearest
forcing and the daily core fixed.

## Authority

- [SPEC-A11-INTERANNUAL-FAMILY-STABILITY](../../specifications/SPEC-A11-INTERANNUAL-FAMILY-STABILITY.md)
- closed A11E1 strategy and fit evidence
- closed A11E2 nearest-candidate selector and location evidence
- operator criterion: useful at about one-third benefit if non-beneficiaries
  are not made materially worse

## Scope

Included: prospective source publication, dependency and calendar preflight,
20 development stations, members 0--7, two frozen stochastic laws, nearest
forcing, ten interannual errors, universal-versus-routed disposition, replay,
review, gates, and reconciliation.

Excluded: tuning, learned routing, confirmation, new data, selector changes,
production Rust or CLI changes, public profiles, and WEPP claims.

## Plan and gates

1. Freeze specification, manifest, executor, schema, and synthetic tests.
2. Publish the exact source on `origin/main` before observed execution.
3. Revalidate the A10 calendar and A11E inputs and execute 320 streams.
4. Replay scientific outputs byte-identically and independently audit the
   frozen arithmetic.
5. Run repository gates and reconcile the package, catalog, and roadmap.

Required gates are strict manifest/schema tests, exact published source and
dependency identities, complete calendar/missingness preflight, 320 finite
streams, zero daily invariant failures, byte-identical replay, review with no
unresolved P0/P1, `cargo fmt --check`,
`cargo clippy --all-targets -- -D warnings`, `cargo test`, `git diff --check`,
and changed-document link validation. No production function changes occur,
so coverage/CRAP is not triggered.

## Resource bound

One development execution plus one replay, each limited to 320 local CPU
streams and compact JSON. No external service or scarce accelerator is used.

## Exit

Close with one frozen scientific disposition or an exact integrity HOLD.
Neither a universal nor mixed exploratory result authorizes production or
outcome-informed routing.
