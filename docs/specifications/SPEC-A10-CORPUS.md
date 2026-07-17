# SPEC-A10-CORPUS — Research Corpus and Offline Transfer Surface

Status: research-only, revision 1 (A10M1)

## Surface

This specification defines A10 normalized corpus objects
([JSON Schema](a10-corpus-object-v1.schema.json)), role/partition manifests,
training-shard indexes, and offline transfer manifests. It does not define a
production generator profile or authorize confirmation access.

## Producers and consumers

A10M1 acquisition tooling produces source receipts, normalized immutable
objects, and manifests. A10M3 consumes only metadata to freeze design. A10M4
and later training stages consume `candidate_fit` and `fit_validation` shards.
Development and confirmation consumers are stage-gated separately.

## Authority basis

The surface is an extension governed by the A10 study plan section 7 and the
A10M1 prospective freeze. The accepted A9 data-role and confirmation rosters
remain authorities for inherited objects.

## Semantics

Every normalized object has one source identity, one role, one spatial or
station partition, one calendar transform, a closed period, coordinates,
regime sampling stratum, records or aligned arrays, and per-field availability
masks. Every numeric field declares units in the field glossary. Null is the
only unavailable-value representation; NaN, sentinel values, inferred
defaults, and cross-product filling are prohibited.

Daymet objects use `daymet_official_365_v1`. Their normalized Gregorian axis
contains a null/non-observed leap-year December 31 row. USCRN daily and
subhourly objects use local-standard-time product identities. Derived event
objects retain their source station and event-transform ID.

Roles are the exact A10 registry: `candidate_fit`, `fit_validation`,
`development`, `confirmation_metadata`, `confirmation_locked`,
`source_sensitivity`, and `synthetic_fixture`. Unknown roles fail closed.
Derived objects inherit source role. Only `candidate_fit` may fit
normalization statistics or update model parameters.

Training shards are deterministic gzip JSON Lines collections of complete
location/station objects. Their index records compressed and logical SHA-256,
byte counts, object counts, source, roles, periods, and schema version.
Transfer manifests enumerate every required offline object, its destination
class (`durable` or `job_local_stage`), bytes, and SHA-256. Destination
existence never substitutes for hash verification.

## Failure behavior

Readers fail closed on unknown schema, source, role, transform, unit, duplicate
identity, hash mismatch, inconsistent array length, tile/role leakage, locked
confirmation input, or unavailable values represented as observations.

## Provenance obligations

Manifests record the A10M1 freeze hash, source URL/product/version, access
time, source and normalized hashes, transform ID, role, period, host class,
and tool/source commit. Confirmation metadata records no target-byte hash and
must state `confirmation_target_series_accessed=false`.
