# AGENTS.md

Conventions and validation gates for coding agents working in cligen-rs.

## Posture

Read [docs/decisions/0001-source-code-authority-port.md](docs/decisions/0001-source-code-authority-port.md)
before touching generator code. The vendored Fortran is the faithful-mode
specification. Port fidelity questions are answered by reading
`reference/cligen532/cligen.f`, not by intuition or external CLIGEN
documentation.

## Hard rules

The normative elaboration of these rules — naming, symbol glossaries,
attribution headers, Fortran state-translation patterns, numerics
discipline — is
[docs/standards/rust-scientific-coding-standard.md](docs/standards/rust-scientific-coding-standard.md);
read it before writing port code. Summary:

- **Never enable fast-math** or float-reordering optimizations, anywhere.
- **Respect the precision map**: faithful-mode code uses f32 where the
  Fortran uses REAL*4 and f64 exactly where the source declares double
  precision. Do not "upgrade" widths in faithful paths.
- **Transcendentals in faithful paths** go through pinned
  implementations — f64 via the `libm` crate, f32 via
  `cligen::libm_pinned` — never `std` float methods. New faithful-path
  transcendentals are adjudicated empirically against captured
  reference values first (standard §1.3).
- **`reference/cligen532/` is read-only.** Fixes go upstream; refreshes
  update PROVENANCE.md.
- **Extensions declare themselves**: new behavior lives behind a
  generation profile and appears in output provenance. No silent
  divergence from faithful mode.
- Fail closed on malformed input; no inferred defaults for missing
  parameters.

## Workflow

- Work runs as work packages: `docs/work-packages/YYYYMMDD-<slug>/`
  (template in `docs/work-packages/templates/`). Fixture/spec work precedes
  implementation where either applies.
- Specs for any new interface surface go in `docs/specifications/`
  (registry in its README) with or before the implementing code.
- Completed roadmap items move from `docs/ROADMAP.md` to the work-package
  catalog.

## Gates (every package)

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

For any package that adds or changes production functions in `crates/`,
additionally (adopted 2026-07-09, operator decision — present from the
first function so no burndown debt ever accumulates):

```
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
```

No production function above CRAP 30. Because `CRAP = comp²·(1−cov)³ +
comp`, complexity ≥ 30 fails at any coverage — the gate is a complexity
cap plus a coverage requirement that scales with complexity. For faithful
port code this forces decomposition of large Fortran units along the
source's own internal structure, which is numerically safe in Rust
(f32/f64 values cross function boundaries exactly; there is no
excess-precision hazard) and is the decomposition the module map wants
anyway. Do not satisfy the gate by `--allow`-listing a function without a
recorded justification in the package artifacts.

Plus package-specific evidence gates (fixture identity, byte-parity on
`.cli` output, etc.). Evidence from the reference binary is valid only with
recorded build provenance (compiler, flags including `-ffp-contract=off`,
libm, source hash).

## Commit style

Imperative subject line, ≤ 72 chars, body only when the diff doesn't speak
for itself.
