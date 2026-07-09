# Rust Scientific Coding Standard — cligen-rs

Status: Active — normative for all Rust code in this repository
Lineage: adapted from openWEPP's `rust-scientific-coding-standard.md` for
the source-code-authority port posture (ADR-0001); self-contained — no
cross-repo reading required. `AGENTS.md` summarizes the hard rules; this
document is the normative elaboration.

## 1. Non-negotiable rules

1. **Faithful mode replicates the source precision map.** f32 where the
   Fortran is REAL*4, f64 exactly at the source's `double precision` /
   `dble()` sites, promotion order preserved. Native mode is uniform f64.
   No third mode without an ADR.
2. **No fast-math, ever.** No float-reordering compiler flags, no
   `fadd_fast`-class intrinsics, no algebraic "simplifications" of source
   expressions. Parenthesization and evaluation order follow the Fortran.
3. **Transcendentals in faithful paths go through pinned
   implementations**, never `std` float methods, so results are
   platform-independent. Concretely (adjudicated by fixture evidence,
   2026-07-09): f64 functions (`pow`, `exp`) use the `libm` crate,
   which matched the reference runtime bit-for-bit across the full tap
   capture; f32 functions (`logf`, `cosf`) use `cligen::libm_pinned` —
   transcriptions of the glibc/ARM algorithms — because the `libm`
   crate's f32 versions diverge from the reference runtime on ~7.5% of
   captured inputs. `sqrtf` is IEEE-exact and needs no pinning. A new
   transcendental entering a faithful path must be adjudicated the same
   way: empirically, against captured reference values, before use.
4. **`#![forbid(unsafe_code)]`** in the `cligen` crate. FFI (PyO3) lives
   in a future separate binding crate with its own rules.
5. **Fortran-style short symbols are allowed — with a glossary.** Inside
   port modules, keep the source's names (`ida`, `nsim`, `r`, `tmxg`) so
   code reads against `cligen.f` line-for-line. Every port module carries
   a module-level symbol glossary with meaning and units (§3).
6. **Every ported module carries an attribution header** (§4).
7. **No unresolved stubs on shipped paths** (`todo!`, `unimplemented!`,
   placeholder panics). Intentionally-unavailable behavior returns a
   typed error. Malformed input fails closed; no inferred defaults.
8. **Extensions declare themselves**: behavior not present in the Fortran
   lives behind a versioned generation profile and appears in output
   provenance. No silent divergence from faithful mode.
9. **`reference/cligen532/` is read-only.** Fixes go upstream and arrive
   as a provenance-documented refresh.

## 2. Naming

- Public API surfaces (crate root, `par`, `output`, `profile`) use
  ordinary Rust naming — spelled-out, documented, unit-suffixed where a
  bare number would be ambiguous (`target_dx_m` style).
- Port-module interiors keep source symbols (rule 5). The boundary is the
  module's public functions: short symbols do not escape into public
  signatures.

## 3. Module symbol glossary (required in every port module)

At the top of each port module, after the attribution header:

```rust
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `ida`  | `ida`   | day index within simulation window | day |
//! | `r`    | `r(ida)`| daily precipitation depth | inches |
//! | `nsim` | `nsim`  | 1 = generate precip (observed value missing) | flag |
```

Units are the *source's* units (CLIGEN is internally imperial in places);
unit conversion happens only at declared boundaries, and the glossary is
where a reviewer finds out which side of the boundary a symbol lives on.

## 4. Attribution header (required in every port module)

```rust
//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:<start>-<end> (<unit names>)
//! Precision-Map: REAL*4 except <sites, or "uniform">
//! Faithful-Acceptance: <fixture gate that pins this module>
```

`Precision-Map` and `Faithful-Acceptance` are the two fields a future
debugger needs first; keep them current when the module changes.

## 5. Fortran state translation patterns

The source's state constructs map to Rust one way, uniformly:

- **Common block → one owning struct**, named for its include file
  (`Crandom3State` for `crandom3.inc`). The struct is the single home of
  that storage; units that shared the block take `&mut` to it.
- **Aliased views** (e.g. `crandom3.inc`'s `vvx/v2x/.../zx` columns onto
  `ranary`; `sta_parms`' scalar aliases onto common arrays) become
  accessor methods on the owning struct — never duplicated fields, never
  a second binding to the same storage.
- **`SAVE` locals → explicit fields** on the unit's state struct (e.g.
  `dstg`'s `array, iarrct`; `ranset`'s `ell, last_r`). No `static`, no
  `static mut`, no lazy globals, no interior mutability for generator
  state. All state flows through parameters.
- **`block data` → constructors**: initialization values move to
  `new()`/`Default` impls with the source lines cited in a comment.
- **`ENTRY` points → separate functions** sharing the unit's state
  struct.
- **Integer arithmetic replicates exactly** (the RNG is pure integer
  work); Fortran `int()` truncation maps to Rust `as` truncation-toward-
  zero — confirm range safety at the site or use a checked conversion
  with a fail-closed error.
- **Float literals are copied verbatim** from the source (`.001`, `5.795`,
  `9.210`) with the source line cited where the constant has history.
- **Clippy vs. faithful shape**: lints that would rewrite source shape
  or source literals (`approx_constant` on a source constant that
  resembles π/TAU, `manual_clamp` on sequential range checks,
  `assign_op_pattern` on `k(2)=3*k(2)`-style updates) get a targeted
  `#[allow]` with a comment citing the source line — never a global
  allow, and never the "fix" clippy suggests, which would silently
  diverge from the specification.

## 6. Numerics discipline

- Each port package audits its units' precision sites before
  implementation and records the map in the attribution header.
- Mixed-precision expressions replicate the Fortran's promotion points:
  widen (`f32 as f64`) exactly where the source promotes, round back
  exactly where it demotes. Do not hoist or defer conversions.
- Comparisons that gate stochastic behavior (`if (rn < p)`-class) are
  bit-sensitive; they get direct fixture coverage, not just end-to-end
  trajectory coverage.
- A faithful-mode module is done when the trajectory differ shows
  identity against its fixture taps — not when its output "looks right."

## 7. Tests, coverage, and documentation

- Tests live in separate files (unit tests beside the module only when
  they need private access; integration and fixture tests under
  `tests/`). Test names cite the source unit they pin
  (`randn_matches_fortran_tap_seeds`).
- Every port module ships with fixture-anchored tests before it is called
  from any other module.
- Public API rustdoc includes `# Units`, `# Numerics`, and `# Errors`
  sections where applicable.
- **CRAP ≤ 30 for every production function** (adopted 2026-07-09),
  gated per package via `cargo llvm-cov` + `cargo crap --fail-above`
  (invocation in `AGENTS.md`). The bound doubles as a complexity cap
  (~29) — large Fortran units decompose along source-internal structure
  rather than porting as single functions; the fixture-anchored tests
  this standard already mandates supply the coverage side. Adopted at
  repository birth precisely so no burndown inventory can accumulate.

## 8. What this standard deliberately omits

Line-count governance, science-contract linkage machinery, comparator
metadata, and the unsafe/interop policy apparatus of the openWEPP
standard — per ADR-0001's lean-DNA decision. If the project grows into
needing one of these, it arrives by ADR, not by drift.
