# Tap Schema — Stage S

Evidence mode: design (Static) + capture (Ran, recorded below and in the
tap manifest).

## Design constraints

- **Bit-exact emission**: every REAL value is written as the hex of its
  IEEE bits (`Z8.8` via `EQUIVALENCE` to `INTEGER*4`), never as decimal
  text. Acceptance can therefore never be contaminated by formatting.
- **Non-invasive**: the tap patch adds writes only; the patched binary's
  12 `.cli` outputs must remain byte-identical to the committed goldens
  (verified at capture; see manifest). Taps never alter control flow or
  arithmetic.
- **Applied to a copy**: `reference/cligen532/` is untouched; the patch
  applies to a copied build tree under this package's (gitignored)
  `artifacts/tap-build/`, and is committed as `tap-patch.diff`.
- **Self-identifying records**: each record carries the state needed to
  verify it independently (or, for `dstg`, to replay sequentially with
  per-call assertions), so acceptance does not depend on reconstructing
  global call order across streams.

## Stage S streams

Three tap files per fixture run, opened in the main program before the
argument loop (so `-r` burn draws are captured), written from inside the
tapped units:

### `cligen_rn.tap` — unit 91, one line per `randn` call

```
format(4i4,1x,z8.8)
k(1) k(2) k(3) k(4)  bits(randn)
```

`k(1..4)` is the seed state at entry (before the internal advance and
rejection loop); the hex field is the returned f32's bits. Every record
is an independent test vector: `randn(state) == value`. All ten seed
streams (`k1`–`k10`) and every caller (`clgen`, `ranset`, `dstg`,
`timepk`, `windg` batches, `-r` burn) appear in call order; records are
self-identifying via the state tuple.

### `cligen_n1.tap` — unit 92, one line per `dstn1` call

```
format(3(z8.8,1x))
bits(rn1) bits(rn2) bits(dstn1)
```

`dstn1` is a pure function of its two uniform arguments; every record is
an independent vector.

### `cligen_dg.tap` — unit 93, one line per `dstg` call

```
format(i3,1x,i3,1x,4i4,1x,z8.8,1x,z8.8)
mox iarrct k7(1) k7(2) k7(3) k7(4)  bits(ai) bits(dstg)
```

`mox`, `iarrct` (the SAVE'd batch cursor), and `k7` are captured at
entry; `ai` and the result at return. Verification is a **sequential
replay per fixture**: initialize from the FIRST record's captured state
(`k7` as recorded; `iarrct` must be 30; `chicnt(10,·,·) = 0`), then for
each record: assert the recorded `iarrct`/`k7` match the replay state
(catching any un-modeled external mutation immediately, with
localization), set `mox` from the record, call `dstg(ai)`, assert the
result bits. Initializing from the first record (rather than block-data
defaults) is necessary because `k7` has pre-generation history: the
complete `k7` site list is the `-r` burn (`cligen.f:733`), one warm
draw in the main program (`cligen.f:891`), and `dstg`'s own batch
refills (`cligen.f:1727`) — `ranset` deliberately skips `k7` in both
its warm and refill loops (4100–4116, 4142–4173 touch every stream
except `k7`). After the first `dstg` call, `k7` evolution is therefore
dstg-exclusive, `chicnt` row 10 is dstg-exclusive (writers: 1729, 1750
only), and `mox` has a single writer (`clgen:1207`) and is treated as a
per-record input. The capture itself confirmed this closure: first
records show `iarrct = 30` with warmed (non-default) `k7`, and
subsequent records evolve consistently with dstg-only consumption.
QC-regeneration events are implicit in the stream: a K-S rejection
consumes 30 further uniforms, which the `iarrct`/`k7` assertions verify.

`ks_tst` has no separate tap: it is exercised and verified through the
`dstg` replay (a wrong verdict desynchronizes `iarrct`/`k7` at the next
record) and by direct constructed-vector unit tests in Rust.

## Fixture coverage

All 12 golden invocations from the fixture-harness manifest are
captured. Full tap files are large (the `randn` stream records every
draw of a multi-decade run) and stay local under gitignored
`artifacts/tap-runs/`, pinned by SHA-256 in `tap-manifest.md`. Committed
for in-repo testing: the `dstg` taps in full (small) and the first 1,000
records of each `randn`/`dstn1` tap, under `fixtures/taps/`. The
full-file verification runs as `#[ignore]`-gated tests against the local
capture tree and is recorded as Ran evidence in `gate-results.md`.

## Provenance

Tap binaries are built from the patched copy with the same pinned
profile as the goldens (`gfortran -O0 -ffp-contract=off -fprotect-parens
-fno-fast-math`); compiler, source and binary hashes in
`tap-manifest.md`. The non-invasiveness gate (patched-binary `.cli` ==
golden, all 12) is part of the manifest.

## Stage C streams

The additive Stage C patch opens two more files in a second copied build
tree. It retains every Stage S tap and does not modify the vendored source.

### `cligen_rs.tap` — unit 94, 24 lines per `ranset` call

Each record contains:

- `B`: entry `mox`, `ntd`, `iyear`, `iopt`, `ell`, and the two current
  `prw` bits;
- `K` + `L`: all ten entry seed arrays and all nine `last_r` bit patterns;
- `E`, `K`, + `L`: exit month/`ell`, seeds, and `last_r`;
- nine `A`/`G` pairs: all 31 `ranary` values for that parameter plus
  `g_dimi`, `g_dimp`, binary64 `g_dsum`/`g_ssum`, and all 20 `chicnt`
  cells for the current month.

The replay initializes from the first record, asserts every entry state that
has no external writer, supplies the three source-identified externally
advanced streams (`k5`, `k7`, `k10`), invokes `ranset`, then asserts every
captured exit and common-block value. Thus QC verdicts, retry draw counts,
mixed-precision accumulation, SAVE state, and preserved `ranary` tail cells
are checked at every call. At the first record, the replay also computes one
draw from each captured entry seed and asserts the nine common-block rolling
values initialized at `cligen.f:4099-4117`.

### `cligen_stagec.tap` — unit 95, direct unit vectors

`stage-c-vector-driver.f` is linked only into the copied reference build. It
emits integer results directly and every REAL/DOUBLE PRECISION result as
`Z8.8`/`Z16.16` IEEE bits. The committed 919-line fixture covers exhaustive
365/366-day `jlt` calendars, the valid single-storm `ntd` shape, `jdt`
boundaries, the confidence routines, all ACM public units, both reverse-
communication directions, and all three `gratio` accuracy selectors.

The Stage C build profile, patch/driver/source/binary hashes, per-case stream
hashes, and the representative final non-invasiveness rerun are recorded in
`tap-manifest.md`.
