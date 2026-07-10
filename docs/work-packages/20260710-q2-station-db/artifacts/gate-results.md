# Gate Results — Q2 Station DB

Date: 2026-07-10
Evidence mode: **Ran** — every row is a command executed this session
with its exit code checked directly (never through a pipe).

## Standard gates

| Gate | Result | Exit |
|---|---|---|
| `cargo fmt --check` | clean | 0 |
| `cargo clippy --all-targets -- -D warnings` | clean | 0 |
| `cargo test --release` | **105 passed, 0 failed** (post-R1 rerun; initially 103 before the finding-1/2/5 regression vectors) — includes the 12-golden byte-identity gates (untouched), the quality suite, and the new 11-test `stations` suite + 6 stations unit tests | 0 |
| Ignored identity suites (`CLIGEN_FMT_SWEEP=/workdir/cligen-rs/target/stage-c-fmt/fmt_pairs.txt cargo test --release -- --ignored`) | 9 passed, 0 failed (untouched by this package) | 0 |
| `cargo llvm-cov` | TOTAL 88.88% regions / 80.64% functions / 91.12% lines | 0 |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | **329 functions (post-R1); none exceed 30; no allow-lists.** First run flagged 4 new-code functions (`StationsError::fmt` 182, `fetch_archive` 110, bin `stations` 58.5, `cache_root_from_env` 33.6); closed by decomposition + real tests: error-render unit test, a loopback-HTTP fetch test (real redirect handling), per-subcommand CLI functions, and a pure `cache_root_from(var)` resolution rule with pinned-order unit tests | 0 |
| `cargo deny check` | advisories/bans/licenses/sources ok. New dependencies: `rusqlite` (bundled SQLite), `ureq`, `tar`, `flate2`. The TLS tree required extending the `deny.toml` allowlist with ISC, BSD-3-Clause, CDLA-Permissive-2.0 (documented in `deny.toml`; all permissive) | 0 |

## Q2 acceptance evidence (all Ran)

| Acceptance | Evidence | Result |
|---|---|---|
| `cargo publish --dry-run` clean under the size limit, no data in the tarball | Post-R1 (finding 3 corrected — the first run's tarball contained the 5.3 KB au fixture payload and the original "no data" claim was false): `tests/fixtures/stations/` is now excluded from packaging; re-run `cargo publish --dry-run -p cligen --allow-dirty` — **75 files, 616.7 KiB (163.5 KiB compressed)**, `cargo package --list` shows zero payload entries | exit 0 |
| Manifests carry SHA-256 + lineage | `crates/cligen/src/stations/manifests.json`: five collections, each with archive sha256/bytes/url + lineage + catalog pin; validated by unit tests (fail-closed vectors for schema version, unknown fields, malformed hashes) | pass |
| Fresh install → sync → run round-trip | `cargo install --path crates/cligen --root <tmp>` → `cligen stations sync us-2015 ghcn-intl` (real network fetch of the private release assets with `CLIGEN_SYNC_TOKEN`, sha-verified) → `cligen stations nearest` (New Meadows 44.97/−116.28 → `id106388.par` at 0.000 km; Jeogla −30.58/152.11 → `all_years/ASN00057011.par` at 0.000 km) → runspecs consuming the emitted cache paths → `cligen run` → **both `.cli` outputs byte-identical to the committed goldens** (`cmp` clean vs `new-meadows-id-seed0.cli` and `jeogla-au-seed0.cli`); quality sidecars emitted | pass |
| Full-network sync of all five collections | `cligen stations sync` (no args) with token: us-legacy, us-2015, ghcn-intl (46.9 MB through the GitHub-API 302→S3 redirect path), au, chile — all verified and published | exit 0 |
| Nearest matches a pinned independent oracle | `artifacts/oracle/nearest-oracle.py` + pinned `expected.json` (committed post-R1, finding 4): 7 query points across all five collections, 5 rows each — **35/35 id+order matches, all distances within 1e-4 km** (re-run after remediation, exit 0); plus the committed 7-station au oracle test (`nearest_matches_pinned_au_oracle`) | exit 0 |
| Corrupted payload / traversal vectors fail closed | `hash_mismatch_fails_closed_before_extraction` (tampered byte → HashMismatch, cache untouched), `traversal_archive_fails_closed` (forged `../evil.par` header → BadArchiveEntry, nothing lands), `catalog_row_count_mismatch_fails_closed`, `network_error_status_fails_closed` (404) | pass |
| Redirect auth hygiene | `network_sync_follows_redirects_without_forwarding_auth` — post-R1 (finding 5) the loopback server asserts the origin request carries the bearer token AND the redirect hop carries no Authorization | pass |

## What these gates do not cover

- A public-visibility fetch (the repo is private; every network sync
  ran with a token). The manifests' API asset URLs work in both
  states, but the tokenless path has never been exercised — it 404s
  until the operator makes the data public.
- `cargo publish` itself (dry-run only; publication is an operator
  action, and would first need a version/readme polish pass).
- Cross-platform behavior of the TLS/SQLite dependency tree (built
  and tested on this Linux host only).
- The au catalog's negative-longitude quirk is carried, not tested
  as a semantic (queries reproduce the catalog as produced).
