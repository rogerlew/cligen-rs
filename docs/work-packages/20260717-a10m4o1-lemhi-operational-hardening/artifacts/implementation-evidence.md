# A10M4O1 implementation evidence

Execution date: 2026-07-17
Control host: `rmm` (macOS arm64)
Side effects: repository-local files and temporary local fixtures only

## Implemented contracts

- Toolkit records have a dual reader for `lemhi-toolkit-record-1` and
  `lemhi-toolkit-record-2`; new v2 profiles emit producer
  `lemhi-toolkit-hardening-2` and reject mixed provider APIs.
- Seven declarative v2 providers cover transport, scheduler, recoverable
  storage, L40 accelerator, CPython runtime, PyTorch/NumPy framework, and the
  exact Rust 1.92.0 Linux x86-64 toolchain closure.
- `initialize-authority` creates one exclusive hash-chained ledger genesis;
  `derive-run` preserves immutable authority/budget/resource/branch fields and
  accepts only published source lineage. Live v2 state derives from the
  authority ledger anchor rather than arbitrary `--state-root`.
- Published head checkpoints detect truncation before reviewed state. Every v2
  live reservation/submission requires authority-token scheduler
  reconciliation; ambiguity holds. The documented same-domain rollback limit
  remains explicit.
- Primary submission reserves the frozen recovery contingency before `sbatch`;
  verified cleanup releases it. Capacity admission validates bytes, inodes,
  ownership, mode, filesystem, and minimum free floor; per-base claims
  serialize and are released only by exact identity.
- The v2 Slurm path uses `--export=NONE` and a queryable authority/submission
  token. Environment closure rejects ambient overrides and requires exact
  `PATH`, `TMPDIR`, and pre-import
  `CUBLAS_WORKSPACE_CONFIG=:4096:8` for deterministic CUDA.
- The process supervisor owns a child process group, forwards catchable
  signals, waits, writes durable status atomically, attempts cleanup despite
  status failure, and makes cleanup uncertainty dominant. Recovery validation
  requires settled jobs/steps/requeues and double exact node/UID/marker/path/
  filesystem checks before the committed bounded deletion script.
- Collection authenticates private `RAW_COLLECTED` state before projection.
  Typed longest-first path projection rejects sibling-prefix replacement,
  reserved tokens, invalid UTF-8, duplicate-key JSON, and unknown leaks while
  binding raw parents, sanitized hashes, and token counts.
- Transfers record integer nanoseconds/rates and typed states, revalidate
  skips, and require provider-proved range integrity for resume. Asset manifests
  are content-addressed and append-only within one run lineage; cross-run
  caching remains excluded.

## Application boundary

The agent guide now requires package authors—not toolkit core—to validate
corpus missingness, complete checkpoint cursors, CPU-first checkpoint/RNG
deserialization, and format-aware output completeness. The 5x/10x scientific
runtime labels are unchanged.

## Canonical transition

Canonical v1 remains byte-identical. The package publishes only immutable
semantic candidate `lemhi-a10-py311-l40-v2-candidate`, hash
`5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`.
It contains no status or smoke evidence. The separately scaffolded live smoke
is the only path to an attestation; a later designation-index package is the
only path to current status.
