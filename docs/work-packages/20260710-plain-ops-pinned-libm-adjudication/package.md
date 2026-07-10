# Plain-Operations Pinned-Transcendental Adjudication

Status: `SCAFFOLDED`
Date: 2026-07-10
Evidence mode: Mixed

## Objective

Determine whether the explicit `f64::mul_add` operations in the faithful
pinned f32 `logf`/`cosf` implementations are necessary for bit identity on a
non-FMA CPU. A passing candidate would remove the software-FMA bottleneck
without relaxing faithful behavior; a failing candidate would establish that
the cost is load-bearing.

## Scope

Included:

- Candidate plain-operation variants at each current `mul_add` call site in
  `libm_pinned`'s faithful log/cos paths.
- Bit-for-bit comparison against the existing captured transcendental corpus
  and all 12 golden CLI outputs on the Xeon E5-2697 v2 host.
- A reproducible before/after seed-17 runtime measurement only after a
  candidate passes every fidelity gate.

Excluded:

- Fast math, fused-operation disabling flags, width changes, or any
  acceptance tolerance.
- Changing the fast-batch profile or beginning a stochastic-parity campaign.

## Authority

- ADR-0001 and the Rust Scientific Coding Standard §1.3: faithful
  transcendentals require empirical adjudication against reference captures.
- `crates/cligen/src/libm_pinned.rs`: current pinned f32 log/cos
  transcriptions and explicit `mul_add` sites.
- `20260710-cli-runtime-profile/artifacts/profile-report.md`: non-FMA
  `fma_fallback` attribution motivating the candidate.

## Plan

1. Inventory each relevant `mul_add` operation and the exact existing capture
   coverage.
2. Add a test-only candidate seam with no default behavior change.
3. Run the full transcendental corpus and 12 golden outputs against the
   candidate; record the first bit divergence or complete identity.
4. If and only if identity passes, make the faithful implementation change,
   rerun the runtime benchmark, and close with all production gates.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- Full captured `logf`/`cosf` corpus bit identity and 12/12 CLI golden byte
  identity, or an evidence artifact naming the first divergent input.

## Exit criteria

`EXECUTED-COMPLETE`: evidence decides whether plain operations preserve the
faithful contract; any runtime comparison is labeled conditional on that
result. A divergence is a successful negative result, not permission to ship
the candidate.

## Artifacts

- `artifacts/`
