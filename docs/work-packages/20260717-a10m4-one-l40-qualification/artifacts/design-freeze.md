# A10M4 prospective design freeze

Frozen before asset staging, remote mutation, or allocation on 2026-07-17.

## Exact implementation

The sole model is `N0-l32-w128-d2-lognormal`: a two-layer 128-wide ReLU
encoder, 32-state GRU recurrence, and eight-parameter output head. The package
records its exact parameter count. This is implementation qualification, not a
new candidate identity; no fitted weights survive package cleanup.

One 730-day Daymet window from an accepted `candidate_fit` object supplies the
two deterministic optimizer batches. A separately loaded accepted
`fit_validation` object proves role exclusion and is never passed to the loss,
optimizer, normalization fit, or checkpoint cursor. The package verifies all
98 accepted transfer objects before choosing either object and checks that the
normalization record declares `candidate_fit` only.

The first process performs update 1, atomically checkpoints all frozen state,
then computes update 2 as the uninterrupted control. A fresh process restores
the checkpoint and repeats update 2. Loss bits and every resulting parameter
must be exactly equal on the same L40; tolerances are not widened.

Generation uses a package implementation of Random123 Philox 4x32-10 with the
frozen `station,burn,member,date,draw` layout. Independently keyed station
streams prove order independence. Each 100-year Gregorian stream is generated
once; its 30-year result is a byte-exact prefix. Support is constructive, not
repaired after generation.

## CPU benchmark qualification

The job builds release faithful Rust from the exact source commit with Cargo
1.92.0 and a locally vendored dependency closure. The build is offline on the
compute node. Six inherited parameter files represent all regimes.

After GPU work, a fresh process sets `CUDA_VISIBLE_DEVICES` empty, pins itself
to one CPU from its Slurm affinity, sets all framework thread counts to one,
reloads the CPU export, and executes the frozen two-warmup/nine-alternating-
sample protocol at 30 and 100 years for every station. Logical candidate work
repeats to at least one timed second. Raw samples, medians, repeat counts,
dispersion, output completeness, cold start, peak RSS, export bytes, and exact
host/affinity are retained. This M4 run proves mechanics only: it does not emit
the M3 candidate PASS/WARN/FAIL decision.

## Assets and identities

- CPython runtime, requirements lock, 26-wheel archive: exact canonical records;
- Cargo 1.92.0 x86-64 archive: 10,788,340 bytes, SHA-256
  `e5e12be2c7126a7036c8adf573078a28b92611f5767cc9bd0a6f7c83081df103`;
- source archive: exact scaffold execution commit;
- Cargo vendor archive: `Cargo.lock`-resolved and generated before staging;
- corpus archive: exactly the 98 accepted transfer-manifest paths plus the
  normalized manifest and normalization statistics;
- selected parameter archive: inherited A8a content hash, used only for the
  faithful benchmark.

Every asset is a singly linked regular file under a private allowlisted root,
staged via `.part`, SHA-256 verified, and promoted before submission.

## Resource and safety boundary

- run/package: `a10m4-qualification-r1` /
  `a10m4-one-l40-qualification`;
- classification: `development-only`;
- one attempt, `gpu-icrews`, `gpu:l40:1`, 8 CPUs, 65,536 MiB, 120 minutes;
- revision-1 ledger: 120 requested GPU-minutes;
- evidence allowlist: `evidence.json`, `benchmark.json`, `checkpoint.json`,
  `resource.json`, and exact Slurm stdout/stderr;
- no network in job, retry, requeue, development target series, confirmation
  target, public profile, or candidate score;
- exact marked remote root and scheduler-purged job-local storage are removed
  after verified evidence retrieval.

## Error traps

- Never load Lemhi's advertised modules or ambient Spack compiler paths.
- Build faithful Rust with `/usr/bin/gcc` and `/usr/bin/g++` explicitly.
- Never move the venv after creation or install without `--require-hashes`.
- Do not treat a successful optimizer step as a candidate fit or retain weights.
- Do not read inherited development JSON objects; parameter files are baseline
  inputs, while development target series remain prohibited.
- Do not classify M4 runtime ratios under the M3 selector.
- A Slurm `COMPLETED` state is insufficient without the structured gate receipt.
- A failed attempt atomically supplies explicit unavailable placeholders for
  later-stage allowlisted receipts so the exhausted matrix remains collectable.
- Any failed/ambiguous attempt is reconciled and collected before amendment;
  no invented retry or remote path is allowed.

## Accepted execution amendments

The prospective Cargo-only archive identity above was superseded before the
first successful build by amendment 002. The accepted run uses the complete
official Rust 1.92.0 x86-64 distribution: 192,171,372 bytes, SHA-256
`d2ccef59dd9f7439f2c694948069f789a044dc1addcc0803613232af8f88ee0c`.
Amendments 003--010 preserve the failed hypotheses and prospectively correct
the vendor path, deterministic CuBLAS environment, failure cleanup, masked
Daymet rows, restart cursor, RNG tensor placement, and faithful output
completeness predicate.

The final successful source boundary is `1b791b9`. Its job assets include
`qualify.py` SHA-256
`62af3ec0d1b691788b3601f3d3127046f5c14bbba1a90bb2778cb6601377edec`,
`source.tar.gz` SHA-256
`b6a3c6841f3a9fc0529f526300fb2a8fcd1e64850bd6c4cb9ed1450418eeda96`,
and `cargo-vendor.tar.gz` SHA-256
`13d7f41f3e0d8b45254a1e6070db5b814d54327e9201ccbe22a57269168f0d3c`.
All other final identities are preserved in run 11's toolkit plan and prepare
receipts. The original stable authority ID governed run IDs `r1` through
`r11`; `r2` was a zero-allocation administrative abort, while every allocated
successor received a prospective amendment and remained inside the package
ceiling.
