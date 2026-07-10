# R1 Dispositions — Claude Code (Q2 station DB)

Date: 2026-07-10
Evidence mode: Ran for every remediation (post-remediation gate sweep
re-run; exit codes direct). All six findings **ACCEPTED**.

| # | Sev | Disposition | Applied fix |
|---|---|---|---|
| 1 | MEDIUM | **ACCEPTED.** `--force` had a destroy window: the valid entry was removed before the staging rename, and a rename failure stranded the cache empty with staging leaked. | `publish_staging` (sync.rs): retire-aside → rename staging in → remove retired only on success; a rename failure restores the prior entry and cleans staging. Regression: `forced_resync_with_bad_payload_preserves_the_existing_entry` (failed forced re-sync leaves the valid entry usable; successful `--force` leaves no staging/retired residue). |
| 2 | MEDIUM | **ACCEPTED.** Manifest `version`/`catalog` and catalog `par` values fed `Path::join` unvalidated; hostile metadata could escape the payload root. | `Collection::validate` now requires `version` to be a single normal component and `catalog` a safe relative path; `resolve_par` rejects anything but a bare file name (the SPEC-pinned catalog shape) before any join. Regression: `hostile_catalog_par_values_never_reach_the_filesystem` (absolute, `..`, nested, empty) + manifest-validation vectors. |
| 3 | MEDIUM | **ACCEPTED — my gate claim was false.** The committed au test fixture is real payload bytes and rode in the crates.io tarball while gate-results claimed "no data in the tarball." | `crates/cligen/Cargo.toml` gains `exclude = ["tests/fixtures/stations/"]` (comment cites this finding). Ran: `cargo package --list` shows 0 `fixtures/stations` entries; dry-run re-run: 75 files, 163.5 KiB compressed. Gate-results corrected with a note. Consequence accepted: `cargo test` from a published tarball skips the stations fixture tests (test fixtures are repo-only). |
| 4 | MEDIUM | **ACCEPTED.** The 35/35 five-collection oracle was Ran-but-unreproducible: script, inputs, and expectations were not committed. | `artifacts/oracle/nearest-oracle.py` (generate + compare modes, fixed 7-case input set) and `artifacts/oracle/expected.json` (pinned expectations from the original catalogs) committed; comparison re-run against the synced cache: 35/35, exit 0. |
| 5 | LOW | **ACCEPTED.** The redirect-auth test proved nothing without a token in play. | The vector now sets `CLIGEN_SYNC_TOKEN=test-token-q2`, asserts the origin request carries `Authorization: Bearer test-token-q2`, and asserts the redirect hop carries no Authorization. Env mutation is scoped to this single in-process reader (noted in-test). |
| 6 | LOW | **ACCEPTED.** A relative `CLIGEN_DATA_DIR` produced non-absolute emitted paths against the contract. | `cache_root_from_env` absolutizes a relative root against the working directory (fail-closed if the working directory is unreadable); the pure resolution rule and its unit tests are unchanged. |

Post-remediation gates (Ran, exit codes direct): fmt clean; clippy
clean; `cargo test --release` **105 passed, 0 failed** (stations
suite now 11); llvm-cov ok; CRAP 329 functions none above 30, no
allow-lists; `cargo deny check` ok; `cargo publish --dry-run` 75
files / 163.5 KiB compressed with zero payload entries; oracle
compare 35/35 exit 0.

Net: findings 1-2 hardened the sync path beyond the original tests'
reach, finding 3 corrected a false evidence claim, finding 4 made the
acceptance reproducible. The reviewer's clean-dimension notes
(network posture, hash-before-extract, probe order, tie-breaks,
manifest fidelity, deny honesty) stand as R1 confirmation of the
core design.
