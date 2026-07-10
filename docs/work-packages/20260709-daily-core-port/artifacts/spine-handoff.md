# Spine Handoff — Stage S → Stage C

Author: Claude Code (Stage S executor), 2026-07-09.

## What the spine established (imitate these)

- **`daily.rs`**: `clgen` ported, decomposed along the source's own
  blocks (`solar_rmx`, month-boundary + live `ranset` call,
  `gen_precip`, `temps_observed`/`temps_generated` with the shared
  `temp_params`, `gen_radiation`, and the factored `interp_val`
  four-way dispatch — the source repeats that block verbatim per
  parameter; the port factors it with identical per-branch
  arithmetic). The "Tdew -10" screen message became the typed
  [`ClgenEvents`]; the clamp itself is faithful.
- **State homes** (SPEC-GENERATOR-CORE rev 5): new `Cbk3State`
  (`{j, ida}`) and `Cbk5State` (`{r[366], sml}`); `Cbk4State` +
  `nc/nt/mo`; `Cbk1State` + `wv/th/pi2/tdp`; `Cbk7State` + the
  generation scratch (`ra tmxg tmng rmx yls ylc pit nsim msim l`) —
  `/bk7/` is now complete for every live member.
- **Pinned transcendentals**: `tanf_pinned`, `acosf_pinned`,
  `expf_pinned` landed and adjudicated (transcendental-census.md;
  `libm` crate candidates all rejected on sweep evidence). **Stage C
  uses `expf_pinned` in `alphb` and `logf_pinned` in `r5monb`** — no
  new adjudications should be needed; if you meet any other
  transcendental, stop and adjudicate per §1.3 first.
- **Replay pattern**: `tests/daily_identity.rs` — sequential per-day
  replay with entry-state assertions and captured external inputs
  (protocol table in gate-results.md). Reuse its `setup`/`parse`
  helpers for your streams.

## Stage C unit list (tap acceptance already captured)

1. **`windg`** (2020-2122) → extend `daily.rs`. Taps:
   `fixtures/taps/daily/<case>/wg-sample.tap` (`W mo dax Z(v9_in)
   Z(fxx(dax))` + `X Z(wv) Z(th) Z(v9_out) j`). Consumes `fxx(dax)`
   and `v10x(dax)`; writes `wv`/`th` (cbk1), `v9` (cbk7), `j` (cbk3!),
   and **clamps `wvl(j,4,mo)` in place to 0.01 when zero**
   (station-state mutation — replicate). Calm short-circuit when the
   direction search exhausts (`dir(mo,16) ≤ fx`). No new
   transcendentals (`dstn1` internal only). Replay: same day sequence
   as the cg replay, windg after clgen per day — or standalone with
   `v9`/batch state from the cg/wg records (spine recommendation:
   extend the cg replay loop to drive both units per day; the wg
   records interleave 1:1 with cg records by construction).
2. **`r5monb`** (3898-4001) → `daily.rs`. Tap:
   `r5.tap` (`R5 12×Z8.8` post-conversion `wi`). Pure arithmetic +
   `logf_pinned` (`alog(f)`, f ∈ (0,2)); reads `nc` (now in
   `Cbk4State`), `prw`/`rst` (cbk7), converts `wi` **in place** to the
   α = R30/R ratio. Its header comments claiming a `k7` read and `r1`
   write are stale — trust the body (draw-order characterization).
3. **`alphb`** (3817-3897) → `daily.rs`. Taps: `ab-sample.tap`
   (`G mo ida k7(4i5) Z(r(ida)) Z(wi(mo)) Z(sml)` + `H Z(r1)`).
   Consumes one `dstg` draw (k7); `ei = r(ida) - sml`; `ajp` via
   `expf_pinned(-tmax/ei)` for `ei ≥ 1`; writes `r1` (extend
   `Cbk9State` with `ab`/`ab1`/`rn1`/`r1` — the main program sets
   `ab = 0.02083`, `ab1 = 1 - ab` at `cligen.f:879-880`, and warms
   `rn1 = randn(k7)` at 891; cite them in the constructor/setup).
   Requires post-`r5monb` `wi` — run `r5monb` in the replay setup
   before the day loop, exactly as `main:878` does.
4. **Full-matrix `#[ignore]` gates** for wg/ab streams against
   `tap-runs/` (digests in tap-schema.md), recorded in
   gate-results.md; extend the committed-sample tests likewise.

## Named hazards for Stage C

- **alphb's `k7` handoff**: the cg replay treats `k7` as an external
  input because `dstg` advances it between clgen calls. Once your
  replay drives clgen + windg + alphb in day order, `k7` becomes
  internal — the ab record's `k7` entry assertions then localize any
  dstg-draw desync (and the item-3 `dg` streams remain the deeper
  oracle: identical call counts, e.g. 4,822 for new-meadows-seed0).
- **alphb runs only on wet days** (`day_gen:3119,3141` call it under
  the storm branch): the ab records are sparser than cg records —
  match them by `(mo, ida)` keys, not 1:1 interleave. The exact
  day_gen trigger condition should be characterized from source
  before wiring the combined replay (r(ida) > 0 is the expectation;
  verify, don't assume — the truncated-observed case pins EOF edges).
- **`wvl` clamp persistence**: the in-place 0.01 skew clamp survives
  across days (station state); a replay that reloads `ParFile` state
  per day would silently lose it.
- **`j` lives in `Cbk3State`** — windg writes the COMMON loop index;
  keep it in the struct (the source comment mocks it; the port keeps
  it faithful).
- **No SAVE, no f64** anywhere in the three units (census) — any you
  find is a finding.

## Acceptance commands (Stage C must keep green and extend)

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings   # verify exit code directly
cargo test
cargo test --release --test tap_identity -- --ignored --nocapture
cargo test --release --test par_state_identity -- --ignored --nocapture
cargo test --release --test daily_identity -- --ignored --nocapture
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
```

## Open items the spine leaves deliberately

- The combined clgen+windg+alphb day-loop replay (upgrades `k7`/`v9`
  from external inputs to asserted internal state) — Stage C, with
  the day_gen trigger characterization above.
- `ClgenEvents` consumption (the Tdew message surface) — the modes
  package decides its final reporting; nothing to do now.
- `zx` batch column (parameter 9) remains unconsumed until `timepk`
  (item 6).
