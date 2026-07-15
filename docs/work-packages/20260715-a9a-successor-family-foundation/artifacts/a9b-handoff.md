# A9b calibration-harness implementation handoff

Status: freeze-ready; A9b remains unscaffolded and unauthorized
Predecessor terminal required: `FOUNDATION-READY-A9B`

## Objective

Implement the external, optimizer-neutral A9 research harness and prove it
against synthetic/adverse fixtures. A9b does not fit observed climate, choose
an optimizer as scientific authority, implement either candidate model for
production, generate candidate climate from observed fits, or modify `crates/`.

## Authority set

A9b must copy exact hashes, not prose from memory, from:

- [SPEC-A9-RESEARCH-FOUNDATION](../../../specifications/SPEC-A9-RESEARCH-FOUNDATION.md)
  and its three schemas;
- [model-family envelope](model-family-envelope.md);
- [tuning-harness contract](tuning-harness-contract.md);
- [data/evaluation plan](data-and-evaluation-plan.md);
- [objective registry](objective-registry-v1.json);
- [fixture plan](fixture-plan.md);
- [authority manifest](authority-manifest-v1.json);
- [exposure manifest](exposure-manifest-v1.json); and
- [metadata-only confirmation roster](confirmation-metadata-selection-v1.json).

Any source mismatch is a predecessor-integrity hold.

## Implementation units

Research tooling should live outside production crates, with one documented
command surface. The implementation must provide:

1. canonical JSON encoding and schema/hash validation;
2. data-role manifest construction, disjointness checks, path/hash/key
   firewall, append-only access log, and atomic confirmation transition;
3. immutable fit-artifact read/write and typed fit outcomes;
4. candidate plugin protocol with mock renewal and latent plugins only;
5. optimizer plugin protocol plus a deterministic exhaustive/mock optimizer;
6. Philox4x32-10 counter field, exact length-prefixed identity encoding,
   domain separation, and published golden vectors;
7. Gregorian/nested horizon runner and typed daily/event context;
8. hard-constraint and monthly-moment/quadrature interfaces;
9. objective-registry parser, availability logic, paired-null calibration,
   Pareto calculation, and frozen lexicographic selector;
10. append-only hash-chained attempts, checkpoint/restart, typed resource
    exhaustion, and registered one-retry behavior; and
11. all FX-001--FX-020 fixtures plus a normative-requirement coverage map.

Mock candidate plugins exist only to exercise state semantics and interfaces.
They must not be installed as accepted generation-profile or station-model
values.

## Exact command boundary

The scaffold should define commands equivalent to:

```text
a9-harness validate <artifact>
a9-harness fit --role-manifest ... --candidate-plugin ...
a9-harness evaluate --role development|gate_calibration ...
a9-harness optimize ...
a9-harness calibrate-gates ...
a9-harness confirm --sealed-freeze ...
a9-harness verify-log ...
a9-harness run-fixtures ...
```

Names may change before A9b dispatch, but the permission boundary may not.
`fit`, `evaluate`, `optimize`, and `calibrate-gates` reject confirmation bytes
through path, hash, normalized logical identity, and station-period identity.
`confirm` refuses `metadata_only`, incomplete, reused, or hash-mismatched
freezes.

## Numerical freeze

Before any future observed tuning, A9b freezes:

- Philox test vectors and byte encoding;
- canonical JSON bytes and self-hash rules;
- monthly-moment analytic fixtures for 28/29/30/31 days;
- deterministic quadrature algorithm/order/tolerance;
- objective estimator reference vectors;
- paired-null maximum-statistic implementation; and
- exact replay behavior on the supported host/toolchain.

The research harness may use f64, but every numeric algorithm and library
version is recorded. It cannot call `std`/platform math in a future faithful
path or change faithful arithmetic. A9e will separately adjudicate production
numerics.

## Resource and evidence outputs

A9b is bounded to eight workers, 12 GiB RSS, 24 hours per stage, 72 hours total,
and 50 GiB retained output. Fixture and golden evidence is retained; large
artifacts use LFS at 10 MiB. Scratch output is content-addressed and may be
deleted only after its metrics/hash records are durable.

Required artifacts include implementation/source manifest, schemas mirrored
only where the research tool actually consumes them, fixture input/expected
manifests, golden RNG/canonicalization/moment/objective vectors, role-firewall
mutation results, resource/restart evidence, requirement coverage map,
consolidated review, and gate results.

## A9b review gates

- all 20 fixture groups pass without waiver;
- every SPEC-A9 normative requirement maps to code plus a fixture or static
  invariant;
- fit/optimizer/simulation/member RNG domains and replay vectors are exact;
- both mock class plugins pass the structural non-isomorphism audit;
- role firewall defeats copied, renamed, symlinked, and logically duplicate
  confirmation records;
- null calibration is candidate-blind and baseline-zero safe;
- no accepted runtime ID/schema/default changes and no production function
  changes occur;
- no observed fit/development/gate/confirmation target is acquired or read;
- repository format, Clippy, and test gates pass; and
- review has zero open P1/P2 findings.

## Terminals

- `HARNESS-READY-A9C` — complete synthetic harness and freeze artifacts;
- `HOLD-A9B-SCHEMA-CONTRACT` — artifact/canonicalization semantics do not
  validate or reproduce;
- `HOLD-A9B-RNG-DETERMINISM` — domain separation or replay is not exact;
- `HOLD-A9B-ROLE-FIREWALL` — confirmation can reach a prohibited command;
- `HOLD-A9B-SYNTHETIC-RECOVERY` — a class cannot recover its registered
  synthetic law or classes collapse structurally;
- `HOLD-A9B-OBJECTIVE-CONTRACT` — availability, null calibration, or selection
  is non-executable; or
- `HOLD-A9B-RESOURCE-BOUND` — bounded restart/evidence retention cannot be
  demonstrated.

Every hold names the first failed fixture or requirement. A9c remains
unscaffolded until a separate operator dispatch after `HARNESS-READY-A9C`.
