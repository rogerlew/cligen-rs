# Fast Batch RNG Profile Spike

Status: `EXECUTED-COMPLETE` (review dispositions, F2 FMA-host evidence, and
all gates recorded)
Date: 2026-07-10
Evidence mode: Mixed

## Objective

Measure the runtime effect of replacing faithful `ranset` monthly-batch
generation with a versioned, four-lane batched uniform producer. The spike
must preserve the existing daily consumption surface while explicitly
declaring its non-faithful output; it does not establish stochastic parity.

## Scope

Included:

- A `fast_batch_v0` generation profile in SPEC-RUNSPEC and output command
  provenance, defaulting to the unchanged faithful profile.
- A deterministic four-lane batch producer that fills the existing
  `Crandom3State.ranary` 9×31 surface with open-interval f32 uniforms.
- Bypass of `ranset`'s source-specific QC/retry loop only for the new
  profile; faithful `ranset`, seed streams, `dstg`, and daily transforms
  remain available and unchanged.
- Reproducibility, range, profile-provenance, and structural-output tests.
- A separate fast-profile benchmark against the faithful Rust baseline on
  the established 12-workload matrix.

Excluded:

- A claim of bit, trajectory, or stochastic parity with CLIGEN 5.32.3.
- Fast-math, float-reordering flags, unsafe SIMD/intrinsics, or changes to
  `reference/cligen532/`.
- Replacing `dstg`, storm generation, or the downstream daily weather
  transforms.
- Any production recommendation before a separate stochastic-parity
  campaign.

## Authority

- ADR-0001 §§1–3: the reference remains faithful-mode authority; extensions
  require a versioned profile and output declaration.
- `reference/cligen532/cligen.f:4002-4340`: faithful `ranset` batch shape,
  per-parameter streams, and QC/retry protocol being bypassed only by the
  extension.
- `docs/specifications/SPEC-RUNSPEC.md` and new
  `docs/specifications/SPEC-GENERATION-PROFILES.md`.

## Plan

1. Close the preceding profile package; write the profile and runspec
   contract before code.
2. Add the profile boundary and a deterministic, four-lane batch state at
   the existing month-refill seam.
3. Add fixture-independent tests that prove the faithful default remains
   byte-identical and the fast profile is labeled, deterministic, finite,
   and in the required uniform range.
4. Execute a divergence-permitted, structural-output benchmark on the
   established 12-workload matrix and record raw samples and interpretation.
5. Run package gates, coverage/CRAP, and close with no stochastic-parity
   claim.

## Execution & dispatch

Repository: `/home/workdir/cligen-rs`.
Starting branch: current `origin/main`.
Push target: `main`.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- All faithful golden runspec outputs remain byte-identical.
- Fast-profile outputs are deterministic across repeat runs, structurally
  valid, finite, and carry the required profile marker.
- The 12-case benchmark retains raw timing samples and refuses a missing or
  malformed fast-profile output.

## Exit criteria

`EXECUTED-COMPLETE`: the labeled spike, its tests, metrics, and all gates
are committed. The report distinguishes direct measurements from estimates
and says explicitly that stochastic parity is unadjudicated. A legitimate
hold names a toolchain or structural-output blocker and retains completed
evidence.

## Artifacts

- `artifacts/benchmark-plan.md`
- `artifacts/fast-batch-results.json`
- `artifacts/fast-batch-results.csv`
- `artifacts/wepp1-fast-batch-results.json`
- `artifacts/wepp1-fast-batch-results.csv`
- `artifacts/benchmark-report.md`
- `artifacts/disposition-codex.md`
