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
- **Transcendentals in faithful paths** go through the pinned
  implementations (`libm` crate) — not `std` float methods — so results
  are reproducible across platforms.
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

Plus package-specific evidence gates (fixture identity, byte-parity on
`.cli` output, etc.). Evidence from the reference binary is valid only with
recorded build provenance (compiler, flags including `-ffp-contract=off`,
libm, source hash).

## Commit style

Imperative subject line, ≤ 72 chars, body only when the diff doesn't speak
for itself.
