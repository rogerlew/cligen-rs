# ADR-0001: Source-Code-Authority Port of CLIGEN 5.32.x

Status: Accepted
Date: 2026-07-09
Deciders: Roger Lew (operator); drafted by Claude Code

## Context

CLIGEN 5.32.x is the stochastic weather generator of the WEPP model family:
~7,700 lines of Fortran 77 (`cligen.f` plus 13 common-block includes),
recoded by C. R. Meyer circa 1999–2004 to the WEPP F-77 coding conventions,
with built-in distributional self-tests (chi-square, Kolmogorov–Smirnov,
mean/variance confidence checks). It is public domain, upstream-maintained
at github.com/jfrankenberger/cligen5, and already patched by this project's
operator (5.323 `day_gen` end-of-file fix, 2025-09).

The motivating goal is not replacement for its own sake but **augmentation**:
modified storm duration/intensity derivation, NOAA design-storm curves,
float64 parquet observed input replacing quantized `.prn`, leap-year
imputation, single-pass variable substitution, post-event scaling, parquet
output with provenance, par-database and par-mutation tooling, and a PyO3
surface. None of these are reachable through a wrapper around the Fortran
binary: they live inside the generator. A wrapper-first staging was
considered and rejected by the operator for exactly that reason.

The surrounding ecosystem also supplies a cautionary tale. The prj2wepp
translator (WEPP interface lineage) survived for two decades as a binary
whose true input envelope its heaviest user had to characterize by
experiment (dailyerosion/dep#158), because its semantics lived only in
un-shared source and a stale error message. cligen-rs must never become
that artifact.

## Decision

1. **Port CLIGEN to Rust with the Fortran source as the specification.**
   The pinned source vendored at `reference/cligen532/` is the authority
   for what faithful mode computes. Where the source and any external
   description disagree, the source wins. This is the opposite of
   openWEPP's legacy posture (comparator-as-flag, ADR-0017 there), and
   deliberately so: openWEPP's legacy claims to model nature and can be
   wrong about it; CLIGEN *defines* a fitted stochastic model whose station
   parameters were fitted to this machinery. There is no external truth to
   re-derive it from. (openWEPP's ADR-0024 ratified this epistemology for
   empirical submodels; this ADR applies it to an entire binary.)

2. **Dual execution modes with a declared equivalence class each:**
   - **Faithful mode** replicates the Fortran's *precision map* — REAL*4
     arithmetic with the source's REAL*8 islands (e.g. `DSTG`'s
     `double precision fu, xx`) exactly where the source has them.
     Acceptance is stochastic-trajectory identity against golden fixtures
     from the reference build. A generic float-width core cannot express
     this mode; the heterogeneous precision map is part of the spec.
   - **Native mode** is uniform f64 and is the evolution path (and the
     float64 parquet pipeline target). Its divergence from faithful mode
     is measured once, characterized, and documented — never discovered
     downstream.

3. **All extensions are labeled divergences behind versioned generation
   profiles.** Every output (`.cli` text or `.cli.parquet`) declares the
   profile that produced it (e.g. `faithful-5.32.3`, later
   `atlas14-storm-v1`), plus seed, par lineage, and program version.
   Consumers bind to profiles, not to "whatever the binary does."

4. **Reference-build provenance is a hard requirement for fixtures.**
   Golden fixtures are generated only from a Fortran build with recorded
   compiler, flags (floating-point contraction disabled), libm identity,
   and source hash. Faithful-mode transcendentals route through pinned
   implementations (the Rust `libm` crate — musl lineage — unless fixture
   evidence forces another choice).

5. **Interface semantics are written down.** File formats, API seams, and
   producer/consumer surfaces get specifications in `docs/specifications/`
   before or with the code that implements them. The failure mode this
   forecloses: semantics that live only in a binary and an error string.

## Inherited DNA (from openWEPP), kept deliberately lean

Kept:

- **Work-package execution record** (`docs/work-packages/`): one package
  per unit of work, package.md + artifacts, honest terminal states
  (complete vs held-with-named-blocker). Single review pass; the dual
  review/dual verification apparatus is not imported.
- **Truthfulness discipline**: evidence labeled Ran vs Static; verbs match
  what was actually executed; delegated runs attributed.
- **Forward-only roadmap** (`docs/ROADMAP.md`): completed work moves to
  the work-package record.
- **ADRs** (this directory).
- **Toolchain pinning and gates**: `rust-toolchain.toml`; `cargo fmt
  --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`.
- **Exact binary provenance for evidence runs** (the reference build rule
  above).

Explicitly not imported (add later only if the project grows into them):

- The science-contract profile machinery (SC-* templates, binding-exposure
  lint, unit registries, comparator-tier metadata).
- Dual independent review + dual verification per package.
- Line-count governance, cargo-deny/nextest gates.

## Consequences

- The port must begin with the fixture harness and a precision-map audit,
  not with generator code; without golden fixtures, "faithful" is
  unfalsifiable.
- One-ULP differences in transcendental functions can bifurcate an entire
  stochastic trajectory at occurrence branches (`if (rn < p)`), so
  fixture comparison must report first-divergent-day/variable rather than
  aggregate statistics — aggregate tests cannot distinguish a seed-stream
  transcription error from legitimate noise.
- Meyer's built-in QC subroutines (`chitst`, `ks_tst`, `conflm`, `confls`)
  port along with the generator and serve as a second, distributional
  validation instrument — but they never substitute for trajectory
  identity in faithful mode.
- The Fortran reference stays runnable from `reference/cligen532/` for the
  life of the project; retiring it requires a superseding ADR.
