# cligen-rs

A Rust implementation of CLIGEN, the stochastic weather generator of the
WEPP model family — executed as a **source-code-authority port** of CLIGEN
5.32.x, then extended.

CLIGEN generates daily (and event/breakpoint) climate series — precipitation
occurrence and depth, storm duration and peak intensity, temperatures, solar
radiation, dew point, wind — from fitted station parameter (`.par`) files.
Its outputs drive WEPP, openWEPP, and the wepppy/WEPPcloud stack.

## Why this project exists

CLIGEN is a fitted statistical machine, not a physics model: the thousands
of station `.par` files were fitted to *this generator's* distributional
machinery, and there is no external physical truth to re-derive it from.
The Fortran source therefore *is* the definition of the model — and owning
that definition in Rust is what makes meaningful augmentation possible:

- modified storm duration / peak-intensity derivation from station
  coefficients and event depth
- NOAA (Atlas 14 class) design-storm curve representation
- float64 parquet observed-series input replacing quantized `.prn` files
- automated leap-year imputation
- single-pass variable substitution (no flatfile → wepppyo3 → flatfile
  round-trips)
- post-event month-by-month and global scaling
- native `.cli.parquet` output with full generation provenance
- typed station-par database management and provenance-stamped par
  mutation utilities
- a PyO3 API surface for wepppy

The governing decision — including the faithful/native dual-mode design and
what "faithful" means — is [ADR-0001](docs/decisions/0001-source-code-authority-port.md).

## Posture, in two sentences

The pinned Fortran source in [`reference/cligen532/`](reference/cligen532/)
is the specification for **faithful mode**; acceptance is trajectory
identity against golden fixtures generated from a provenance-pinned
reference build. Divergence from the Fortran is never accidental: it is a
labeled extension carried in a versioned **generation profile** that every
output file declares.

This is deliberately a different posture from openWEPP's (where legacy
source is a flag, not an authority): openWEPP models nature and can be
wrong about it; CLIGEN defines a stochastic model, and the definition
lives in the source.

## Repository layout

| Path | Purpose |
|---|---|
| `crates/cligen/` | The library crate (generator core, par model, I/O) |
| `reference/cligen532/` | Pinned public-domain CLIGEN 5.32.3 Fortran source — the faithful-mode specification |
| `docs/decisions/` | Architecture decision records |
| `docs/standards/` | Coding standards (the Rust scientific/port standard) |
| `docs/specifications/` | Interface specifications: file formats, API seams, producer/consumer surfaces |
| `docs/port/` | Fortran decomposition analysis and port plan |
| `docs/work-packages/` | Execution record — one package per unit of work |
| `docs/ROADMAP.md` | Forward-only work queue |

## Status

Pre-implementation. The scaffold, posture decision, decomposition
first-pass, and roadmap exist; no generator code has been ported yet.

## Provenance and licensing

CLIGEN is a USDA-ARS work in the public domain; the pinned copy and its
lineage are documented in
[`reference/cligen532/PROVENANCE.md`](reference/cligen532/PROVENANCE.md).
The Rust code is licensed under [Apache-2.0](LICENSE).
