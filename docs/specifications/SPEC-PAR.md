# SPEC-PAR — Station Parameter (`.par`) Format and Typed Par Model

Status: active (rev 1, Stage S of the par+monthlies package)
Surface: the CLIGEN station-parameter file format as 5.32.3 reads it,
and the `cligen::par` typed model (`ParFile`) that owns it. This spec is
the foundation the A4 par-database/mutation work builds on.

## Producers / consumers

Producers (external): the USDA station-parameter database and the
wepppy/GHCN builder — at least two formatting conventions exist in the
wild (see §Serialization). Consumers: `par::ParFile::parse` (this spec's
implementation), `par::sta_parms` (state distribution into the common-
block structs), Stage C's `sta_dat` intake driver, and later the A4
par-database/mutation utilities.

Authority basis: `reference/cligen532/cligen.f` read sites — formats
`cligen.f:2753-2756` (`sta_parms`), `cligen.f:2324-2325` (`sta_dat`
record 1), read statements 2793-2815, 2881-2883, 2459; the four fixture
`.par` files as concrete instances. Fidelity questions are answered by
those lines, not by external CLIGEN documentation.

## Record grammar

A `.par` file is LF-terminated text records. CLIGEN 5.32.3 reads records
1–83 with fixed-column formats; everything after record 83 is present in
real files but **never read** (adjudicated: `close(10)` at
`cligen.f:2927` immediately follows the record-83 read).

| Record(s) | Format | Fields |
|---|---|---|
| 1 | `(a41,i2,i4,i2)` | `stidd` station name, `nst` state code, `nstat` station code, `igcode` wind/ET flag (0 = wind data → Penman; 1 = none → Priestley–Taylor) |
| 2 | `(6x,f7.2,6x,f7.2,7x,i3,7x,i2)` | `ylt` latitude °N, `yll` longitude °E, `years` of record, `itype` single-storm type 1..4 |
| 3 | `(12x,i5,17x,f5.2)` | `elev` (feet in the file; see §Derived), `tp6` max 6-h precip (in). The TP5 value on this record falls inside the `17x` skip — **unread** by 5.32.3 |
| 4–6 | `(8x,12f6.2)` | `rst(·,1)` mean daily precip (in), `rst(·,2)` std dev (in), `rst(·,3)` skew — 12 monthly values each |
| 7–8 | `(8x,12f6.2)` | `prw(·,1)` P(wet\|wet), `prw(·,2)` P(wet\|dry) — monthly probabilities |
| 9–10 | `(8x,12f6.2)` | `obmx`, `obmn` mean daily max/min temperature (°F; the CV derivation at `cligen.f:2894-2898` adds the 459.67 Rankine offset and the source comment pins Fahrenheit) |
| 11–12 | `(8x,12f6.2)` | `stdtx`, `stdtm` temperature std devs (°F) |
| 13–14 | `(8x,12f6.2)` | `obsl` mean daily solar radiation (Langley/day), `stdsl` std dev |
| 15 | `(8x,12f6.2)` | `wi` max .5-h precip — **intensity (in/h) in the file**, halved to depth at load (§Derived) |
| 16 | `(8x,12f6.2)` | `rh` mean dew point (°F) |
| 17 | `(8x,12f6.3)` | `timpkd(1..12)` cumulative time-to-peak distribution (fraction) |
| 18–81 | `(8x,12f6.2)` | `wvl(i,j,1..12)`: 64 records, direction `i` = 1..16 outer, parameter `j` = 1..4 inner (% time, mean speed m/s, std dev, skew) — implied-DO order `(((wvl(i,j,k),k=1,12),j=1,4),i=1,16)` |
| 82 | `(8x,12f6.2)` | `calm(1..12)` % calm by month |
| 83 | `(a19,f6.3,2(2x,a19,f6.3))` | `site(1..3)`/`wgt(1..3)` wind-interpolation stations + weights. In all four fixtures this record is blank (the station/weight text lives in the *unread* tail), so `site` = blanks, `wgt` = 0.0 |
| 84+ | — | Tail (`INTERPOLATED DATA…`, `---Wind Stations---`, station/weight rows). Retained verbatim by the typed model; never parsed |

The 8-column row labels (` MEAN P `, `% NNW   `, …) fall inside the `8x`
skip: CLIGEN never validates them, and `ParFile` treats them as part of
the retained record bytes (no label validation — variant labels must not
fail a file 5.32.3 would read).

## Fortran read semantics (normative for `parse`)

- **Fixed columns.** Fields are column slices of the record; a record
  shorter than a field's extent is blank-padded (`PAD='YES'` default).
- **Blank handling.** `BLANK='NULL'`: all blanks inside a numeric field
  are ignored; an all-blank field is 0 (`0.0`). Parse strips blanks
  before conversion.
