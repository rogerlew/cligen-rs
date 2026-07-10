# Interface Specifications

Specifications for every surface another party depends on: file formats,
API seams, producer/consumer boundaries. The rule this directory enforces
(ADR-0001 §5): **no interface whose semantics live only in a binary.**

## Model

One document per surface, `SPEC-<NAME>.md`. Each spec states:

- **Surface** — what is being specified (format, API seam, CLI behavior).
- **Producers / consumers** — who writes it, who reads it, on which side
  of the boundary authority sits.
- **Authority basis** — for ported behavior, the `reference/cligen532/`
  source locations that define it (source-code authority per ADR-0001);
  for extensions, the generation profile that introduces it.
- **Semantics** — fields, units, invariants, failure behavior. Fail-closed
  is the default posture for malformed input.
- **Provenance obligations** — what lineage the surface must carry
  (profile, seed, par lineage, program version) where applicable.

Specs are authored with or before the code that implements them, inside
the owning work package. Keep them as short as correctness allows; this is
not the openWEPP science-contract apparatus and should not grow its
machinery without an ADR.

## Registry

| Spec | Surface | Status |
|---|---|---|
| [SPEC-PAR](SPEC-PAR.md) | Station parameter (`.par`) format + typed par model | active |
| SPEC-CLI-TEXT | `.cli` text output (WEPP-compatible) | planned |
| [SPEC-CLI-DIFF](SPEC-CLI-DIFF.md) | `.cli` field-wise trajectory differ | active |
| SPEC-CLI-PARQUET | Native parquet climate output, provenance columns | planned |
| [SPEC-GENERATION-PROFILES](SPEC-GENERATION-PROFILES.md) | Versioned runspec generator-profile selector + CLI declaration | active (fast-batch spike) |
| [SPEC-FAST-BATCH-V1](SPEC-FAST-BATCH-V1.md) | Proposed fast-batch-v1 runtime contract + quality assessment (ADR-0002) | draft rev 2 |
| [SPEC-QUALITY-REPORT](SPEC-QUALITY-REPORT.md) | Machine-readable per-run climate quality report (the ADR-0002 instrument) | draft rev 1 |
| SPEC-STATION-DB | Typed station-par database, collection manifests, location query, `cligen stations` (crates.io: data outside the crate) | planned (Q2) |
| [SPEC-OBSERVED-INPUT](SPEC-OBSERVED-INPUT.md) | Observed-series input seam (active `.prn` compatibility surface; future f64 parquet extension) | active |
| [SPEC-GENERATOR-CORE](SPEC-GENERATOR-CORE.md) | Generator core: seed/state ownership, faithful-mode shapes | active |
| SPEC-PROVENANCE | Generation-profile + lineage block shared by all outputs | planned |
| [SPEC-RUNSPEC](SPEC-RUNSPEC.md) | `inp.yaml` run specification + `cligen` CLI surface (no legacy interface) | active (contract; implementation with item 8) |
| SPEC-PYO3 | Python API surface | planned |
