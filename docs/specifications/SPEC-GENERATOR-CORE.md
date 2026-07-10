# SPEC-GENERATOR-CORE — Seed/State Surface and Faithful-Mode Shapes

Status: active (rev 7, Stage C of the storm-machinery package)
Surface: the generator core's state ownership and function-signature
conventions — the patterns every ported unit follows.

## Producers / consumers

Producers: the `cligen` crate's port modules (`rng`, `deviates`, `qc`,
`acm`, `monthlies`, `daily`, and `storm`, plus later `modes`). Consumers:
every downstream port module, and (through them) the output surfaces.
Authority basis: `reference/cligen532/` per ADR-0001; unit and state
lines per the ratified decomposition.

## State ownership

- **One struct per live common block** (coding standard §5), built
  incrementally: a block's struct is created by the first package that
  ports one of its units and gains fields as later packages port
  theirs. Current homes: [`Crandom3State`] (`crandom3.inc`, complete),
  [`Cbk7State`] (`cbk7.inc`: seeds, station parameters, rolling
  deviates, and daily generation scratch), [`Cbk4State`] (`cbk4.inc`,
  `iopt` plus daily `nc`/`nt`/`mo` and storm `dtp`/`dmxi`),
  [`Cbk1State`] (`cbk1.inc`, the
  `sta_parms` slice plus daily `wv`/`th`/`pi2`/`tdp`), [`Cbk9State`]
  (`cbk9.inc`, `wi` plus daily `ab`/`ab1`/`rn1`/`r1`),
  [`CinterpState`] (`cinterp.inc`, complete), [`Cbk3State`]
  (`cbk3.inc` live slice), and [`Cbk5State`] (`cbk5.inc` live slice).
- **Unit-local `SAVE` state** is a per-unit struct named `<Unit>State`
  (`DstgState`, `RansetState`, `DinvrState`, `DzrorState`), owned by the
  caller and passed `&mut`. The ACM ENTRY pairs share their host-unit
  state, aggregated for CDF consumers by `AcmState`.
- **No globals of any kind.** All state flows through parameters; the
  future `modes` orchestrator owns every struct.

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
  read-only over that field and does not otherwise port the block. The
  monthlies package applied this narrow rule to `fouri2` before the daily
  package created `Cbk3State`; its established evaluator remains shaped as
  source arguments followed by common state:
  `fouri2(indpar, ida, &CinterpState)`.
- Precision follows each module's declared precision map; faithful-path
  transcendentals follow coding-standard §1.3 (pinned, with each new
  function/domain adjudicated empirically before use).
- Inputs the generator cannot produce (non-positive uniforms, out-of-
  domain cosine arguments, `mox` outside 1..12) fail closed —
  assert/panic — rather than replicating glibc/Fortran special-case or
  out-of-bounds behavior. Each such divergence is documented at the
  function.

## Storm intake seam

- [`SingleStormParams`] is the typed replacement for `sing_stm`'s
  option-4/7 prompt reads: `mo`, `jd`, `ibyear`, `damt`, `usdur`,
  `ustpr`, and `uxmav`, in the source's integer/REAL*4 widths and units.
- `sing_stm(ioyr, ibyear, numyr, single_storm, &mut Cbk4State)` returns
  only the values the source writes (`jd`, `iyear`, and the possibly
  defaulted `numyr`). For options 4/7 it also writes the storm month to
  `Cbk4State.mo`; for option 6, only exact `-1` sentinels default
  (`ibyear = ioyr`, `numyr = 100`).
- Missing values that would make the source enter a prompt loop return a
  typed `InteractiveOnly` error. Output-name prompting and unit-7/8
  open/overwrite management are explicit typed deferrals; filesystem
  policy belongs to the future CLI/output surface.

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
