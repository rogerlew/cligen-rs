# SPEC-GENERATOR-CORE — Seed/State Surface and Faithful-Mode Shapes

Status: active (rev 6, Stage C of the daily-core package)
Surface: the generator core's state ownership and function-signature
conventions — the patterns every ported unit follows.

## Producers / consumers

Producers: the `cligen` crate's port modules (`rng`, `deviates`, `qc`,
and Stage C's `acm`, plus later `daily`/`storm`/`modes`). Consumers:
every downstream port module, and (through them) the output surfaces.
Authority basis: `reference/cligen532/` per ADR-0001; unit and state
lines per the ratified decomposition.

## State ownership

- **One struct per live common block** (coding standard §5), built
  incrementally: a block's struct is created by the first package that
  ports one of its units and gains fields as later packages port
  theirs. Current homes: [`Crandom3State`] (`crandom3.inc`, complete),
  [`Cbk7State`] (`cbk7.inc`: seeds, `prw`, rolling deviate fields, and
  the station-parameter arrays — renamed from `Cbk7Seeds` when the par
  package landed the block's station fields; remaining generation
  scratch arrives with daily/modes), [`Cbk4State`] (`cbk4.inc`,
  currently the `iopt` slice), [`Cbk1State`] (`cbk1.inc`, the
  `sta_parms` slice), [`Cbk9State`] (`cbk9.inc`, `wi` plus the daily
  intensity fields `ab`/`ab1`/`rn1`/`r1`), and
  [`CinterpState`] (`cinterp.inc`, complete), and — from the daily
  package — [`Cbk3State`] (`cbk3.inc` live slice) and [`Cbk5State`]
  (`cbk5.inc` live slice), with `Cbk4State` gaining `nc`/`nt`/`mo`,
  `Cbk1State` gaining `wv`/`th`/`pi2`/`tdp`, and `Cbk7State` gaining
  the generation scratch members.
- **Unit-local `SAVE` state** is a per-unit struct named `<Unit>State`
  (`DstgState`, `RansetState`, `DinvrState`, `DzrorState`), owned by the
  caller and passed `&mut`. The ACM ENTRY pairs share their host-unit
  state, aggregated for CDF consumers by `AcmState`.
- **No globals of any kind.** All state flows through parameters; the
  orchestrating caller (ultimately `modes`, Stage C+) owns every struct.

## Seeds

- [`SeedState`] is one stream's `k(4)` integer state. The ten
  production streams live in [`Cbk7State`] with block-data defaults
  (`cligen.f:1054-1063`).
- The `-rN` selector maps to `Cbk7State::burn(n)` — n discarded draws
  from `k1..k9`, `k10` deliberately excluded (`cligen.f:723-737`).
- Stream assignments are documented on `Cbk7State`; `k7` is the
  intensity/`dstg` stream and, after the main program's single warm
  draw, is consumed exclusively by `dstg`.

## Faithful-mode function shapes

- A ported unit is a free function named for its source unit, taking
  its Fortran arguments first, then `&mut` state structs in a stable
  order: seed(s), unit-local state, common-block state
  (`dstg(ai, &mut k7, &mut DstgState, &mut Crandom3State)`).
- Functions that the source lets write into a common block do so
  through the passed `&mut` (e.g. `ks_tst` writes `chi_n`), never
  through a return-value side channel that diverges from source
  behavior.
- A source common-block field may be passed as a plain argument before
  that block has an owning Rust struct only when the current package is
  read-only over that field and does not otherwise port the block. Stage
  C applies this narrow rule to `fouri2`: `ida` is passed directly, while
  `Cbk3State` is deferred to the daily package that owns the rest of
  `/bk3/`. The evaluator remains shaped as source arguments followed by
  common state: `fouri2(indpar, ida, &CinterpState)`.
- Precision follows each module's declared precision map; faithful-path
  transcendentals follow coding-standard §1.3 (pinned, with each new
  function/domain adjudicated empirically before use).
- Inputs the generator cannot produce (non-positive uniforms, out-of-
  domain cosine arguments, `mox` outside 1..12) fail closed —
  assert/panic — rather than replicating glibc/Fortran special-case or
  out-of-bounds behavior. Each such divergence is documented at the
  function.

## Modes

Only **faithful mode** exists at this revision. Native f64 mode (A2)
will be specified as a revision here before it lands; generation
profiles and output provenance are SPEC-PROVENANCE's surface (A1).

## Acceptance

Faithful-mode acceptance for core units is bit-identity against the
Fortran tap fixtures (tap schema in the RNG/deviates package):
per-record vectors for pure units, sequential state-asserting replay
for stateful units, full-stream verification as a recorded evidence
gate.
