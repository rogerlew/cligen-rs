# Five-Collection Conversion Scan

Status: Ran — 2026-07-12

## Inputs

The delegated preflight tokenlessly synced and hash-verified all five Q2
payloads into the gitignored
`/Users/roger/src/cligen-rs/target/a4a-collection-scan`. Embedded manifest JSON
SHA-256:
`86039805acc0a160cb44773b9f02d04cd68173690df34337d794ab5e727c96ef`.

| Collection | Version | Archive SHA-256 |
|---|---|---|
| us-legacy | 2026.07 | `6c84662d4dd2e614b2dd4248dad417960610944840afc7f4c1dce254029972e4` |
| us-2015 | 2026.07 | `f3bf68bb39e65378c1eefc9a956b514fc7cf0fb8e3377e868852f7b3f7b25ab9` |
| ghcn-intl | 2026.07 | `119053deacd1ff8b51cece29bd7e400611ad5da04a1ce72f67ef0fc7274eac21` |
| au | 2026.07.1 | `47f68abb91c06ea4a542da62af7f052ad03aa8f6241b865d99b7f8969e566d1` |
| chile | 2026.07 | `9c3b1f1869927991bc6bfa3807e4da3967231f787fba2961374bff6fa64f920e` |

The executable gate iterates `SELECT par FROM stations ORDER BY par COLLATE
BINARY` in each catalog of record and resolves each row through
`stations::resolve_par`. It deliberately does not walk the payload filesystem:
ghcn-intl retains duplicate 10/20/30-year trees and us-legacy carries an
uncatalogued `temp.par`.

## Command

```text
CLIGEN_DATA_DIR=/Users/roger/src/cligen-rs/target/a4a-collection-scan \
  cargo test --test station_collection_conversion -- --ignored --nocapture
```

Two preliminary invocations used a relative `CLIGEN_DATA_DIR` and failed
before opening a catalog because Cargo runs integration tests from the crate
directory. No evidence is claimed from those setup failures; the absolute-path
command above is the completed run.

## Results

| Collection | Catalog rows | Converted bit-identically | Inherited legacy-invalid | Negative-zero fields |
|---|---:|---:|---:|---:|
| us-legacy | 2,642 | 2,642 | 0 | 0 |
| us-2015 | 2,765 | 2,765 | 0 | 0 |
| ghcn-intl | 12,704 | 12,662 | 42 | 120 |
| au | 7 | 7 | 0 | 0 |
| chile | 1 | 1 | 0 | 0 |
| **Total** | **18,119** | **18,077** | **42** | **120** |

For every converted row the gate proved:

- legacy parse → document → JSON → document → model equality, with every
  `f32` represented by its `to_bits()` bytes;
- deterministic document re-emission;
- exact fixed-width identity strings and wind tensor ordering;
- negative-zero count preservation.

Aggregate SHA-256 over collection name, catalog `par` id, and canonical JSON
bytes in the pinned traversal order:
`5ccb23055e3fae6b4ff95ecd2145f170ce1b972d166beb6304134898befb4da9`.

The 42 ghcn-intl failures are inherited malformed record-1 headers: station
names overflow the fixed `A41` field into state-code columns 42–43, so both
Fortran and SPEC-PAR fail rather than infer shifted values. A4a does not
truncate or normalize them.
