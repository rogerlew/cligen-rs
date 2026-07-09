# Intake-Path Characterization — `-i` Routing Through `sta_dat`/`sta_name`

Evidence mode: Static (source trace of `cligen.f`, fixture command matrix
from the golden-fixture harness). The par-state snapshot capture
(tap-manifest.md) supplies the Ran confirmation noted at the end.

## The fixture matrix's command shapes

All 12 golden invocations pass `-i<file>.par` and never pass `-S`/`-s`
(fixture-runs.tsv). Command-block state at `sta_dat` entry is therefore
uniform across the matrix:

| Variable | Value | Source |
|---|---|---|
| `istate` | −1 | block data `cligen.f:1079` (no `-S`) |
| `index` | −1 | block data `cligen.f:1080` (no `-s`) |
| `infile` | the `.par` name | `-i` parse `cligen.f:752-753` |
| `numarg` | > 0 | `iargc()` `cligen.f:645` |
| `interp` | 0 (stochastic, single-storm) or 2 (observed `-I2`) | block data `cligen.f:1089`; `-I` parse `cligen.f:812-826` |

## Live trace (every fixture run takes exactly this path)

`sta_dat` (`cligen.f:2240-2483`), entered with `moveto = 0`:

1. `cligen.f:2337-2350` — `moveto ≠ 10`: set `timpkd(0) = 0.0`, call
   `header(version)` (screen banner only, no state effect,
   `cligen.f:2153-2184`). `numarg > 0` skips the "Press Enter" prompt.
2. `cligen.f:2356` — `istate ≤ 0 .and. (infile = "XXX" .or. index ≥ 0)`
   evaluates **false** (`infile ≠ "XXX"`, `index = −1`):
   **`sta_name` is never called** in the fixture matrix.
3. `cligen.f:2363` — same shape, false: the no-stations retry prompt is
   skipped.
4. `cligen.f:2392-2399` — `infile ≠ "XXX"`: `open(10, file=infile,
   status='old', err=55)`, `write(*,*) infile`, `rewind`, `ndflag = 0`.
5. `cligen.f:2427` — `istate > 0 .and. index > 0` false → **else** branch
   `cligen.f:2459`: `read(10,1010) stidd, nst, nstat, igcode` — the
   single-station path: first record parsed as `(a41,i2,i4,i2)`, no
   match against `istate`/`index`.
6. `cligen.f:2470-2471` — `call sta_parms(stidd, index, tp6, wgt, ylt,
   yll, years, elev, itype, timpkd)`. Note the **second argument is
   `index` (= −1), not the `nstat` read from the file** (deliberate
   7/13/00 change, commented-out original at 2468-2469); its only
   consumer is `sta_parms`' interactive display prompt, disabled here
   because `numarg > 0` forces `yc = 'N'` (`cligen.f:2931-2936`).
7. `sta_parms` reads records 2..83, distributes state, closes unit 10;
   `sta_dat` returns with `ndflag = 1` (no retry).

### First-record semantics on this path

`(a41,i2,i4,i2)` over the fixture headers:

| Fixture | cols 42-43 (`nst`) | 44-47 (`nstat`) | 48-49 (`igcode`) |
|---|---|---|---|
| `id106388.par` | 10 | 6388 | 0 |
| `ca046006.par` | 4 | 6006 | 0 |
| `ut422852.par` | 42 | 2852 | 0 |
| `ASN00057011.par` | blank → 0 | blank → 0 | blank → 0 |

`igcode = 0` (wind data present / Penman ET) for all four. `nst`/`nstat`
are read but not consumed on the single-station path (matching happens
only on the `-S`+`-s` path).

## Path census (what Stage C must port vs. fail-close vs. defer)

| Surface | Status in the fixture matrix | Disposition recommendation |
|---|---|---|
| `sta_dat` single-station `-i` path (steps 1-7 above) | **live, exercised** | Port; acceptance = par-state snapshots (all four stations). |
| `sta_dat` `-S`+`-s` matched-scan path (`cligen.f:2427-2455`): buffered line re-read `read(buffer,1010,err=60,end=61)`, skip-on-mismatch, hard `stop " Requested Station Not Found."`) | live surface, **unexercised** by the matrix (non-interactive when both flags given) | Port with constructed-file unit tests (multi-station state files are line-compatible with the single-station header format), or defer with a typed `Unsupported` error. Spine leaves the choice to Stage C; either way no golden acceptance surface exists — say so in the tests. |
| `sta_dat` missing-`-i`-file behavior: `open(err=55)` sets `ndflag = 55`, but with `infile ≠ "XXX"` the retry prompt at 2401-2420 is skipped and control reaches the unit-10 read at 2459 on an **unopened unit** → Fortran runtime I/O abort | error path, unexercised | Fail closed with a typed error (`ParError::Io`). The Fortran behavior is an uncontrolled runtime abort, not a contract; replicate the *fail* semantics (no output produced), not the crash mechanics. |
| `sta_name` (`cligen.f:2486-2652`) | **never called** — every call site requires `infile = "XXX"` (pure interactive) or `-s`-without-`-S` (state prompt loop; still interactive `read(*,1000)`) | Interactive-only surface: the `ranset mox=0` treatment — do not port generation behavior; a stub returning a typed `InteractiveOnly` error (or deferral to the modes/usr_opt package, ROADMAP item 5+) is faithful. Every one of its statements is a `write(*)`/`read(*)` prompt loop plus the `stations` catalog display; no state consumed by generation is produced here (its `istate` write is command-block state that the non-interactive path receives from `-S`). |
| `header` (`cligen.f:2153-2184`) | live, every run | Two banner `write(*)`s; port as a trivial stdout function (or fold into the CLI binary). No `.cli` effect. |
| Interactive station display inside `sta_parms` (`cligen.f:2939-2965`) | dead in matrix (`numarg > 0` → `yc = 'N'`) | Not ported (display-only writes; no state effect). Spine records this; the Rust `sta_parms` omits it. |

