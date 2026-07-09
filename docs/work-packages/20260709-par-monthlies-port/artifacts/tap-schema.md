# Tap Schema — Par + Monthlies (Stage S extension)

Evidence mode: design (Static) + capture (Ran, recorded in
tap-manifest.md). Extends the item-3 tap pattern (recorded additive
patch, copied build tree, `reference/` untouched, non-invasiveness gate
= golden byte-identity); the item-3 schema document is the design
authority for the conventions reused here.

## Design constraints (inherited, one addition)

- Bit-exact emission: every REAL written as IEEE-754 bits (`Z8.8` via
  `EQUIVALENCE` to `INTEGER*4`). The par state is **REAL*4 throughout**
  (no `DOUBLE PRECISION`/`dble`/`d0` site exists in `cligen.f`
  2656-2970 or 7252-7657 — grep-verified), so the anticipated `Z16.16`
  records are not needed; recorded here so nobody hunts for them.
- Non-invasive: writes only; patched-binary `.cli` byte-identical to
  all 12 goldens (gate result in tap-manifest.md).
- Applied to a copy: `artifacts/tap-build/` (gitignored), patch
  committed as `tap-patch.diff`. This patch is **independent of the
  item-3 patch** — it instruments a fresh copy of the vendored source
  and does not emit the rn/n1/dg/rs streams.
- Self-identifying records: the snapshot is keyed by (station, interp);
  each interpolator record carries the arguments needed to verify it
  against the snapshot state independently.

## Streams (four files per run, opened in the main program before the
argument loop)

### `cligen_par.tap` — unit 96, one snapshot per `sta_parms` completion

Written by an added `tapsnap` subroutine called immediately after
`close(10)` in `sta_parms` (the post-`sta_parms` seam: every state
write including the `fouri1`/`ryf1` setup and the feet→meters `elev`
conversion has happened), plus one `H` record written from `sta_dat`
immediately after the `sta_parms` call returns. Record grammar
(one line each unless noted; all hex fields are f32 bits):

| Tag | Payload | Source state |
|---|---|---|
| `SNAP` | `\|a41\|` station id | `stidd` |
| `I` | interp, o_mo (decimal) | `cinterp` integers |
| `A` | ylt, yll, tp6 | output args |
| `Y` | years, itype, elev (decimal; elev post-conversion) | output args |
| `W` | wgt(1..3) | the format-1030 read |
| `S` | `\|a19\|a19\|a19\|` | `site(1..3)` |
| `K` ×13 | i (0..12), timpkd(i) | `timpkd(0:12)` |
| `R` ×12 | month, rst(m,1..3), prw(m,1..2) | `cbk7` |
| `M` ×12 | month, obmx obmn stdtx stdtm obsl stdsl cvs cvtx cvtm wi rh calm | `cbk7`/`cbk9`/`cbk1` |
| `V` ×64 | dir i (1..16), param j (1..4), wvl(i,j,1..12) | `cbk1` |
| `D` ×12 | month, dir(m,1..17) | `cbk1` |
| `F` ×14 | param, x_bar(p), c(1..6,p), t(1..6,p) | `cinterp` (fouri1) |
| `E` ×14 | param, emv(1..14,p) | `cinterp` (ryf1) |
| `Q` ×14 | param, pmt(1..13,p) | `cinterp` (ryf1) |
| `U` ×14 | param, pmv(1..13,p) | `cinterp` (ryf1) |
| `Z` ×14 | param, xes(1..12,p) | `cinterp` (ryf1) |
| `H` | nst, nstat, igcode (decimal) | `sta_dat` first-record read |
| `DONE` | — | end marker |

191 lines per snapshot. Acceptance: the Rust `sta_parms` port (with
`fouri1`/`ryf1` on the interp-2/3 paths) must reproduce **every** value
bit-exactly from the fixture `.par` bytes.

### `cligen_f2.tap` — unit 97, one line per `fouri2` call

`format(i3,1x,i5,1x,z8.8)`: `indpar ida bits(fouri2)`. Pure function of
`cinterp` state (from the same station's I2 snapshot) and `ida`
(`cbk3`); every record is an independent vector.

### `cligen_y2.tap` — unit 98, one line per `ryf2` call

`format(i3,1x,i3,1x,i5,1x,i3,1x,z8.8)`: `mo jd ntd indpar bits(ryf2)`.
Pure function of the I3 snapshot state and its arguments.

### `cligen_li.tap` — unit 99, one line per `lintrp` call

`format(i3,1x,i3,1x,i5,1x,i3,1x,z8.8,1x,z8.8)`:
`mo jd ntd o_mo bits(lf) bits(rf)`. `lintrp` is pure per-call (its
`data`-initialized local `ni(2)` is reassigned on every call before
use, so the implicit-SAVE hazard is inert); each record is an
independent vector for both outputs plus `o_mo`.

Post-`sta_parms`, nothing but `lintrp` writes any `cinterp` field
(`o_mo`/`lf`/`rf`; `fouri1`/`ryf1` run at par time only), so
per-record verification against the frozen snapshot state is sound for
all three streams.

## Capture matrix

Two classes, 24 runs total (commands in tap-manifest.md):

1. **The 12 golden invocations** — the non-invasiveness gate, plus free
   capture: snapshots for new-meadows/jeogla at interp 0 and
   mt-wilson/fish-springs at interp 2, and the observed `-I2` runs'
   `fouri2` streams.
2. **12 capture-only runs** (seed 0; outputs are *not* goldens): the
   same commands with the `-I` flag substituted, filling the full
   4-station × interp {0,1,2,3} snapshot matrix and producing the
   `ryf2` (`-I3`) and `lintrp` (`-I1`) streams for all four stations.
   Rationale: no golden invocation uses `-I1`/`-I3` (see
   intake-path-characterization.md), so their streams cannot come from
   the golden matrix.

Snapshot equivalence classes confirmed at capture: byte-identical
snapshots for the same (station, interp) across seeds and run modes
(e.g. new-meadows seed0/seed17/single-storm×2 share one hash) — the
snapshot is a pure function of the `.par` bytes and `interp`, which is
what makes it a valid parser acceptance surface.

## Committed samples vs. local full captures

`fixtures/taps/par/<station>-I<n>/` (16 combos) carries:

- `cligen_par.tap` in full (191 lines);
- `f2-sample.tap` / `y2-sample.tap` / `li-sample.tap` — first 1,000
  records of the combo's non-empty streams (I2 → f2, I3 → y2,
  I1 → li).

Full streams stay local under gitignored `artifacts/tap-runs/`, pinned
by SHA-256 in tap-manifest.md; full-stream verification is Stage C's
`#[ignore]`-gated evidence gate, same as item 3.

## Provenance

Build profile identical to the goldens
(`gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math`);
compiler, source, patch, and binary hashes in tap-manifest.md.
