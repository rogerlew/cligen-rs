# Spine Handoff — Stage S → Stage C

Author: Claude Code (Stage S executor), 2026-07-09.

## What the spine established (imitate these)

- **Module pattern**: `crates/cligen/src/{rng,deviates,qc,crandom3,cbk7,libm_pinned}.rs`
  — every port module carries the attribution header
  (Origin-Class / Migration-Method / Replaces / Precision-Map /
  Faithful-Acceptance), a symbol glossary with source units, and
  source-line citations at every non-obvious transcription point.
- **State pattern**: one struct per live common block, built
  incrementally (`Crandom3State` complete; `Cbk7Seeds` = the `/bk7/`
  block's seed members, extended later by `par`). `SAVE` locals →
  `<Unit>State` structs (`DstgState`). Block-data values → `Default`
  impls citing lines. EQUIVALENCE views → accessor methods
  (`Crandom3State::vvx` etc., 1-based `elem` mirroring source).
- **Signature pattern** (SPEC-GENERATOR-CORE): Fortran args first, then
  `&mut` state in stable order (seeds, unit state, common state).
- **Numerics rules as practiced**: f32/f64 per the source's precision
  map; promotion points transcribed operand-by-operand (see `dstg`'s
  `xx`/`fu` comments); f64 transcendentals via `libm` crate; f32 via
  `libm_pinned`; verbatim source literals with faithful-shape clippy
  `#[allow]`s citing lines (standard §5/§1.3, amended this stage).
- **Test pattern**: per-record tap vectors for pure units; sequential
  state-asserting replay for stateful units; committed samples run in
  `cargo test`, full streams behind `#[ignore]` as a recorded evidence
  gate.

## Stage C unit list (all with tap/fixture acceptance)

1. `jdt` (1817–1845), `jlt` (1846–1903) → `calendar.rs`. Pure integer
   date logic; unit tests from source-derived vectors.
2. `conflm` (4589–4649), `confls` (4650–4704) → extend `qc.rs`.
   `confls` uses `dble()` widening (4662–4663) and calls `cdfchi`.
3. The ACM cluster (4705–7251) → `acm.rs`, uniformly f64: `cdfchi`,
   `cumchi`, `cumgam`, `dinvr`, `dzror`, `erf`, `erfc1`, `exparg`,
   `gam1`, `gamma`, `gratio`, `ipmpar`, `rexp`, `rlog`, `spmpar`.
   ENTRY points `dstinv` (in `dinvr`) and `dstzr` (in `dzror`) become
   separate functions sharing the host unit's state struct (standard
   §5); `SAVE` + `ASSIGN`/assigned-GOTO reverse-communication logic
   translates to explicit state-machine structs.
4. `ranset` (4002–4341) → extend `rng.rs` (or `ranset.rs` if size
   demands): seed init + the QC battery (`ks_tst`/`conflm`/`confls`
   live calls at 4227–4246); `SAVE ell, last_r`; touches `cbk4`/`cbk7`
   station state — port the minimal field slices it reads, extending
   the owning structs.

## Named hazards for Stage C

- **`ranset` + `mox = 0`**: `ranset` runs before `clgen` sets `mox`
  (single writer, 1207), and its `chicnt(j, mox, ichi)` accesses at
  4211/4315 with `mox = 0` under-run the 1-based month dimension in
  Fortran — reading/writing adjacent common storage. Characterize
  against the source layout BEFORE porting; the Rust port must fail
  closed or replicate the exact aliased behavior with a documented
  decision (my `ks_tst` port asserts `mox ∈ 1..=12` and documents
  this). Check whether `ranset`'s QC battery is even reachable before
  `mox` is set in the fixture runs — the taps and run logs can settle
  it empirically.
- **`ranset` refill loops skip `k7`** (4142–4173) — deliberate;
  don't "fix" it.
- **Acceptance for `ranset`**: the `randn` full-stream tap already
  contains every draw `ranset` makes (self-identifying by seed state);
  a `ranset` replay test can verify its draw pattern against the
  capture the way `dstg`'s replay does. Interior taps beyond the
  captured streams (if the K-S/confidence internals need direct
  verification) follow the tap-patch pattern: recorded patch, copied
  tree, never `reference/`.
- **ACM verification**: `confls`→`cdfchi` results feed pass/fail
  decisions whose effects are visible in the captured `randn` stream
  (regeneration draw counts). For direct vectors, glibc-independent:
  the ACM functions are self-contained f64 — construct vectors by
  running the Fortran units through a tap-patched driver if needed.

## Acceptance commands (Stage C must keep these green and extend)

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings   # verify exit code directly
cargo test
cargo test --release --test tap_identity -- --ignored --nocapture
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
```

## Open items the spine leaves deliberately

- `libm_pinned` license provenance review (MIT ARM upstream vs LGPL
  glibc carrier — module header note) → Stage R1.
- The `Cbk7Seeds`-extension pattern when `par` ports the block's
  station fields — recorded in SPEC-GENERATOR-CORE, executed later.