## Interpolation-mode routing (which setup unit runs at par time)

`sta_parms` runs `fouri1` (interp = 2) or `ryf1` (interp = 3) for all 14
parameters at `cligen.f:2830-2868`; interp 0/1 run **neither** (linear
`lintrp` is generation-time-only, `day_gen` `cligen.f:3090-3093`).

Golden-matrix coverage:

| interp | Runs in the golden matrix | Par-time setup exercised |
|---|---|---|
| 0 | new-meadows (continuous + single-storm), jeogla | none (cinterp state stays block-data/BSS) |
| 2 | mt-wilson, fish-springs (padded + truncated) | `fouri1` × 14 parameters |
| 1, 3 | **none** | `lintrp` (gen-time) and `ryf1`/`ryf2` unexercised |

Consequence for acceptance: `ryf1`/`ryf2`/`lintrp` bit-identity cannot
come from the 12 golden invocations. The tap capture therefore adds
**capture-only runs** (same commands with the `-I` flag substituted;
same stdin plumbing; outputs *not* goldens) to populate the full
4-station × {0,2,3} snapshot matrix plus `-I1`/`-I3` generation streams.
The non-invasiveness gate remains defined on the 12 golden invocations
only. See tap-schema.md.

## The `timpkd(0:12)` aliasing quirk (load-bearing for the port)

`timpkd` is declared `real timpkd(0:12)` in both `sta_dat` and
`sta_parms`; `timpkd(0) = 0.0` is set in the main program
(`cligen.f:846`) and again in `sta_dat` (`cligen.f:2338`); indices 1..12
are read from the Time Pk record (`cligen.f:2815`, format `(8x,12f6.3)`).
The setup calls pass the **array name**: `call fouri1(timpkd,14)` /
`call ryf1(timpkd,14)` (`cligen.f:2844,2859`). Fortran passes the address
of the first element — `timpkd(0)` — so the callee's `x(1:12)` window is
`[timpkd(0)=0.0, timpkd(1..11)]`: the sentinel zero enters as "January"
and **December (`timpkd(12)`) never participates in parameter-14
interpolation setup**. The Rust port must replicate this shifted window
exactly (it is visible in the `-I2`/`-I3` par-state snapshots).
Parameter 14 additionally has no generation-time evaluator call site
(`fouri2`/`ryf2` are called for parameters 1-3, 6-11, 13 only; grep over
live call sites at `cligen.f:1245-1489`), so the aliased setup state is
write-only in 5.32.3 — still snapshot-verified.

## Other single-writer facts the port relies on

- `interp` has exactly two writers: the `-I` parser (`cligen.f:812-826`)
  and the interactive-restart reset (`cligen.f:963`, unreachable
  non-interactively). Within a fixture run it is constant.
- `wgt(3)`/`site(3)` are populated from the **first record after CALM**
  (`read(10,1030)`, `cligen.f:2883`). In all four fixture files that
  record is blank (" " or 80 spaces), so `site = blanks`, `wgt = 0.0`.
  The station/weight text further down the tail (`---Wind Stations---`
  etc.) is **never read** by 5.32.3 — `close(10)` at `cligen.f:2927`
  follows immediately. `wgt` has no consumer beyond `sta_parms`' disabled
  display (`write` at 2961) and the main program's argument slot; `site`
  is local display-only. Dead-but-parsed surface; SPEC-PAR records it.
- `elev` is read as `i5` from the third record (the "declared integer,
  file has floating-point" source comment at `cligen.f:2253-2254`) and
  converted feet→meters **in place** by `elev = elev*.3048`
  (`cligen.f:2886`): integer→REAL*4 promote, REAL*4 multiply, truncate
  toward zero on integer assignment.

## Ran confirmation (2026-07-09 capture; tap-manifest.md)

Across all 24 capture invocations (12 golden + 12 capture-only):

- Every snapshot's `W` record is `00000000 00000000 00000000` and every
  `S` record is three blank a19 fields (single unique line each across
  all 16 committed combos) — the blank-record read at `cligen.f:2883`
  behaves exactly as traced.
- The unique `H` records are `10 6388 0`, `4 6006 0`, `42 2852 0`, and
  `0 0 0` (jeogla, all-blank GHCN header) — matching the static table
  above verbatim.
- Snapshot `I` records show `interp` equal to each invocation's `-I`
  flag (0 default, 1/2/3 as passed) with `o_mo = 0` at the par-time
  seam; the `-I2` snapshots carry populated `F` (fouri1) records and
  the `-I3` snapshots populated `E`/`Q`/`U`/`Z` (ryf1) records,
  including the parameter-14 shifted-window state.
- All 12 golden invocations of the patched binary reproduced their
  goldens byte-identically (non-invasiveness gate).
