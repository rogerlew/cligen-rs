# Reference Build + Golden Fixture Harness

Status: `EXECUTED-COMPLETE`
Date: 2026-07-09
Evidence mode: Ran

## Objective

Make "faithful" falsifiable before any port code exists: build the vendored
Fortran with pinned provenance, capture a golden fixture matrix, and build
the trajectory differ that reports first-divergent-day/variable. ROADMAP
item 1; nothing ports before this closes.

## Scope

Included:

- Reference build of `reference/cligen532/` with recorded provenance:
  compiler + version, full flag set (floating-point contraction disabled,
  e.g. `-ffp-contract=off`; no fast-math), libm identity, source hash,
  binary hash/size/mtime.
- Determinism self-gate: two independent builds/runs reproduce
  byte-identical outputs for the full fixture matrix.
- Fixture matrix selection and capture: several stations spanning distinct
  climates × multiple seeds × the live modes (multi-year generation,
  single-storm, observed `-O` including a partial-final-year `.prn` for
  the 5.323 EOF case). Fixture `.par`/`.prn` inputs are vendored with
  provenance (public-domain USDA station parameter files).
- The trajectory differ (first Rust code beyond the stub): field-wise
  `.cli` comparison reporting first divergent day/variable/value-pair;
  zero-self-diff demonstrated on a Fortran re-run.
- Fixture manifest: every golden file keyed to build provenance, inputs,
  seeds, mode, and source hash.

Excluded:

- Any generator port code.
- Interior-trajectory taps (deviate-stream captures): **design decision in
  Phase A** — either a recorded tap patch under this package (never
  modifying `reference/`) or deferral to the RNG port package, which needs
  taps for its bit-identity gate. Decide and record; do not silently skip.
- `.cli.parquet`, provenance profiles, and all A-item work.

## Authority

- ADR-0001 §4 (fixture provenance rules) and the hazards in
  [docs/port/fortran-decomposition.md](../../port/fortran-decomposition.md)
  §5 (FMA contraction, libm pinning, QC-coupled trajectories — fixture
  seeds must exercise the QC regeneration path).

## Plan

1. **Phase A — build + decisions.** Reference build with provenance;
   record the libm-pinning decision (which libm the reference links; the
   Rust side pins the `libm` crate) and the interior-taps decision.
   **Warning (pre-dispatch finding, 2026-07-09):** the vendored
   `reference/cligen532/makefile` optimized target is **disqualified for
   golden generation** — its flags include `-fno-protect-parens`
   (explicitly permits floating-point expression reordering) and the
   fast-math family (`-ffinite-math-only`, `-fno-trapping-math`,
   `-fno-signaling-nans`, `-fno-math-errno`). The fixture build defines
   its own pinned profile (deterministic: no fast-math family,
   `-ffp-contract=off`, protect-parens default on; optimization level is
   a Phase A decision to record). The makefile stays untouched in
   `reference/` as provenance of how production binaries were built —
   which also means the vendored production `wepp.cli` cross-references
   may diverge from the pinned build for flag reasons alone; that
   divergence is signal, not alarm. Toolchain on this host: gfortran
   14.2.0 (linuxbrew).
2. **Phase B — fixture matrix.** The station set is selected and vendored
   (operator, 2026-07-09): four production cases in
   [`fixtures/`](../../../fixtures/README.md) — Idaho 44.97°N stochastic,
   California 34.23°N observed (DAYMET), Australia 30.58°S stochastic,
   Utah 39.83°N observed with end-of-record sentinel tail (gridMET).
   Remaining Phase B work: reproduce each case's invocation from the
   vendored `cligen_wepp.log`/`wepp.inp`; add seed variants beyond each
   run's production seed; craft the hard-truncated `.prn` variant pinning
   the exact 5.323 EOF shape; verify the QC-regeneration path is
   exercised (add a stressing seed if not); capture goldens; write the
   manifest. Bonus Phase A instrument: diff the pinned reference build's
   output against each vendored production `wepp.cli` (same source
   version, unknown build) to measure build/libm sensitivity.
3. **Phase C — differ.** Implement `.cli` differ in `crates/cligen`
   (or a `tools/` binary — decide by what the port packages will reuse);
   zero-self-diff gate; a deliberate one-ULP perturbation test proving the
   differ localizes.
4. **Phase D — close.** Gates, review pass, catalog/roadmap updates.

## Gates

- `cargo fmt --check`; `cargo clippy --all-targets -- -D warnings`;
  `cargo test`.
- CRAP ≤ 30 on production functions (`cargo llvm-cov` + `cargo crap
  --fail-above`, per AGENTS.md) — the differ is the first code this
  gate measures.
- Reference-build provenance recorded (ADR-0001 §4).
- Byte-identical determinism re-run across the full matrix.
- Differ zero-self-diff + perturbation-localization demonstration.

## Exit criteria

`EXECUTED-COMPLETE`: reproducible fixture set with manifest + provenance;
differ proven; taps decision recorded. Legitimate holds: reference build
not reproducible (name the nondeterminism source); required station inputs
lack public provenance.

## Artifacts

- `artifacts/build-provenance.md`
- `artifacts/fixture-manifest.md`
- `artifacts/gate-results.md`
- `artifacts/review-*.md`
