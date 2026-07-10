# Stage R1 Review — Codex

Reviewer: Codex
Date: 2026-07-09
Evidence mode: Static source-to-port review + Ran gates and capture checks
Status: `R1-COMPLETE` — one Low finding accepted and fixed; no open R1
findings

Stage R2 remains assigned to Claude Code. This review does not close the
package.

## Scope and method

Reviewed the complete storm-machinery package, including the Stage S spine
and Stage C completion, against the vendored authority:

- `cligen.f:2188-2236` (`timepk`), including draw selection, cumulative
  search, interpolation expression order, and `timpkd(0)`;
- `cligen.f:3105-3176`, including the F-to-C seam, wet-day normalization,
  both `alphb` calls, the duration and intensity clamps, and option-4/7
  override order;
- `cligen.f:3325-3493` (`sing_stm`), plus `command6.inc` defaults and the
  explicit prompt/file-management deferrals;
- main/block-data tables at `cligen.f:602,1064-1066`, the `Cbk4State`
  translation, the sd/tp tap schema and all 24 local captures;
- the committed sample tests, full-matrix ignored replay, and formal quality
  gates.

## Finding and disposition

1. **Low — `/bk4/::mo` documentation retained a stale single-writer
   claim.** After the typed intake landed, `cbk4.rs` still described
   `day_gen`'s `jlt` decomposition as the single production writer, while
   source `sing_stm` writes `mo` for options 4 and 7 at
   `cligen.f:3385`. **Accepted and fixed:** the state glossary now names
   both writer paths. This was a documentation/ownership defect only; the
   typed port already performed the required `Cbk4State.mo` write and its
   fixture test asserted it.

No numeric, precision-map, state-translation, or evidence-alignment finding
remains open. No file under `reference/cligen532/` was modified.

## Review conclusions

### Transcription fidelity

- `timepk` preserves the `iopt = 6` fresh `randn(k10)` draw and the batch
  `zx(dax)` path, increments `i` before testing, caps the search at interval
  12, and evaluates the source's REAL*4 `0.08333*i - ratio*0.08333` order.
  `sta_parms` explicitly installs `timpkd[0] = 0.0`; the interpolation reads
  that sentinel when the search lands in interval 1.
- `wet_day_duration` normalizes non-positive rain to zero before returning
  zero duration. Positive rain calls `alphb`, uses the live 3.99
  coefficient, and clamps duration to 24 hours.
- `storm_block` preserves the source sequence: option-4/7 duration zeroing;
  wet/dry split; second `alphb`; `timepk`; 0.99 `tpr` clamp; `r5p` ceiling;
  Celsius mean-temperature and 1.01 `xmav` floors; then the option-specific
  override and its second floor. The transient infinity before the 4/7
  override remains deliberately unguarded.
- The replay performs `tmxg`, `tmng`, and `tdp` Fahrenheit-to-Celsius
  conversion between `clgen` and the storm chain, matching
  `cligen.f:3110-3112`; the mean-temperature floor therefore consumes
  Celsius values.
- Typed `sing_stm` intake retains the exact option-6 `-1` default checks,
  assigns `iyear` from the resulting `ibyear`, writes option-4/7 `mo`, and
  returns typed errors for source paths that would prompt or manage Fortran
  units. No prompt loop or filesystem policy entered the library.

### Precision and state translation

- All storm numeric values, literals, tables, and intermediates are f32,
  matching source REAL*4. The only transcendental is `alog`, routed through
  `logf_pinned` at both live sites; no standard float transcendental, f64
  widening, reassociation flag, or fast-math configuration was introduced.
- `Cbk4State` owns `dtp` and the source-initialized but unread `dmxi` once.
  `TYMAX` remains a cited main-program constant in `storm.rs`, not a common
  block field. RNG and deviate SAVE translations remain explicit,
  caller-owned state.

### Test and evidence alignment

- The ordinary suite replays the 10 committed sd/tp prefixes and directly
  tests the typed intake against `single-storm.inp`. Exact option-6 defaults,
  valid continuous modes, prompt/file deferrals, and unsupported modes are
  covered.
- Option 7 remains unreachable from the fixture matrix. Its override
  arithmetic and 1.01 floor are covered by tests explicitly labeled as
  constructed source-formula vectors; they are not represented as reference
  goldens.
- The ignored release gate enumerates all 24 manifest cases and asserts all
  ten seed streams per day. Ran result: 189,207 days and 36,065 `timepk`
  calls bit-identical, with full tp-record exhaustion.
- Direct line-count and SHA-256 verification matched all 48 sd/tp manifest
  entries. Format, clippy, ordinary tests, all four ignored release suites,
  coverage, and CRAP commands exited 0 directly; CRAP analyzed 148 functions
  with none above 30.

## R1 disposition

Stage C and R1 are ready for the independently assigned Stage R2 review.
The unresolved evidence limitation is narrowly stated: no committed
reference run exercises option 7, so the source-transcribed override has
constructed arithmetic coverage but no binary golden. R1 does not invent
one, does not widen acceptance, and leaves the package open.
