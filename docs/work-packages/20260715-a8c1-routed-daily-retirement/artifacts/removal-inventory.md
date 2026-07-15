# A8c1 final removal inventory

Status: reviewed final disposition  
Dispatch commit: `49a67775d22f0452bbf65f0a1ad35435e0d340f9`  
A8c implementation commit: `fdd35f60241f25663614db46142bfe3683c6ce5f`  
Pre-A8c comparator: `046eba3c8d4508c84522c6dbd7cec4d39f094563`

## Decision

Remove the A8c runtime rather than retain or deprecate it. The release audit
found no tag, GitHub release, or published crate containing the implementation.
The package version remained `0.1.0`, and the research profile was explicitly
non-default and stopped before promotion. No compatibility shim is warranted.

The baseline manifest records 27 current-interface removal surfaces, 148
immutable preserved records, and four intentionally mutable status documents.
Every current-interface source or schema file is either deleted or restored to
the exact pre-A8c comparator bytes. The only custom disposition in the 27-file
set is the specification registry, which keeps a link to the retired historical
contract while removing it from the accepted interface set.

## Deleted A8c-only surfaces

| Path | Classification | Final disposition |
|---|---|---|
| `crates/cligen/src/routed_precip.rs` | model-specific runtime, RNG, and state | deleted |
| `crates/cligen/src/station/document_v2.rs` | model-specific station intake and coefficients | deleted |
| `crates/cligen/tests/a8c_routed_daily.rs` | model-specific integration tests | deleted |
| `docs/specifications/station-document-v2.schema.json` | unshipped A8c input schema | deleted from current interfaces; recoverable from history |

## Shared production surfaces restored exactly

The following files contain independently required faithful or existing
extension behavior. Their A8c branches, arguments, enum values, and adapters
were removed by restoring the complete file to the comparator blob. A byte
comparison, not a semantic approximation, establishes the disposition.

| Path | A8c-specific content removed | Independent content retained |
|---|---|---|
| `crates/cligen/src/daily.rs` | routed backend argument and dispatch | faithful `clgen` / `gen_precip` path |
| `crates/cligen/src/fast_batch.rs` | A8c profile alias | existing faithful/fast-batch mapping |
| `crates/cligen/src/lib.rs` | routed module declaration | existing public modules |
| `crates/cligen/src/modes.rs` | routed state, station route, and generation dispatch | existing run resolution and generation |
| `crates/cligen/src/parquet_output.rs` | A8c model/profile serialization | accepted existing identities |
| `crates/cligen/src/profile.rs` | A8c generation-profile variant and spelling | faithful and fast-batch profiles |
| `crates/cligen/src/provenance.rs` | A8c model, profile, fit, RNG, and pairing branches | revision-1 provenance contract |
| `crates/cligen/src/quality/mod.rs` | routed station-identity override | existing quality computation |
| `crates/cligen/src/quality/report.rs` | A8c model/profile acceptance | existing report validation |
| `crates/cligen/src/runspec.rs` | revision-2 parser and A8c pairing constraints | legacy/revision-1 station resolution |
| `crates/cligen/src/station/mod.rs` | revision-2 module exports | revision-1 station model |
| `crates/cligen/src/typed_output.rs` | A8c profile token | existing typed-row profiles |

No A8c-created generic helper remains. Static reference review showed that
each candidate helper was either inside an A8c-only module or had no current
non-A8c caller after the profile was removed. Future usefulness is not an
independent contract; A9a is free to define a different seam.

## Current schemas and interface specifications restored exactly

The following ten files were restored to comparator bytes so current accepted
combinations no longer admit the A8c station model, profile, fit, route, or RNG
identities:

- `crates/cligen/schemas/provenance-v1.schema.json`;
- `crates/cligen/schemas/quality-report-s2-m3.schema.json`;
- `docs/specifications/provenance-v1.schema.json`;
- `docs/specifications/quality-report-s2-m3.schema.json`;
- `docs/specifications/runspec.schema.json`;
- `docs/specifications/SPEC-GENERATION-PROFILES.md`;
- `docs/specifications/SPEC-PROVENANCE.md`;
- `docs/specifications/SPEC-QUALITY-REPORT.md`;
- `docs/specifications/SPEC-RUNSPEC.md`; and
- `docs/specifications/SPEC-STATION-DOCUMENT.md`.

The documentation/runtime provenance and quality-schema mirrors remain
byte-identical. `docs/specifications/README.md` is intentionally not restored
wholesale: its active rows return to the pre-A8c contracts, and it retains one
explicit `RETIRED` row for the historical A8c specification.

## Preserved historical record

`SPEC-A8C-ROUTED-DAILY.md` remains as a historical contract with no current
producer or consumer. It names the stopped mechanism and points to the exact
implementation commit. Git history retains the deleted schema and source.

All 148 baseline records remain byte-identical, including the complete A7a,
A7b, A8a, A8b, and A8c work packages; the A7a public report and manifest; the
A8a observed-source snapshot; the untouched A9a scaffold; and `.gitattributes`.
The accepted A8c retained-stream archive remains an LFS-managed file with
SHA-256 `ee50d033c6022f9988fc4734cd892d518866dd7df7a35aba24448399ee47edae`.

## Compatibility result

- Faithful and all pre-A8c extension source files equal the comparator.
- Revision-1 modern station documents and legacy `.par` inputs remain the
  current station interfaces.
- The A8c generation profile, station model, fit IDs, route values, revision-2
  intake, extension RNG, output identities, and quality identities are absent.
- No public default, faithful arithmetic, vendored Fortran, output schema
  version, or research result changed.
- A9a receives only the terminal authorization
  `A8C-ROUTED-DAILY-RUNTIME-RETIRED`; it inherits no A8c runtime contract.
