# Gate Results — Stages S + C/R1

Evidence mode: Ran (2026-07-09). All exit codes checked directly (`$?`),
never through a piped tail.

## Gate suite

| Gate | Command | Exit |
|---|---|---:|
| Format | `cargo fmt --check` | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | 0 |
| Tests | `cargo test` (31 passed, 2 ignored) | 0 |
| Item-3 full streams (post-rename sanity) | `cargo test --release --test tap_identity -- --ignored --nocapture` — randn=19,784,955 / dstn1=26,402,148 / dstg=30,268 / ranset=2,584 records, all bit-identical | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` — 117 functions, none above 30 | 0 |

CRAP note: the first run failed with `ParFile::parse` at 34 (complexity
from the per-field `?` branches); it was decomposed along the record-
group structure (`parse_scalars` / `parse_rst_prw` / `parse_wind`),
after which every function passes. No `--allow` list is used.

## Full-matrix par-state snapshot identity (Ran)

`sta_parms_matches_fortran_snapshots_full_matrix` — 4 stations ×
interp {0,1,2,3} = 16 combos; **every** value of each 191-line snapshot
asserted bit-exactly: intake header (`H`), output arguments, `rst`/`prw`
(EQUIVALENCE columns), the 12 monthly arrays (including derived
`cvs`/`cvtx`/`cvtm` and halved `wi`), `wvl` (768 values), `dir` (204),
and the cinterp state — `fouri1`'s `x_bar`/`c`/`t` on the four `-I2`
snapshots and `ryf1`'s `emv`/`pmt`/`pmv`/`xes` on the four `-I3`
snapshots (including the shifted parameter-14 `timpkd` window and the
−9999.0 `xes` sentinels). This is the package's full-matrix identity
gate: the committed snapshots are the complete capture (191 lines per
combo — there is no larger local stream to gate separately for the
Stage S units).

## Round-trip gate (Ran)

`par_roundtrip_fixture_bytes`: `to_bytes(parse(b)) == b` for all four
fixture `.par` files. `par_parse_fails_closed` pins the fail-closed
surface (non-text, record count, corrupt numeric field).

## Transcendental adjudication for `fouri1` (standard §1.3, Ran)

- `sinf_pinned` (glibc/ARM sibling of the existing `cosf_pinned`, same
  tables/reduction) + `cosf_pinned` + candidate `atan`: verified through
  the composition gate above (every `c`/`t` for 4 stations × 14
  parameters × 6 harmonics bit-exact).
- **`libm::atanf` tried first and REJECTED**: 1-ULP divergence at
  captured input bits `0xBE794977` (new-meadows `obmn`, harmonic 4) —
  Rust `0xBE7487C4` vs reference `0xBE7487C3`. Root cause: the `libm`
  crate carries the 5-term reduced float polynomial; glibc 2.39 ships
  the 11-term fdlibm `s_atanf.c`. Not an FMA effect — the host CPU
  (Xeon E5-2697 v2, AVX only) has no FMA, so glibc's ifunc resolves the
  plain SSE2 build.
- `atanf_pinned` (11-term fdlibm transcription, plain f32 ops):
  - C cross-check: the glibc 2.39 `s_atanf.c` source (fetched from
    sourceware, glibc-2.39 tag) compiled locally with `-O2` (no FMA)
    matched the system `atanf` on a **56,253,020-input** sweep of
    `[2^-31, 2^25)` × both signs (step 0x11), 0 mismatches.
  - Rust cross-check: `atanf_pinned` matched system-`atanf` outputs on
    a **3,721,018-pair** sweep of the same domain (step 0x101),
    0 mismatches. (One-off scratch test against a dumped pair file;
    not committed — the committed acceptance is the snapshot
    composition gate.)
  - Transcription note: the fdlibm source's `/* 0x3eaaaaaa */` comment
    on `aT[0]` is stale — the compiled decimal `3.3333334327e-01` is
    `0x3EAAAAAB`, confirmed against the compiled object. The wrong bit
    pattern reproduces the exact 1-ULP failure.
- gfortran's REAL*4 `atan`/`sin`/`cos` lower to libm calls; the tap
  binary and the golden binary link the same system libm (build
  provenance in tap-manifest.md), so system-libm identity is
  reference-runtime identity.

## Precision census confirmation

Grep over `cligen.f:2656-2970` and `7252-7657`: zero
`double`/`dble`/`d0` sites — the package is REAL*4-clean as the
ratified census predicted. No f64 discovery to record.

## Stage C/R1 final gate suite (Ran)

Run after all R1 findings were fixed:

| Gate | Command | Exit |
|---|---|---:|
| Diff hygiene | `git diff --check` | 0 |
| Format | `cargo fmt --check` | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | 0 |
| Tests | `cargo test` — 34 passed, 3 ignored | 0 |
| Item-3 full streams | `cargo test --release --test tap_identity -- --ignored --nocapture` — randn=19,784,955; dstn1=26,402,148; dstg=30,268; ranset=2,584, all bit-identical | 0 |
| Par/monthlies full streams | `cargo test --release --test par_state_identity -- --ignored --nocapture` — fouri2=380,436; ryf2=275,452; lintrp=36,889, all bit-identical | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` — 124 functions, none above 30 | 0 |

The committed ordinary-test evaluator gate replays 1,000 records per
station for each of `fouri2`, `ryf2`, and `lintrp` (12,000 records total).
Each stream reconstructs evaluator state from the same fixture `.par` via
the already snapshot-gated `sta_parms` setup. The full y2 capture includes
5,292 leap-February records; the full li capture includes 8,784 leap-year
records.

Ran: `sha256sum` over all 16 non-empty full-stream files consumed by the
monthlies ignored gate matched the complete digests now recorded in
`tap-manifest.md`.

CRAP correction record: the first Stage C CRAP run failed with
`ParError::fmt` at 72 after the intake errors expanded its match surface.
Direct tests were added for every display/source branch; the final gate
reports 124 functions and zero above 30. No `--allow` list was used.

## Stage R1 review checks

- Static source-vs-port read: `cligen.f:2153-2184`, `2240-2970`, and
  `7252-7657` against the intake, parser/distribution, and monthlies Rust
  modules.
- Static precision grep over package production modules: no f64 site,
  standard float transcendental, fast-math flag, or duplicated common state.
- Ran fail-closed regression checks for non-ASCII, CRLF, tabbed numeric
  fields, missing files, multi-station deferral, and interactive deferral.
- Static upstream notice check: glibc 2.39 tarball/source hashes and Netlib
  origin recorded in `atanf-pinned-provenance.md`; full Sun notice preserved
  in `libm_pinned.rs`.
