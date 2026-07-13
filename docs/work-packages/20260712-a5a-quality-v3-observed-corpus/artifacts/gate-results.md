# A5a gate results

Date: 2026-07-13  
Evidence classification: **Ran**, except where explicitly labeled Static.

## Outcome

A5a executed successfully. The quality-report envelope remains version 2,
the metric vector is version 3, and the observed-target corpus remains an
independent schema version 1. No generation profile, station model, station
schema, or faithful `.cli` behavior changed.

The admissible baseline completed the frozen matrix:

`17 stations × 2 horizons × 8 burn offsets × 2 QC policies = 544 runs`.

All 544 quality reports and all 544 provenance companions validate and are
included with the 17 exact station parameter files in a deterministic
1,105-member evidence archive. Raw `.cli` streams were hashed and removed by
the fixed runner/evidence policy.

## Rust and packaging gates

Ran from the repository root:

```text
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
cargo package -p cligen --allow-dirty
```

Results:

- formatting and Clippy: pass;
- tests: 181 passed, 10 explicitly ignored evidence/integration tests, 0
  failed;
- all twelve faithful golden `.cli` files: byte-identical;
- CRAP: 670 production functions analyzed, 0 above threshold 30;
- package: 97 files, 1.1 MiB uncompressed / 261.1 KiB compressed; packaged
  crate verification compiled successfully;
- the package contains both runtime schema resources, eliminating any
  source-tree-relative runtime dependency.

The frozen historical quality schemas remain byte-identical:

| Schema | SHA-256 |
|---|---|
| envelope 1 / metrics 1 | `a25683598c8b22af3f90d53da69c3eee7f282abc64f69677748e2269f6d7b4f9` |
| envelope 2 / metrics 2 | `3b8234ecfd9fa544c27bd203ce162e009662f390302872ca2b4a6f47c13f4db9` |
| envelope 2 / metrics 3 | `c7c8ff4140d4a810144ad12897493cd923ed95007fbf6e9230d1930f020503b7` |

## Observed corpus gates

The archived source build and verification were rerun without network access:

```text
cargo build --locked --offline --bin cligen-quality-estimator
python build_target_schema.py
python acquire_sources.py
python build_targets.py --metrics-helper target/debug/cligen-quality-estimator
python build_coverage.py
python finalize_manifest.py
python verify_offline.py
```

Results:

- 17 Daymet source objects retain the Q3 source identities;
- 8 GHCN-Daily objects form the independently versioned 2026-07-12 snapshot;
- 25/25 archive hashes pass and all 102 station/source/period coverage rows
  are explicit;
- all four Draft 2020-12 documents validate, with 17 negative schema vectors;
- source manifest, target schema, target corpus, and coverage ledger rebuild
  byte-identically;
- the target corpus is byte-identical under CPython 3.12.7 and CPython 3.14.5;
- the low-frequency target calls the same Rust metrics-v3 function and
  Cargo-locked `libm` implementation as generated reports;
- the manifest binds exact compiler, Cargo/module source closure, `libm`,
  build documentation, archive documentation, and third-party data notice.

Key identities:

| Artifact | SHA-256 |
|---|---|
| source manifest v1 | `50e64236622766c94e0e5b97ee35906210d5793aa9ec70250ea5f0fb5dfe07ec` |
| observed target corpus v1 | `4d0987bb172aef76f3f3a48704bf9df78a375d9d562a145f435800042b5b5660` |
| observed target schema v1 | `c08a915e2f08a5463a0c7fbca63255a6d4bcee64ca243c5f6f604a889fd8f24d` |
| coverage ledger | `cb5c8b1d9a06b4ccfff1a225ea81bb81d2a9371cb432ec0cbe89a34178db1403` |
| final corpus manifest | `cfc27da46ff842547e8bd3134e599a26ab394a9042ed13c820de744649294cae` |
| third-party data notice | `4fb5006ee77a7f47fbf74a99d3539e586134c50d72f371e73623fd7eaca5f720` |

## Executable A5 climate contract

Ran:

```text
python verify-a5-climate-gate-metrics-v1.py
python observed-bootstrap-v1.py
```

The metric contract expands 24 templates into 1,211 exact scalar bindings.
Its semantic verifier passes 51 mutation/parser negatives. The observed-target
reference produces 2,000 deterministic circular-block replicates (8,000
bounded draws) and passes its golden plus 21 mutation/parser negatives.