- **F-editing.** An explicit decimal point overrides the format's scale.
  A decimal-point-free field is scaled by 10⁻ᵈ (d = 2 or 3 per the
  format). No corpus instance lacks the point; the rule is implemented
  for fidelity.
- **Decimal→f32 conversion** is correctly-rounded (Rust `str::parse`
  guarantee). A double-rounding divergence against gfortran's runtime
  conversion is theoretically possible and empirically excluded for the
  corpus by the par-state snapshot identity gate; any future mismatch is
  a discovery to characterize, not absorb.
- **Failure behavior (fail closed):** fewer than 83 records; a numeric
  field that is non-blank yet unparseable after blank stripping. Both
  produce typed `ParError`s. A missing/unopenable file is an I/O error
  before parse (the Fortran counterpart aborts on an unopened unit —
  see intake-path-characterization.md).

## EQUIVALENCE views (`cligen.f:2783-2787`)

`sta_parms` declares `rst1/rst2/rst3` ≡ `rst(1,1)/rst(1,2)/rst(1,3)` and
`prw1/prw2` ≡ `prw(1,1)/prw(1,2)`: in column-major Fortran these are the
**columns** of `rst(12,3)`/`prw(12,2)` viewed as 12-vectors (the aliasing
census's second site; the interpolation setup is called on them:
`fouri1(rst1,1)` etc.). Rust translation per coding-standard §5: the
owning struct (`Cbk7State`) exposes accessor methods (`rst_col(j)`,
`prw_col(l)`) returning the 12-month column — never duplicated storage.

## The `timpkd` window quirk (normative)

`timpkd` is `real timpkd(0:12)` with `timpkd(0) = 0.0` set by callers.
`sta_parms` passes the array name to `fouri1`/`ryf1` as parameter 14
(`cligen.f:2844,2859`), so the callee's `x(1:12)` is
`[timpkd(0), timpkd(1..11)]` — the sentinel zero participates and
December does not. Faithful consumers must reproduce this window
exactly. (Parameter 14 has no generation-time evaluator call site in
5.32.3; the state is still snapshot-verified.)

## Derived state at load (owned by `par::sta_parms`, not `ParFile`)

Applied after the raw reads, before any consumer sees the state:

- `wi(m) = 0.5 * wi(m)` — intensity→depth (`cligen.f:2810-2812`, B. Yu).
- `elev = int(real(elev) * .3048)` — feet→meters, truncation toward
  zero (`cligen.f:2886`).
- `cvtx/cvtm = stdt·/(obm· + 459.67)`, `cvs = stdsl/obsl` with the
  `obsl ≤ 0` guard (`cligen.f:2889-2904`).
- `dir` cumulative wind-direction distribution from `wvl(·,1,·)`,
  17th column = 100.0, all ×0.01 (`cligen.f:2910-2925`).
- `interp = 2` → `fouri1` × 14 parameters; `interp = 3` → `ryf1` × 14;
  other values → no setup (`cligen.f:2830-2868`).

## Serialization

Two surfaces, two invariants (full adjudication with corpus evidence:
the package's `par-roundtrip-adjudication.md`):

1. **`to_bytes()` (implemented now):** emits the retained records
   verbatim. Invariant: `to_bytes(parse(b)) == b` for any accepted
   input — gated on all four fixtures. Rationale: a canonical formatter
   cannot reproduce the corpus (two zero-rendering conventions, one of
   them section-mixed inside a single file; per-row decimal conventions;
   producer-dependent record-1/tail shapes) — value→text is not
   injective across real producers, so presentation is retained as
   lexemes rather than faked as data.
2. **Canonical rendering (specified now, implemented by A4):** mutated
   records are re-rendered in the USDA convention — 6-char fields,
   suppressed leading zero (`  .26`, ` -.26`), row-family decimals
   (2; 3 for Time Pk), 8-char canonical label. Invariant (semantic
   fixpoint): `parse(canonical(v)) == v` bit-exactly for every field
   family — canonicalization must never perturb a typed value.
   Untouched records keep their original bytes (minimal-diff mutation).
   No corpus instance exercises a negative bare-dot value; the `-.26`
   form is specified from the F-edit width rules, flagged for A4 to
   verify against a producer instance before relying on it.

## Provenance obligations

None carried in the file itself (the format has no provenance fields).
Station lineage for generated outputs is SPEC-PROVENANCE surface; the A4
par database owns par-mutation lineage.

## Acceptance

- Par-state snapshot bit-identity: parse + `sta_parms` distribution
  reproduce every captured value for all four stations × interp
  {0, 2, 3} (tap schema: `fixtures/taps/par/`, 191-line snapshots).
- Byte round-trip: `to_bytes(parse(b)) == b`, all four fixtures.
- Both run in `cargo test` (committed samples); the full-matrix
  verification recipe is in the package's tap-manifest.md.
