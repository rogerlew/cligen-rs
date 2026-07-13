# A1 Design Decisions

Status: accepted for package execution — 2026-07-12

1. **A1 is parametric output only.** Breakpoint import/storage and the
   deprecated single/design-storm Parquet companion do not enter output schema
   v1. Legacy storm `.cli` generation remains unchanged.
2. **Legacy text remains required.** `output.cli` remains required;
   `output.parquet` is an optional sibling ending in `.cli.parquet`. This is a
   compatible migration step and keeps the existing quality-report anchor.
3. **One pre-format stream.** Faithful `DailyRow` remains f32 and feeds the
   legacy renderer. Public `ClimateRowV1` widens those exact values to f64 at
   the output boundary. Parquet is never produced by parsing quantized text.
4. **FLOAT64, not DECIMAL.** Every faithful f32 value widens exactly, including
   negative zero, and the schema remains usable by later native-f64 output.
5. **Versions are independent.** The emitted bundle separately names the
   station-input schema, station model, generation profile, output schema,
   provenance schema, quality-report envelope, and metric vector; the latter
   two remain quality-report top-level fields rather than provenance fields.
6. **Fit unknown stays unknown.** Current station files do not identify a
   fitting method/dataset. Provenance requires `fit.status = unreported` and a
   syntax-independent `parameter_set_sha256`; it does not invent fit lineage.
7. **Portable identity excludes resolved paths.** Canonical effective runspec
   provenance contains resolved defaults, lexical paths, and exact input
   hashes. Resolved filesystem paths remain runtime context and are not
   serialized. This A1 ruling amends SPEC-RUNSPEC revision 6's contrary
   wording and avoids leaking/cache-binding host paths.
8. **Text provenance is a mandatory companion.** Faithful `.cli` cannot embed
   structured metadata without losing byte parity, and `output.quality` may be
   false. Every text output therefore gets `<output.cli>.provenance.json`;
   Parquet embeds the same schema with its own artifact descriptor.
9. **Quality versions do not conflate.** A new
   `quality_report_schema_version` identifies the envelope change; unchanged
   metrics remain `metrics_version = 2` so A5a retains ownership of metrics v3.
10. **Canonical profile IDs use runspec spelling.** Provenance uses
    `faithful_5_32_3` / `fast_batch_v0`. Hyphenated text is only a legacy
    command-marker spelling.
11. **Calendar and coverage are explicit.** A1 Parquet accepts continuous and
    observed runs under `proleptic_gregorian`; observed early EOF/sentinel is
    `observed_source_end`, distinct from requested-year completion.
12. **Writer and canonicalization pins.** Exact pins are `parquet`, `arrow-array`, and
   `arrow-schema` 59.1.0 (Apache-2.0, MSRV 1.85; workspace rustc 1.95), with
   Parquet 2.0, ZSTD level 3, row groups of at most 65,536 rows, a fixed `created_by`,
   and ordered metadata. Logical schema/value/metadata identity is normative;
   cross-library raw-byte identity is not. Repeat bytes are a diagnostic gate
   under the exact pin. `serde_json` 1.0.150 and literal canonical-hash vectors
   pin public run/parameter identities.
13. **Publication is per artifact, not a claimed transaction.** Parquet is
   closed successfully in a same-directory staging file before rename. The
   multi-file output bundle cannot be atomically published as one filesystem
   operation. A canonical-destination lock, alias/staging preflight, atomic
   companion replacement, and the documented text → provenance → Parquet →
   quality order avoid an overclaim.
14. **Text provenance binds content.** A text artifact carries its exact byte
   SHA-256 and a verifier API; Parquet uses null because a file cannot embed
   its own digest. Path-only station selection declares collection lineage
   unreported rather than inferring a station release from cache layout.