| Artifact | SHA-256 |
|---|---|
| SPEC-A5-EVALUATION revision 2 | `e774496f4f4bcc3de184b03bed2ce15e774bcdfb6090d92eea9f8c24d32944da` |
| A5b pre-registration | `ee2f29dfc6e1843affe4734260347abb54336d7a3ce74c652b230a2264b95021` |
| metric-cell manifest v1 | `37d2e36fe84a7fafbc2dafdea553a5702fe94677de23a6ba45ac4a4946572d95` |
| metric-cell manifest schema | `f17b6a3896df1226b60a6e1f181089568cab918488d6564caa4ec12baf83be2c` |
| metric semantic verifier | `ae1ef7f06b4afef94910af656f2077ee2029698a42e9223f3a8099a61dac1ac0` |
| observed bootstrap reference | `d154773bb8bd5265e8423360b69fc6acb0cec8cc64280cdee5c1ac705df8d649` |
| observed bootstrap golden | `d38a730371a847e78fb9563821ea7efffa24f364787f902f555634a32f8c2ec2` |

## Baseline campaign and evidence gate

Ran:

```text
python run-baseline-matrix.py \
  target/release/cligen \
  ~/.cache/cligen/stations/us-2015/2026.07 \
  target/a5a-baseline-v1
python verify-baseline-evidence.py --self-test
```

The runner itself rebuilt the binary using:

```text
cargo build --locked --offline --release --bin cligen
```

Compiler provenance is embedded in the manifest: Rust/Cargo 1.95.0,
`aarch64-apple-darwin`, release profile, no `RUSTFLAGS`, wrappers, custom
target, custom target directory, or active Cargo configuration. The manifest
binds the 85-file implementation closure and every evaluation-contract input.
The binary SHA-256 is
`13e85f851748047e83a39173d7722941606e73127d3ff52c968cdfd3514b20d6`.

The independent verifier passed the manifest and analysis schemas, exact
matrix uniqueness/completeness, safe canonical archive metadata, every member
hash and size, all 544 quality schemas, all 544 provenance schemas, report ↔
provenance ↔ `.par` ↔ run-key semantics, per-run metric summaries and numeric
inventories, and exact analysis recomputation.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| baseline manifest v1 | 1,421,606 | `e6e12a08b7d552edd45481b929271af87530d2821b9b51d5cec066dc76867cbc` |
| baseline analysis v1 | 427,519 | `7892cc2d8931623154c33f854db1170e46749e741d08a3843205131329934733` |
| baseline evidence v1 (`tar+gzip`) | 55,928,355 | `2fca565b8c3f83632e73050984dce0c619352ac4bb76deed86fb3928f8de15fe` |

The evidence archive contains 544 reports, 544 provenance documents, and 17
station `.par` files. The temporary target directory is empty after verified
publication.

The independent verifier rejected two pre-publication development attempts
because its exact `command_echo` expectation omitted the declared QC flag and
then the nonzero-burn prefix. Each rejected 1,106-file target was deleted in
full. After the corrected verifier passed an exhaustive scan of all 1,105
archive members, the final 544-run matrix above was generated again from
scratch and bound to verifier SHA-256
`9a3fbdb4d35ec693db6bad916b1cb941c3c3ebec93340a05899f103f269b32f1`.

Descriptively, the across-burn median annual-precipitation SD under faithful
QC was below the `qc_filter: off` value at all 17 stations for both horizons.
The station-median faithful/off ratio was 0.8234368 at 30 years and 0.8931137
at 100 years. This is baseline context, not an A5b candidate result or
promotion claim.

## WEPP response boundary

Ran:

```text
python verify-wepp-response-schema.py
```

The independently versioned WEPP response schema is Draft 2020-12 valid. Four
positive and 28 structural/semantic/parser negatives pass. Every response
record independently binds the schema, protocol, and semantic-validator IDs
and content hashes. No unpinned sibling WEPP executable or input deck was run;
downstream execution remains an A5b responsibility under the pinned protocol.

| Artifact | SHA-256 |
|---|---|
| WEPP response schema v1 | `7d006023684f2079ce09e5ab1af21e1154a417eb4295ebf1a02c40d7f7a2e70d` |
| WEPP semantic validator v1 | `05e7a085f146e264c3b34e3f7c04f498f0f4d3dd0c9b0cd17a0f8176221b683b` |
| WEPP response protocol v1 | `9cd770d18c04dfde877c91e03304697b107d117bf2e52cc94f1f83e3d99c5800` |

## Review

Independent adversarial review verdict: **ACCEPT WITH P3 OBSERVATIONS**.
No P1 or P2 remains open. Nine P2 findings were remediated before the final
evidence run; the review independently replayed the complete 544-run/
1,105-member verifier. Two nonblocking P3 observations carry into A5b as
conformance-test strengthening: an order-sensitive bootstrap toy statistic
and a non-divisor bounded-integer vector. Review SHA-256:
`667d16c3c512f0c00d762c12315223f62c60555ef83531ae2df6b396c232c25c`.

No new reference-binary evidence was produced. Faithful compatibility was
established by the committed golden byte-parity gates; therefore no new
Fortran compiler/libm provenance applies to this package.
