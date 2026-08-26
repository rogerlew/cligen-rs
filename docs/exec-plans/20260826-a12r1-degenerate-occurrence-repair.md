# A12R1 degenerate occurrence repair ExecPlan

## Purpose / Big Picture

Add an explicit, opt-in PRISM localization profile that can transform a donor
month with `P(W/W)=P(W/D)=0` when PRISM precipitation is positive, without
silently changing the ordinary localization profile or pretending PRISM
observes daily persistence.

## Progress

- [x] 2026-08-26: operator authorized positive occurrence repair with a
  warning after reviewing the A12 hot-arid failure.
- [x] Freeze the public flag, algebra, profile and receipt contract.
- [x] Implement and test the repair path without changing default behavior.
- [ ] Independently review, run gates, execute the A12 failure vector, and
  reconcile the package.

## Decision Log

- The repair is explicit-only under profile
  `stochastic_prism_localized_par_degenerate_occurrence_independent_v1`.
- For an exactly all-dry source month and positive PRISM target, derive wet-day
  count as the continuous zero-count limit of the existing halfway adjustment:
  `target / (2 × source_mean_wet_day)`, then apply the existing absolute
  `0.1 .. D-0.25` bounds. Record that continuous limit, snap its wet fraction
  through the exact F6.2 formatter to the positive lattice `[0.01, 0.99]`, and
  recompute the mean from the snapped value so serialization preserves the
  PRISM monthly expectation.
- Set `P(W/W)=P(W/D)=q` at that snapped value. This is a declared
  independent-day assumption, not a PRISM persistence estimate.
- Scale source intensity by the existing limiting factor 2.0. Normal rendering,
  f32 reparse, and encoded constraints remain mandatory.
- Repair only the exact `PWW=PWD=0`, positive-target case. Other invalid
  occurrence states continue to fail closed.

## Plan of Work

Revise SPEC-A10 and A12R1 before production code. Preserve the existing public
two-argument localization and run APIs as disabled-repair wrappers. Add an
opt-in CLI value, a distinct profile ID, structured per-month repair receipts,
stderr warnings, and tests proving default failure plus explicit success on the
A12 donor. Execute a one-year run at the exact A12 point and verify source and
binary receipt hashes.

## Validation

Run focused tests, CLI help/vector tests, formatting, Clippy, the full Rust
suite, LLVM coverage, CRAP, link checks, independent review, and an exact
artifact inspection. Confirmation remains sealed.

## Recovery

Artifact publication remains atomic. Any failed repair or downstream encoded
constraint removes staging and publishes nothing. The ordinary profile remains
unchanged and continues to fail on the A12 vector.

Revision note (2026-08-26): initial operator-authorized implementation plan.
