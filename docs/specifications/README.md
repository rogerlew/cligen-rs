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
| [SPEC-STATION-DOCUMENT](SPEC-STATION-DOCUMENT.md) | Modern fixed-monthly station JSON + shared typed model ([JSON Schema](station-document.schema.json)) | active (rev 1; A4a) |
| [SPEC-A8C-ROUTED-DAILY](SPEC-A8C-ROUTED-DAILY.md) | Historical A8c station route, integrated daily precipitation mechanism, fallback, RNG, and pilot boundary | **RETIRED** (rev 1; runtime and accepted schemas removed by A8c1) |
| [SPEC-A9-RESEARCH-FOUNDATION](SPEC-A9-RESEARCH-FOUNDATION.md) | Research-only successor fit, objective, data-role, RNG, calibration, and confirmation contracts ([fit schema](a9-fit-artifact-v1.schema.json), [objective schema](a9-objective-registry-v1.schema.json), [data-role schema](a9-data-role-manifest-v1.schema.json)) | research-only (rev 1; A9a; no accepted runtime identifier) |
| [SPEC-A10-CORPUS](SPEC-A10-CORPUS.md) | Research-only normalized corpus, roles, shards, and offline transfer manifests | research-only (rev 1; A10M1; no accepted runtime identifier) |
| [SPEC-A10-NEURAL-CANDIDATE](SPEC-A10-NEURAL-CANDIDATE.md) | Research-only A10 model, fit/checkpoint, and nested generated-stream contracts ([model](a10-model-v1.schema.json), [checkpoint](a10-fit-checkpoint-v1.schema.json), [stream](a10-generated-stream-v1.schema.json)) | research-only (rev 1; A10M3; no accepted runtime identifier) |
| [SPEC-A10-SELECTOR-BENCHMARK](SPEC-A10-SELECTOR-BENCHMARK.md) | Research-only paired B0/B1 applicability, CPU generation benchmark, runtime boundaries, and deterministic selector ([evidence schema](a10-selector-evidence-v1.schema.json)) | research-only (rev 1; A10M3; no selected candidate) |
| [SPEC-LEMHI-AGENT-TOOLKIT](SPEC-LEMHI-AGENT-TOOLKIT.md) | Agent workflow lifecycle, provider contracts, receipts, safety boundaries, and cleanup for Lemhi | authoritative (rev 1; foundation implemented) |
| [SPEC-LEMHI-CANONICAL-CONFIGURATION](SPEC-LEMHI-CANONICAL-CONFIGURATION.md) | Versioned canonical runtime, framework, scheduler, storage, isolation, evidence, and invalidation contract for A10 Lemhi GPU agents | authoritative (rev 1; `lemhi-a10-py311-l40-v1`) |
| [SPEC-CLI-TEXT](SPEC-CLI-TEXT.md) | Frozen `.cli` text output + mandatory provenance companion | active (rev 1; A1) |
| [SPEC-CLI-DIFF](SPEC-CLI-DIFF.md) | `.cli` field-wise trajectory differ | active |
| [SPEC-CLI-PARQUET](SPEC-CLI-PARQUET.md) | Parametric typed row stream + `.cli.parquet` output ([field manifest](cli-parquet-v1.fields.json)) | active (rev 1; A1) |
| [SPEC-GENERATION-PROFILES](SPEC-GENERATION-PROFILES.md) | Versioned generator-profile selector + `qc_filter` conditioning knob + CLI declaration | active (rev 4; A1/Q3) |
| [SPEC-FAST-BATCH-V1](SPEC-FAST-BATCH-V1.md) | Fast-batch-v1 runtime contract + quality assessment (design study of record) | **RETIRED** (Q4 adjudication ratified 2026-07-10; v0 stays a closed spike) |
| [SPEC-QUALITY-REPORT](SPEC-QUALITY-REPORT.md) | Machine-readable per-run climate quality report (the ADR-0002 instrument; [envelope-2/metrics-3 schema](quality-report-s2-m3.schema.json), [frozen envelope-2/metrics-2 schema](quality-report-v2.schema.json), [preserved v1 schema](quality-report-v1.schema.json), [latest alias](quality-report.schema.json)) | active (rev 8, envelope 2 / metrics 3 — A5a) |
| [SPEC-OBSERVED-TARGET-CORPUS](SPEC-OBSERVED-TARGET-CORPUS.md) | Independently versioned, hash-pinned observed targets for A5 candidate fitting and held-out evaluation | active (rev 1 — A5a; [v1 schema](observed-target-corpus-v1.schema.json)) |
| [SPEC-A5-EVALUATION](SPEC-A5-EVALUATION.md) | Fixed A5 candidate matrix, aggregation hierarchy, promotion gates, executable observed-target bootstrap, experimental A5b lineage boundary, and separate downstream-WEPP response protocol ([metric-cell manifest v1](a5-climate-gate-metrics-v1.json), [manifest schema](a5-climate-gate-metrics-v1.schema.json), [WEPP response v1 schema](a5-wepp-response-v1.schema.json)) | active (rev 3 — A5b prospective amendment) |
| [SPEC-A5B-CANDIDATES](SPEC-A5B-CANDIDATES.md) | Experimental A5b coefficient-augmented station bundles, seven fixed candidate models, independent overlay plans, run records, and sealed evidence manifest ([station schema](a5b-augmented-station-v1.schema.json), [plan schema](a5b-overlay-plan-v1.schema.json), [run-record schema](a5b-run-record-v1.schema.json), [evidence schema](a5b-candidate-evidence-v1.schema.json)) | active (rev 1 — A5b; not a promoted profile) |
| [SPEC-A5E0-PILOT](SPEC-A5E0-PILOT.md) | Experimental direct annual-state pilot: analytic coefficient fit, isolated generator seam, deterministic extension/faithful RNG partitioning, and sealed campaign evidence ([coefficient schema](a5e0-coefficients-v1.schema.json), [campaign schema](a5e0-campaign-evidence-v1.schema.json)) | retired (rev 1 — exploratory execution held at prospective boundary; not promoted; runtime retired by A5f1, historical specification retained) |
| [SPEC-STATION-DB](SPEC-STATION-DB.md) | Station collections, hash-pinned manifests, local cache, `cligen stations` (data outside the crate) | active (rev 2; A4a local converter) |
| [SPEC-OBSERVED-INPUT](SPEC-OBSERVED-INPUT.md) | Observed-series input seam (active `.prn` compatibility surface; future f64 parquet extension) | active |
| [SPEC-GENERATOR-CORE](SPEC-GENERATOR-CORE.md) | Generator core: seed/state ownership, faithful-mode shapes | active |
| [SPEC-FAITHFUL-GENERATION](SPEC-FAITHFUL-GENERATION.md) | End-to-end continuous stochastic + hybrid observed climate-generation behavior | active |
| [SPEC-PROVENANCE](SPEC-PROVENANCE.md) | Independently versioned generated-artifact lineage shared by text, Parquet, and quality output ([v1 schema](provenance-v1.schema.json), [latest alias](provenance.schema.json)) | active (rev 1; A1) |
| [SPEC-RUNSPEC](SPEC-RUNSPEC.md) | `inp.yaml` run specification + `cligen` CLI surface (no legacy interface) | active (rev 7: A1 output/provenance) |
| SPEC-PYO3 | Python API surface | planned |
