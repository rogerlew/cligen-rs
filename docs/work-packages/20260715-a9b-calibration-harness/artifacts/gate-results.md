# A9b gate results

Status: `PASS`
Executed: 2026-07-15
Dispatch basis: clean `main`/`origin/main`
`795f76775135044f7643e44f1f08cca1136e7236`

## Package and research-tool gates

| Gate | Result | Evidence |
|---|---|---|
| predecessor identity | PASS | 14 A9a/specification files reproduce exact byte lengths and SHA-256 hashes; `FOUNDATION-READY-A9B` present |
| source/dependency capture | PASS | 27 exact source/script records; Python 3.12 and five exact schema-library versions; no observed access |
| command surface | PASS | `validate`, `fit`, `evaluate`, `optimize`, `calibrate-gates`, `confirm`, `verify-log`, and `run-fixtures` executed on synthetic inputs |
| `python3 -m unittest discover -s research/a9_harness/tests -v` | PASS | 5 passed, 0 failed |
| `mypy research/a9_harness --ignore-missing-imports --check-untyped-defs --no-error-summary` | PASS | no type errors |
| `python3 -m pip check` | PASS | no broken requirements |
| `python3 .../verify-a9b.py` | PASS | 20/20 fixtures, two classes, 31 objectives, five normative requirements, eight commands, zero runtime/observed changes |
| full fixture campaign | PASS | FX-001--FX-020 all pass; seven canonical generated evidence files retained |
| deterministic replay | PASS | five core generated artifacts replay byte-for-byte |
| renewal recovery | PASS | 200 calibration/400 validation 100-year replications; scalar coverage 0.9025--0.97; joint 0.9325; four of four fit seeds pass |
| latent recovery | PASS | 200 calibration/400 validation 100-year replications; scalar coverage 0.9075--0.9875; joint 0.9575; four of four fit seeds pass |
| role/access mutation | PASS | path, symlink, rename, copy, bytes, object/logical hash, normalized key, metadata state, concurrent lock, and second consume fail closed |
| RNG/numerical golden | PASS | Random123 Philox zero vector, A9 encoding, canonical JSON, 28/29/30/31-day moments, quadrature, events, Daymet, objectives reproduce |
| optimizer/resource | PASS | all four attempt states retained; replay/retry/checkpoint/corruption/wall/memory/budget/storage/LFS checks pass |
| production/reference isolation | PASS | no diff under `crates/` or `reference/cligen532/`; no network client or accepted runtime surface |
| consolidated review | PASS | `ACCEPT`; zero open P1/P2 findings |

## Repository gates

| Command | Result | Summary |
|---|---|---|
| `git diff --check` plus untracked whitespace scan | PASS | no whitespace error |
| `cargo fmt --check` | PASS | no formatting difference |
| `cargo clippy --all-targets -- -D warnings` | PASS | zero warnings |
| `cargo test` | PASS | 202 registered tests: 192 passed, 0 failed, 10 ignored |

Executed Rust tests include faithful `.cli` golden byte identity and modern
station-document parity. Ignored tests retain their pre-existing explicit
external/full-capture reasons. Coverage/CRAP is not triggered because A9b adds
or changes no production function under `crates/`.

## Evidence identities

The exact implementation and generated-artifact hashes are in
`source-manifest-v1.json`; replay pairs are in
`generated/determinism-replay-v1.json`. All generated files are below 10 MiB.
FX-020 separately proves that retained evidence at or above 10 MiB routes to
the package's LFS-covered `artifacts/large/` namespace.

## Terminal

All gates pass without waiver. Terminal: `HARNESS-READY-A9C`.
A9c remains unscaffolded and requires a separate operator dispatch.
