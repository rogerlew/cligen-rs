# A1 Gate Results

Status: Ran — all required gates passed on 2026-07-12.

## Toolchain

| Tool | Version |
|---|---|
| `rustc` | 1.95.0 (`59807616e`, 2026-04-14) |
| `cargo` | 1.95.0 (`f2d3ce0bd`, 2026-03-21) |
| `cargo-llvm-cov` | 0.8.7 |
| `cargo-crap` | 0.3.0 |
| `arrow-array`, `arrow-schema`, `parquet` | exactly 59.1.0 |
| `serde_json` | exactly 1.0.150 |
| Python `pyarrow` | 16.1.0 |
| Python `jsonschema` | 4.23.0 |

## Repository gates

| Command | Result |
|---|---|
| `cargo fmt --check` | Passed |
| `cargo clippy --all-targets -- -D warnings` | Passed |
| `cargo test` | Passed: 153 tests; 10 ignored evidence/environment gates |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | Passed; full test replay completed and LCOV was written |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | Passed: 537 production functions analyzed, 0 above CRAP 30 |

The first CRAP run correctly rejected the original monolithic
`validate_artifact` at 39.9. It was decomposed along schema, digest, mode,
output-selection, and calendar invariants. The final serial coverage/CRAP run
above is the authoritative result; no allow-list or threshold exception was
added.

## Faithful and typed-output gates

- The existing 12-case parity harness reproduced every committed `.cli`
  golden byte-for-byte. This covers continuous, observed padded/truncated,
  and deprecated single-storm output at burns 0 and 17.
- All 10 continuous/observed cases also ran with Parquet enabled. Their text
  remained byte-identical, while the Parquet files contained 78,538 typed
  rows in total. The two storm cases remain text-only and fail closed if
  Parquet is requested.
- Parquet values are projected from retained pre-format `DailyRow` values by
  exact binary32-to-binary64 widening. Tests cover every field, signed zero,
  leap/year-one dates, contiguous simulation indices, non-finite rejection,
  and observed early-source-end coverage. No `.cli` text reparse is present.
- Legacy `.par` and modern station-document runs produce equal climate values
  and parameter-set hashes while retaining different input-schema, input-byte,
  and effective-runspec identities.
- Every text artifact receives canonical provenance even when quality output
  is disabled. Exact text SHA-256 verification, embedded Parquet provenance,
  quality-report propagation, and canonical hash vectors passed.

## Publication and malformed-input gates

Executable tests cover declared output collisions, derived companion aliases,
lexical `..`, symlinks, hardlinks, Unicode casefold/normalization collisions,
reserved staging names, concurrent no-replace publication, failed writes,
record terminators, null-smuggling, mutated resolved runspec state, oversized
burn counts, unsupported storm Parquet, and the frozen text year domain.
Failures do not expose a partial final Parquet file. Successful bundle order is
text, provenance, Parquet, then quality; the package does not claim a
multi-file filesystem transaction.

## Schema and identity evidence

Independent Draft 2020-12 validation checked strict JSON parsing, all seven
changed/published schema resources, offline versioned references and latest
aliases, and independent quality v1/v2 compatibility. It validated 57
provenance sidecars, 41 quality reports, 10 embedded Parquet provenance
payloads, 12 runspecs, and 24 station documents; 23 expressible adversarial
mutations were rejected. Rust validation additionally gates cross-field hashes,
calendar arithmetic, coverage spans, and other semantics JSON Schema cannot
express.

Published-resource SHA-256 values at closeout:

| Resource | SHA-256 |
|---|---|
| `provenance-v1.schema.json` | `c1f2ef184547f6a6e11b1a62472dd40d860443cb69287e5c29b6c102aecdc941` |
| `cli-parquet-v1.fields.json` | `38a8d241d3228813c3899c9c68bcf6f7cdfad229226c5e27621b928e1e36d540` |
| `quality-report-v1.schema.json` | `a25683598c8b22af3f90d53da69c3eee7f282abc64f69677748e2269f6d7b4f9` |
| `quality-report-v2.schema.json` | `3b8234ecfd9fa544c27bd203ce162e009662f390302872ca2b4a6f47c13f4db9` |

The deterministic 40-file A1 golden-output bundle (10 each of text,
provenance, Parquet, and quality, hashed as sorted `shasum -a 256` records)
had aggregate SHA-256
`738fd4f0ff07f0f53a2b29b47a06ed370ca9ca380f823f3de3ed36f2410dd81e`.
The pre-existing committed golden hash manifest itself remains
`7adb04f621d83c4614533157802ab162f6b639281ae4661afba58d72e5b0b812`.
