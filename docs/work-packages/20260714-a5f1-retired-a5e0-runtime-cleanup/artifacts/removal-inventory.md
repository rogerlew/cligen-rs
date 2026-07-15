# A5f1 Removal Inventory

Status: `A5E0-RUNTIME-RETIRED`

## Removed

- `crates/cligen/src/a5e0.rs` — the 1,127-line public experimental module,
  coefficient intake, annual-state runtime, diagnostics, and unit tests.
- `crates/cligen/examples/a5e0_runner.rs` — the package-local research
  executable wrapper.
- `pub mod a5e0` — the unshipped crate-root export.
- `modes::run_to_cli_resolved_a5e0` and the optional extension branches in the
  resolved generator path.
- Exact faithful-stream skip-ahead, seed-period, raw-update accounting, and
  four tests whose only consumer and purpose were A5e0 partition evidence.

The affected `lib.rs`, `modes.rs`, and `rng.rs` files and the two deleted paths
exactly match their state at pre-runtime commit
`27e5e7754bdfafcca649a71d0f5576910433d0d3`.

## Preserved

- `SPEC-A5E0-PILOT` and both research schemas;
- the accepted A5e0 report and its manifest;
- the complete A5e0 and A5f0 work-package artifacts;
- retained raw `target/a5e0` evidence where locally present; and
- implementation commit `1ca40bbe006ed5d823d2dd8e373f720f20d60ba0`.

The historical producers and verifiers are evidence for their execution
commit, not promises that retired research binaries build from current
`main`. Reproduction of A5e0 generation requires checking out the recorded
implementation commit. A5f0's committed derived evidence remains preserved.

## Unchanged

- faithful and native generation-profile identifiers;
- runspec, station, provenance, typed-output, and quality schemas;
- faithful RNG recurrence and `randn` arithmetic/source shape;
- all accepted defaults; and
- the conditional A7 roadmap sequence.
