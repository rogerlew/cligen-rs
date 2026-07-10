# Spine Handoff — Stage S → Stage C

Author: Claude Code (Stage S executor), 2026-07-09.

## What the spine established

- **`storm.rs`**: `timepk` (mode-split draw; the `T` record's k10 is
  exit state), `wet_day_duration` (first `alphb` + the live 3.99
  coefficient), `storm_block` (the full `iopt ≥ 4` chain with the
  deliberate transient infinity and the iopt-4/7 overrides;
  `iopt < 4` fails closed). `Cbk4State` gained `dtp`/`dmxi`;
  `TYMAX` is a cited `storm.rs` constant.
- **Replay** (`tests/storm_identity.rs`): the day loop in `day_gen`
  source order — clgen → **F→C conversion (3110-3112, load-bearing:
  the xmav floor reads Celsius)** → duration → chain — with all ten
  seed streams asserted per record. Protocol notes in
  gate-results.md; 80,906 days + 15,468 timepk calls green.

## Stage C unit list

1. **`sing_stm` typed intake** (3325-3493, characterization in
   storm-chain-characterization.md): a typed function taking the
   storm parameters (`mo jd ibyear damt usdur ustpr uxmav`) and the
   observed-mode `ibyear`/`numyr` defaulting; it **writes `mo` into
   `Cbk4State`** on the 4/7 path (the one state effect). The
   interactive prompts and the unit-7/8 open-with-overwrite dialog
   are NOT ported (the `sta_name` treatment — typed
   `InteractiveOnly`/`Unsupported` errors; file management belongs to
   the CLI binary). Acceptance: unit tests from the characterized
   values (`single-storm.inp` ↔ `SingleStormParams`), no tap surface
   exists (no numeric computation).
2. **Full-matrix `#[ignore]` gates**: extend `storm_identity.rs` to
   the 24-case matrix (the item-5 R1 precedent — don't stop at the 10
   committed cases; digests in tap-schema.md).
3. Gates, exit codes direct.

## Named hazards

- The `jd = dax` equivalence fails for single-storm mode (jd = storm
  date, dax = 1) — already handled in the replay; keep it in mind
  when extending.
- `iopt = 7` is fixture-unreachable: ported as written, no golden
  acceptance — say so in the tests (constructed-vector coverage of
  the override arithmetic is welcome; inventing goldens is not).
- `tp` sample prefixes are shorter than wet-day counts in the sample
  gate (verification skips once exhausted); the full gate asserts
  exhaustion.

## Acceptance commands

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings   # direct exit
cargo test
cargo test --release --test tap_identity -- --ignored --nocapture
cargo test --release --test par_state_identity -- --ignored --nocapture
cargo test --release --test daily_identity -- --ignored --nocapture
cargo test --release --test storm_identity -- --ignored --nocapture
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
```
