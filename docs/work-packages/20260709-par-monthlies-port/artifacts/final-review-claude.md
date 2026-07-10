# Stage R2 Final Review — Claude Code

Reviewer: Claude Code (Stage S author; R2 per the package's cross-review
structure), 2026-07-09.
Evidence mode: Ran (independent gate re-runs, byte-level stdout
comparison, merge verification) + Static (targeted source-vs-port
reads).

## Verdict

**CLOSE — `EXECUTED-COMPLETE`.** All package acceptance criteria are
met on merged `main`; both reviews are dispositioned; no tolerance
exists anywhere on the acceptance surface. Two low-severity
observations are recorded below (accepted, non-blocking).

## Merge reconciliation (performed as part of R2)

Stage C/R1 landed on `agent/flat-file-modernization`, which had forked
before `main`'s operator-directed provenance commit (`84b0617`). R2
merged the branch into `main` (merge commit recorded in history),
resolving:

- `libm_pinned.rs` header: combined the R1 verbatim SunPro notice with
  the main-side lineage/threshold adjudication summary.
- Provenance artifacts: the main-only `atanf-sunpro-provenance.md`
  (NetBSD rev 1.4 float-lineage anchor; the single glibc-era delta —
  2^25 threshold, commit `9a71f1fcf536…`, BZ #18196 — with its
  result-visible band characterization and uncopyrightable-functional
  disposition; huge-band/∞/NaN sweeps; the GCC MPFR probe hazard) was
  folded into R1's `atanf-pinned-provenance.md` (glibc release-tarball
  pin, glibc-LICENSES anchor, Netlib double-original cross-check) so
  the package carries **one** provenance record; references repointed.
  The two records were complementary with no contradictions.

## Gates — re-run independently on merged `main` (Ran, exits direct)

| Gate | Result |
|---|---:|
| `cargo fmt --check` | 0 |
| `cargo clippy --all-targets -- -D warnings` | 0 |
| `cargo test` | 0 |
| `tap_identity --ignored` (item-3 streams: randn 19,784,955 / dstn1 26,402,148 / dstg 30,268 / ranset 2,584) | 0 |
| `par_state_identity --ignored` (fouri2 380,436 / ryf2 275,452 / lintrp 36,889) | 0 |
| `cargo llvm-cov` | 0 |
| `cargo crap --fail-above` (124 functions, none above 30) | 0 |

Cross-check: the full-stream evaluator totals equal the Stage S capture
manifest's per-stream line counts exactly (f2: 17,944 + 17,974 +
16,660 + 16,660 + 53,690 + 53,690 + 86,487 + 117,331 = 380,436; y2:
86,487 + 117,331 + 53,690 + 17,944 = 275,452; li: 11,322 + 15,340 +
7,670 + 2,557 = 36,889) — the ignored gate consumed every captured
record of every non-empty stream, with zero drops.

## Targeted source-vs-port reads (Static, against in-context source)

Per the cross-review structure, R2 targeted the Stage C units (R1 had
independently read the Stage S units):

- **`ryf2`** vs `cligen.f:7545-7657`: slot selection (normal vs
  leap-February 13/14 endpoints and 13 pseudo-midpoint), all six
  ratio branches with their exact operand orders, `mjd = float(jd) −
  0.5`, and the deliberate non-leap `xes(mo,·)` indexing in the
  leap-February path — all faithful. The 5,292 leap-February records
  in the full y2 stream back this empirically.
- **`fouri2`** vs `7387-7423`: `dd` formula, six ordered harmonic
  additions (left-associated, matching the source's single
  expression), `cosf_pinned` throughout — faithful.
- **`lintrp`** vs `7252-7337`: `mod` month arithmetic (wrap at both
  ends verified by hand), per-call `ni(2)` leap reassignment (no
  implicit-SAVE carried), divisor selection (`ni(o_mo)` forward /
  `ni(mo)` backward) — faithful.
- **`intake::sta_dat`** vs the characterized live path
  (`cligen.f:2337-2471`): banner → open/echo → record-1 parse →
  `sta_parms`, with typed `Unsupported`/`InteractiveOnly` deferrals
  exactly where the characterization drew the line.
- **Setup/eval pair consistency**: `ryf1`↔`ryf2` share the slot
  conventions (emv 14, pmt/pmv 13, xes 12) with matching writers and
  readers; `fouri1`↔`fouri2` share the literal `6.2832` and pinned
  cosine. The interp-state surface has a single owner
  (`CinterpState`) on both sides.
- **Banner bytes (Ran)**: the Rust `header` output is a byte-exact
  prefix of the captured Fortran stdout
  (`tap-runs/new-meadows-id-seed0/stdout.log`) — verified directly,
  independent of the self-referential unit test (observation 2).

## R1 disposition review

All four findings verified as really fixed:

1. Parser strictness: ASCII/LF validation and space-only blank
   stripping present in `par/file.rs`; CRLF/tab/non-ASCII regressions
   pinned in tests (read and confirmed).
2. SunPro notice: complete verbatim notice in the module header;
   provenance artifact now consolidated (see merge section).
3. Full-stream digests: complete 64-hex table in `tap-manifest.md`,
   values consistent with the Stage S 16-hex prefixes.
4. SPEC-PAR rev 2: per-record canonical families, typed
   overflow/quantization rejection, fixpoint invariant — a real A4
   contract, and the negative bare-dot form stays flagged for A4
   producer verification.

## Observations (accepted, non-blocking)

1. **`infile` screen echo padding**: gfortran's list-directed
   `write(*,*) infile` pads the `character*256` to full width
   (trailing spaces); the Rust echo writes the bare path. Screen-only
   output, on no acceptance surface (`.cli` bytes, state, and taps are
   the gated surfaces). Accepted as-is; noted so nobody mistakes a
   future stdout diff for a defect.
2. **`header_matches_fortran_banner` is self-referential** (its
   expected string duplicates the implementation literal). The R2
   byte-comparison against the captured Fortran stdout covers the gap
   this session; a future package touching intake should anchor the
   test to a committed stdout capture instead.

## Close-out actions

- Package status → `EXECUTED-COMPLETE`.
- ROADMAP item 4 moved to the work-package record per convention.
- `fdlibm-sunpro-LICENSE.txt` added to the package artifact list.
