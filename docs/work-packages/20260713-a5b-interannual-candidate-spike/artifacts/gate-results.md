# A5b Gate Results

Status: passed
Date: 2026-07-13 (America/Los_Angeles)
Source snapshot: `10df134607fcf9c22d27aa38a0e27b457f7c176c`

## Repository gates

All commands ran from `/Users/roger/src/cligen-rs` against the completed A5b
worktree.

| Command | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS; includes the 11 overlay tests and 12/12 faithful `.cli` byte parity |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS; report written |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS; 730 functions analyzed, 0 above CRAP 30 |
| `git diff --check` | PASS |

## Contract and mutation gates

| Command | Result |
|---|---|
| `python3 artifacts/fit/fit-a5b-models.py --self-test` | PASS; 7 candidates, 10 mutations rejected, golden SHA-256 `35e5b359017cacf2a8ec9a9a97c988eb447a5db90346f671cafa77dc18552293` |
| `python3 artifacts/runtime/generate-a5b-plan.py --self-test` | PASS |
| `python3 artifacts/runtime/run-a5b-matrix.py --self-test` | PASS; 1,904-run projection, 952 plans, 14 mutations rejected |
| `python3 artifacts/runtime/verify-a5b-evidence.py --self-test` | PASS; 34 positive/mutation checks |
| `python3 artifacts/climate/analyze-a5b-v3.py --self-test` | PASS; 14 checks including unequal generated-sample counts with identical embedded targets, bootstrap order, bounded draws, and Gates 1–7 boundaries |
| `python3 artifacts/wepp/run-wepp-matrix-v7.py --self-test` | PASS; pinned WEPP integration, 2,176-run projection, parser/overflow/recovery/lifecycle/publication mutations |
| `python3 artifacts/wepp/analyze-wepp-v9.py --self-test` | PASS; 26 checks and 2,176 response plus 2,176 execution records validated |
| `python3 artifacts/freeze/verify-accepted-a5a-baseline.py --self-test` | PASS; 544-run matrix, 1,105 archive members, accepted hashes, and three boundary mutations |

The accepted A5a replay retained manifest SHA-256
`e6e12a08b7d552edd45481b929271af87530d2821b9b51d5cec066dc76867cbc`
and verifier SHA-256
`9a3fbdb4d35ec693db6bad916b1cb941c3c3ebec93340a05899f103f269b32f1`.
The A5b overlay is the sole admitted implementation extension and has the
prospectively frozen SHA-256
`05cc96dcf12a7855d883aef573c16f8e6a4691beece58c0bfe20a222ea102ec9`.

## Production evidence gates

| Gate | Result |
|---|---|
| Fit corpus | PASS; exactly 17 archived Daymet objects, 30 complete fit years per station, no post-2009 fit contribution, 17 `ok` fits for every candidate |
| Fit repeatability | PASS; deterministic fit manifest, station bundles, diagnostics, golden, and byte-repeat checks |
| Candidate matrix | PASS; exactly 1,904 unique records = 7 candidates × 17 stations × 2 horizons × 8 replicates |
| Candidate archives | PASS; 7 canonical archives × 952 members = 6,664 members |
| Shared-base archive | PASS; 544 canonical members |
| Candidate lifecycle | PASS; sole `candidate_cli_bytes_removed_after_wepp` transition completed; 1,904 transient CLIs removed after campaign publication |
| Climate analysis | PASS; status `complete`, 14 candidate/horizon gate rows, 2,000-replicate observed-target bootstrap, 84 registered sensitivity projections |
| WEPP matrix | PASS; exactly 2,176 response and 2,176 execution records |
| WEPP archives | PASS; 8 canonical archives × 544 members = 4,352 members |
| WEPP parser audit | PASS; 4 `EffInt` and 13,473 `Sm` fixed-width overflows, 152 `PeakRO` recoveries, and 7 same-day duplicate rows close under the frozen rules |
| Gate table | PASS as evidence; 14/14 rows have Gate 7 true and 0/14 rows pass all seven gates, the registered scientific outcome |
| Public promotion | PASS; no public station model, profile, runspec, provenance, typed-output, or legacy `.par` vocabulary changed |

The post-WEPP candidate manifest SHA-256 is
`6c74128a2d1a3017834474f858fb2ceebe52d5bbe2b39fb3dada953c8440cd06`.
The campaign index SHA-256 is
`4399d2250d699cc2c05c4a7cf0d1bac37dcbeeed0bfe19aa49e57a24c2311d09`.

## Analysis retention gate

The canonical climate analysis was 135,677,893 bytes, exceeding GitHub's
single-object limit. It was archived with deterministic gzip (`mtime = 0`,
level 9):

- archive SHA-256:
  `540a72530d5a6b6b063a951d65c91cb0a903a474e14935a26c8ee88580fef78c`;
- archive bytes: 6,563,160;
- decompressed content SHA-256:
  `7243a51bbb81782d14e8faea1b4d3f01566e7f1c5071b159ca1e6f85dd88f0ac`;
- decompressed bytes: 135,677,893.

An independent decompression/hash/status check passed. No package file remains
above 99,000,000 bytes. The WEPP analysis remains uncompressed at 29,845,878
bytes with SHA-256
`221347acedbf0556ace91d3d64dce99d9e5407855d258f7e097f3bfab4ae873e`.
The generated climate/WEPP evidence archives, compressed climate analyses,
and 29.8 MB WEPP analysis are committed through Git LFS. Source, schemas,
manifests, station bundles, executable contracts, and human-readable reports
remain ordinary Git objects.

## Amendment and failure history

Failed executable-contract versions are retained rather than overwritten:

1. WEPP v4 exposed a valid dry zero-event stream; v5 added the frozen
   zero-event form, then exposed legitimate `EffInt` and `PeakRO` field
   overflows. v6 added source-anchored handling but its archive revalidator
   imposed a positive-record invariant on the zero-event case. v7 corrected
   that audit and completed all 2,176 simulations.
2. Climate analyzer v1 exposed a NumPy/sequence emptiness defect. v2 corrected
   that defect but treated a generated sample count as an immutable embedded
   target identity and therefore closed incomplete. v3 retained target,
   normalization, station-parameter, and minimum-count identity while
   correctly allowing candidate sample counts to differ; it completed.
3. WEPP analyzer v8 correctly refused the incomplete climate evidence. v9
   binds the accepted v3 climate evidence and completed.

Each change is covered by an independent amendment and freeze artifact under
`artifacts/freeze/`; earlier scripts and incomplete evidence remain present.
No version was rewritten after inspecting its output.
