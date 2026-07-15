# A8c1 scaffold-time retirement surface inventory

Status: static planning inventory; not the execution baseline manifest  
Source inspected: `main` at
`fdd35f60241f25663614db46142bfe3683c6ce5f`  
Method: repository symbol search plus A8c specification/package review

## Disposition classes

- **Remove candidate:** presumptively exists only for the stopped A8c model.
- **Review shared seam:** touched by A8c but may contain independently used
  behavior; execution must prove the final disposition.
- **Preserve evidence:** immutable accepted scientific record; never rewritten
  to make current `main` execute the historical producer.
- **Historical comparator:** used to restore/check source shape and retained in
  Git, not copied blindly over later unrelated work.

## Primary candidate-specific sources

| Surface | Current role | Presumptive disposition |
|---|---|---|
| `crates/cligen/src/routed_precip.rs` | A8c occurrence/amount state and extension RNG | Remove candidate |
| `crates/cligen/src/station/document_v2.rs` | A8c route, fit, and seasonal coefficients | Remove candidate; A9 defines its own fit contract |
| `crates/cligen/tests/a8c_routed_daily.rs` | A8c runtime/profile/station integration | Remove candidate |
| `docs/specifications/SPEC-A8C-ROUTED-DAILY.md` | accepted experimental behavior record | Preserve, mark retired through registry/status policy |
| `docs/specifications/station-document-v2.schema.json` | A8c-specific station/model schema | Remove from accepted/current schema surface; preserve through Git history and A8c evidence |

## Shared integration surfaces requiring line-level disposition

| Surface | A8c content identified at scaffold time |
|---|---|
| `crates/cligen/src/profile.rs` | `A8cRoutedDailyV1` enum and string identity |
| `crates/cligen/src/runspec.rs` | revision-2 parser, station-model mapping, A8c profile constraints and resolution |
| `crates/cligen/src/modes.rs` | routed station requirement and routed generation path |
| `crates/cligen/src/daily.rs` | routed precipitation seam around faithful `gen_precip` |
| `crates/cligen/src/provenance.rs` | A8c station model/profile enums and closed validation combinations |
| `crates/cligen/src/quality/mod.rs` and `quality/report.rs` | routed parameter identity and A8c model acceptance |
| `crates/cligen/src/parquet_output.rs` | A8c station/profile serialization names |
| `crates/cligen/src/typed_output.rs` | A8c accepted profile token |
| `crates/cligen/src/fast_batch.rs` | signature adaptation made for the routed generation seam |
| `crates/cligen/src/lib.rs` and `station/mod.rs` | A8c module and type exports |

Execution must compare these files with the pre-A8c source commit and retain
later unrelated fixes. A generic function or signature survives only with an
independent current consumer and test; “the successor might need it” is not a
retention justification.

## Schema and specification surfaces

The current accepted/runtime schema set contains explicit
`a8c_routed_daily_v1`, `a8c_integrated_daily_v1`, and/or
`legacy_daily_only_v1` branches in:

- `docs/specifications/runspec.schema.json`;
- `docs/specifications/provenance-v1.schema.json` and its runtime mirror;
- `docs/specifications/quality-report-s2-m3.schema.json` and its runtime
  mirror;
- `docs/specifications/SPEC-RUNSPEC.md`;
- `docs/specifications/SPEC-PROVENANCE.md`;
- `docs/specifications/SPEC-QUALITY-REPORT.md`;
- `docs/specifications/SPEC-GENERATION-PROFILES.md`;
- `docs/specifications/SPEC-STATION-DOCUMENT.md`; and
- `docs/specifications/README.md`.

Retirement must remove current accepted combinations without erasing the
historical specification. Documentation schema and runtime mirrors must remain
byte-identical where the repository currently requires mirroring.

## Preserved scientific record

Preserve exact bytes for:

- `docs/work-packages/20260714-a7a-daily-precipitation-structure-baseline/`;
- `docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/`;
- `docs/work-packages/20260715-a8a-dry-regime-applicability/`;
- `docs/work-packages/20260715-a8b-secondary-year-fallback/`;
- `docs/work-packages/20260715-a8c-routed-daily-pilot/`;
- `docs/reports/a7a-daily-precipitation-structure-report.md` and its manifest;
- `.gitattributes` coverage for the A8c retained-stream archive; and
- A8a observed-source archives and the A8c Git LFS retained-stream object.

The execution baseline must hash the actual file set rather than relying on
this prose list.

## Required execution decisions

1. Did any A8c current surface ship through crates.io, a tag, release, or
   supported Git revision?
2. What is the last pre-A8c comparator commit, and which later unrelated edits
   must be preserved?
3. Does any routed seam have a current non-A8c contract, consumer, and test?
4. Are revision-2 station documents a released compatibility surface or only
   an unshipped A8c research format?
5. Which specification status mechanism preserves the A8c record while
   removing it from accepted current enums?
6. Do the retained LFS pointer, remote object, archive hash, and all member
   hashes verify before and after retirement?
