# A11E5 — Full Interannual Family Stability

Status: `EXECUTED-COMPLETE — NOT_VIABLE_ON_FROZEN_CRITERION`

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

## Outcome

Published source `2eb57485c53d6a85af0cd8ce502314769fe50702`
authenticated the inherited A11E inputs, repeated the canonical calendar and
missingness preflight, and completed all 160 paired station/member rows and 320
daily-core streams. Metrics were finite, daily invariant failures were zero,
confirmation access was false, and the four scientific outputs replayed
byte-identically.

The circular-block treatment materially improved the ten-metric family score
in 142/160 pairs (88.75%), was neutral in 9, and materially worsened 9. It
comfortably passed the one-third benefit threshold. Precipitation dispersion
improved strongly: the monthly median error ratio was 0.632 and the annual
ratio was 0.333 relative to Gaussian. Eight of ten aggregate metric medians
were within the frozen 5% noninferiority bound.

The universal criterion nevertheless failed. Annual temperature dispersion
had a treatment/control median ratio of 1.464, and annual precipitation
lag-one error narrowly exceeded the bound at 1.057. The original member-0
temperature result (0.254 treatment versus 0.412 control) did not persist:
members 1--7 all had higher treatment medians. The terminal scientific
disposition is therefore `NOT_VIABLE_ON_FROZEN_CRITERION`, not a HOLD.

The result supports a bounded successor hypothesis, not immediate routing:
retain the circular-block precipitation mechanism while using a separately
prospective temperature/dependence treatment that preserves cross-variable
coherence. Any hybrid must be specified before seeing its outputs and must
repeat the same noninferiority audit. No production or confirmation action is
authorized.
