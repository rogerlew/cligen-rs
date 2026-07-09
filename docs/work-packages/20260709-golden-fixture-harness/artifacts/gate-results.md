# Gate Results

Evidence mode: Ran
Date: 2026-07-09

## Rust Gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS, 8 integration tests |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS, report written to `target/lcov.info` |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS, 25 functions analyzed, 0 over threshold |

Tool versions observed:

```text
rustc 1.92.0 (ded5c06cf 2025-12-08)
cargo 1.92.0 (344c4567c 2025-10-21)
cargo-llvm-cov 0.8.7
cargo-crap 0.2.2
```

## Reference Build / Fixture Gates

| Gate | Result |
|---|---|
| Reference-build provenance recorded | PASS, `artifacts/build-provenance.md` |
| Full fixture matrix generated | PASS, 12 goldens in `artifacts/goldens/` |
| Two independent build/run determinism | PASS, all 12 run-B outputs byte-identical to run-A goldens |
| Fixture manifest records commands, inputs, seeds, hashes | PASS, `artifacts/fixture-manifest.md` and `artifacts/fixture-runs.tsv` |
| QC-regeneration path exercised | PASS, K-S failure/regeneration messages recorded in run logs |
| Hard-truncated `.prn` EOF case captured | PASS, Fish Springs truncated goldens end on 2026-07-07 |
| Interior-taps decision recorded | PASS, deferred to RNG/deviates package in `artifacts/build-provenance.md` |

## Differ Gates

| Gate | Result |
|---|---|
| `.cli` differ implemented | PASS, `crates/cligen/src/cli_diff.rs` and `cligen-cli-diff` |
| Interface spec written | PASS, `docs/specifications/SPEC-CLI-DIFF.md` |
| Zero self-diff demonstrated | PASS, `artifacts/logs/differ-zero-self.log` |
| Perturbation localized | PASS, `artifacts/logs/differ-perturbation.log` reports row 2 `duration_h` |
| Production cross-reference measured | PASS, `artifacts/differ-evidence.tsv` |

## Notes

The first CRAP run exposed two over-threshold harness functions. The final
code decomposes the binary argument path and uses a table-driven field-name
lookup; the final CRAP run reports zero functions over threshold.
