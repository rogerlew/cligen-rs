# Spine Handoff — Stage S → Stage C

Author: Claude Code (Stage S executor), 2026-07-09.

## What the spine established (imitate these)

- **Par model**: `crates/cligen/src/par/{mod.rs,file.rs,sta_parms.rs}` —
  `ParFile` is the typed read surface **plus retained raw records**
  (SPEC-PAR; the round-trip adjudication is
  `par-roundtrip-adjudication.md`: typed-values-only byte round-trip is
  unreachable in this corpus, lexeme-preserving `to_bytes` is the gated
  invariant). `sta_parms(par, &mut bk7, &mut bk1, &mut bk9, &mut ci)`
  is the faithful distribution + derivation unit; the interactive
  display block is not ported (dead on all non-interactive paths).
- **State pattern extended**: `Cbk7Seeds` → **`Cbk7State`** (rename
  decision recorded in the struct header and SPEC-GENERATOR-CORE
  rev 3) with the block's station arrays and the `rst_col`/`prw_col`
  EQUIVALENCE accessors; new `Cbk1State` (sta_parms slice),
  `Cbk9State` (`wi` slice), `CinterpState` (complete, block-data
  `interp = 0` cited).
- **Monthlies**: `monthlies.rs` carries `fouri1` + `ryf1` with the
  package's transcendental adjudication in the module header. The
  parameter-14 `timpkd(0:12)` aliased window is constructed explicitly
  in `sta_parms` — do not "fix" it (SPEC-PAR §timpkd window quirk).
- **Pinned transcendentals**: `libm_pinned` gained `sinf_pinned`
  (ARM sibling of `cosf_pinned`, shared tables) and `atanf_pinned`
  (glibc 2.39 **11-term** fdlibm, plain f32 ops — no FMA: the pinned
  host's ifunc resolves the SSE2 build). `libm::atanf` is REJECTED for
  faithful paths (5-term polynomial, 1-ULP divergence; evidence in
  gate-results.md). New rule of thumb the adjudication produced: the
  fdlibm bit-pattern comments can be stale (`aT[0]` is 0x3EAAAAAB, not
  the commented 0x3eaaaaaa) — verify constants against a compiled
  object, not comments.
- **Test pattern**: `tests/par_state_identity.rs` — snapshot parser +
  the full-matrix identity gate (4 stations × interp {0,1,2,3}, every
  snapshot value asserted bit-exactly) + the byte round-trip and
  fail-closed tests. Snapshots are committed complete (191 lines/combo
  under `fixtures/taps/par/`), so this gate runs entirely in
  `cargo test`; only the *interpolator streams* have committed-sample
  vs local-full splits.

## Stage C unit list (all with tap acceptance already captured)

1. **`fouri2`** (7387–7423) → extend `monthlies.rs`. Per-record vectors:
   `fixtures/taps/par/<station>-I2/f2-sample.tap`
   (`indpar ida bits`, format i3,1x,i5,1x,z8.8) verified against the
   same station's I2 snapshot state loaded via the Stage S snapshot
   parser + `sta_parms`. Uses `cosf_pinned`; f32 throughout; reads
   `ida` (cbk3 — a minimal `Cbk3State` slice or a plain argument;
   spine's recommendation: argument now, struct when `daily` ports).
2. **`ryf2`** (7545–7657) → `monthlies.rs`. Vectors:
   `y2-sample.tap` (`mo jd ntd indpar bits`) against I3 snapshot state.
   Pure f32 arithmetic; note `xes(mo,·)` is read with the *non-leap*
   month index even in the leap-February branch — transcribe, don't
   reason.
3. **`lintrp`** (7252–7337) → `monthlies.rs`. Vectors: `li-sample.tap`
   (`mo jd ntd o_mo bits(lf) bits(rf)`). Writes `o_mo`/`lf`/`rf` into
   `CinterpState`. Its `data`-initialized local `ni` is reassigned
   every call (`ni(2)` per leap year) — no implicit-SAVE state to
   carry.
4. **`sta_dat`** (2240–2483) + **`header`** (2153–2184) intake drivers
   on the characterized live paths (intake-path-characterization.md):
   the single-station `-i` path is the exercised surface (acceptance:
   the `H` records already asserted in the identity test — wire the
   driver so it produces the same `ParFile`/`sta_parms` flow); the
   `-S`+`-s` matched-scan path is live-but-unexercised — port with
   constructed-file unit tests or defer with a typed error (spine left
   the choice open; either way state the acceptance honestly).
   `header` is a stdout banner.
5. **`sta_name`** (2486–2652): interactive-only (never called in the
   fixture matrix) — fail-closed/defer with the `ranset mox=0`
   treatment; do not port prompt loops.

## Named hazards for Stage C

- **Full-stream evidence gate**: the committed `f2/y2/li` samples are
  first-1,000-record prefixes. Add `#[ignore]`-gated full-stream tests
  against `artifacts/tap-runs/` (hashes in tap-manifest.md) mirroring
  `tap_identity.rs`'s split, and record the run in gate-results.md.
  Non-empty stream coverage: f2 on 6 golden observed runs + nm-I2 +
  jg-I2; y2 on the four `-I3` capture-only runs; li on the four `-I1`
  runs.
- **`fouri2`/`ryf2` per-record verification needs the snapshot state
  first** — load the station's `.par`, run `sta_parms` with the right
  `interp`, then evaluate records. The identity test already proves
  that state bit-exact, so any stream mismatch localizes to the
  evaluator.
- **`ryf2`'s `mjd = float(jd) - 0.5`** and the quarter-month ratio
  branches are exact-comparison sensitive (`xes == -9999.0` sentinel
  checks): keep `#[allow(clippy::float_cmp)]` with citations, as
  `ryf1` does.
- **CRAP**: decompose along source-internal structure if a unit's `?`/
  branch count pushes complexity ≥ 30 (`ParFile::parse` precedent in
  gate-results.md); never `--allow`-list.
- **`elev` truncation**: already inside `sta_parms`; `sta_dat` must
  not re-convert.

## Acceptance commands (Stage C must keep these green and extend)

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings   # verify exit code directly
cargo test
cargo test --release --test tap_identity -- --ignored --nocapture
cargo test --release --test par_state_identity -- --ignored --nocapture   # once full-stream tests exist
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
```

## Open items the spine leaves deliberately

- ~~`atanf_pinned` SunPro-license provenance~~ **RESOLVED post-spine
  (operator-directed, 2026-07-09)**: NetBSD rev 1.4 original fetched
  and diffed against the glibc 2.39 carrier — all protectable
  expression is Sun/NetBSD under the SunPro notice; the single
  glibc-era element (2^25 huge-arg threshold, commit 9a71f1fc,
  BZ #18196) is dispositioned as an uncopyrightable functional
  constant, and the transcription is sweep-verified against the
  reference runtime across the reduction band, the huge band, ±inf,
  and NaN. See `atanf-sunpro-provenance.md` +
  `fdlibm-sunpro-LICENSE.txt`. R1 now *verifies this record* instead
  of performing the adjudication.
- The canonical `.par` renderer (SPEC-PAR §Serialization invariant 2)
  is specified but deliberately unimplemented — A4 surface, not
  Stage C.
- `Cbk3State` (only `ida` needed by `fouri2`) — argument vs struct
  slice left to Stage C; whichever lands, record it in
  SPEC-GENERATOR-CORE.
