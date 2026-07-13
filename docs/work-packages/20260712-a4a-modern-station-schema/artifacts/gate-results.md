# A4a Gate Results

Status: Ran — all required gates passed on 2026-07-12.

## Repository gates

| Command | Result |
|---|---|
| `cargo fmt --check` | Passed |
| `cargo clippy --all-targets -- -D warnings` | Passed |
| `cargo test` | Passed: 117 tests; 10 ignored collection/network gates |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | Passed with `cargo-llvm-cov 0.8.7` |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | Passed with `cargo-crap 0.3.0`: 377 production functions, 0 above CRAP 30, maximum 28.0 |

The coverage and CRAP tools were absent from the host and installed locally
before running their gates. No allow-list or threshold exception was added.

## Parity and interface evidence

- Four fixture stations round-tripped with exact integers, fixed-width
  strings, and every `f32::to_bits()` value, including negative zero.
- All 12 golden runs validated and ran through both legacy `.par` and modern
  station-document intake. Modern `.cli` bytes equal legacy output and the
  committed goldens; their quality sidecars are byte-identical.
- Deterministic conversion, default modern command provenance, exactly-one
  runspec selection, malformed inputs, collision handling, and conversion
  without cache/home environment variables passed their executable tests.
- Legacy public API boundaries remained available while both input formats
  converged on the crate-private fixed-monthly typed model.

## Published-schema validation

Python `jsonschema 4.23.0` ran as an external Draft 2020-12 validator. It
validated 24 canonical station documents and rejected the Unicode-width,
i32-overflow, and f32-overflow adversarial documents. It also validated the
legacy and modern runspec vectors and rejected a present-but-null station
selector. Repository tests independently inspect the schemas and runtime
fail-closed behavior; `jsonschema` was not added as a runtime dependency.

## Five-collection gate

```text
CLIGEN_DATA_DIR=/Users/roger/src/cligen-rs/target/a4a-collection-scan \
  cargo test --test station_collection_conversion -- --ignored --nocapture
```

Passed in 57.75 seconds: 18,119 catalog rows examined, 18,077 converted with
zero adapter mismatches, 42 inherited malformed ghcn-intl headers rejected,
and 120 negative-zero fields preserved. The deterministic aggregate SHA-256
was
`5ccb23055e3fae6b4ff95ecd2145f170ce1b972d166beb6304134898befb4da9`.
Input versions, archive hashes, traversal rules, and row-level accounting are
recorded in `collection-scan.md`.

## Review

The final adversarial review verdict was **ACCEPT WITH P3 OBSERVATIONS** and
no remaining P1/P2 findings. Direct error-rendering coverage and the full
external schema gate resolved two observations. Atomic destination
publication remains a documented, non-blocking hardening opportunity because
the current converter contract promises collision safety and deterministic
bytes, not atomic replacement.
