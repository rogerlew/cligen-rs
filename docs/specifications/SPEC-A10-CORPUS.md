# SPEC-A10-CORPUS — Research Corpus and Offline Transfer Surface

Status: research-only, revision 2 (A10M1; calendar-contract hardening
2026-07-19)

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

Daymet objects use `daymet_official_365_v1`. USCRN daily and subhourly objects
use local-standard-time product identities. Derived event objects retain their
source station and event-transform ID.

### Daymet calendar contract

The words "365-day", "no-leap", and "complete calendar" are insufficient
calendar specifications and must not substitute for a transform ID. These
surfaces are distinct:

| Surface | Normative leap-year behavior |
|---|---|
| Daymet `daymet_official_365_v1` source | 365 observations; February 29 is present and December 31 is absent |
| A10 normalized date axis | complete proleptic-Gregorian dates; the absent leap-year December 31 row is null and `source_observed=false` |
| A10 generated stream | complete proleptic-Gregorian calendar, including February 29 and December 31 |
| inherited A5 `noleap_365_v1` sensitivity | fixed month lengths with February 28 days; a separate legacy transform that is never interchangeable with the A10 transform |

The canonical fit-period example and exact false-mask dates are pinned in
[`a10-daymet-calendar-profile-v1.json`](a10-daymet-calendar-profile-v1.json).
For 1980-01-01 through 2009-12-31, a normalized object has 10,958 aligned
calendar rows, 10,950 observed Daymet rows, and eight null/unobserved rows:
December 31 of 1980, 1984, 1988, 1992, 1996, 2000, 2004, and 2008.

`dates` defines the normalized target axis. `source_observed` and non-null
required fields jointly define which rows may contribute observed values.
Therefore:

- a complete `dates` axis does not imply complete observations;
- consumers must not require every Gregorian row to be observed;
- consumers must not infer the missing civil date from a generic 365-day
  label or array length;
- imputation, calendar compression, or relabeling requires a separately named
  transform and corpus identity;
- month/year eligibility and all observed-data losses must be mask-based; and
- generated complete-Gregorian rows never fabricate a corresponding observed
  Daymet value.

For exact calendar windows, the end boundary is exclusive. Within the
1980--2009 fit period an eight-year target has 2,922 Gregorian labels and
2,920 observed Daymet rows. Each year-month used by A10M5R8 retains at least
28 jointly observed precipitation/Tmax/Tmin rows; future objectives must pin
their own support threshold rather than inherit that number implicitly.

### Consumer preflight

Before resource reservation or training, every A10 daily-data package must
publish a passing preflight receipt that records:

1. source transform ID and normalized calendar axis;
2. inclusive source bounds and exclusive window-end convention;
3. expected calendar, observed, and masked counts;
4. exact masked dates for at least one representative leap year;
5. required-field mask composition and month/year eligibility; and
6. a fixture spanning February 29, the absent December 31, and both sides of
   a target-window boundary.

An all-calendar-row-observed predicate for `daymet_official_365_v1` is a
contract violation and must fail during preflight, before scarce compute is
reserved or a scientific run begins.

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
confirmation input, unavailable values represented as observations, calendar
profile mismatch, or a consumer that treats an unobserved normalized row as a
target.

## Provenance obligations

Manifests record the A10M1 freeze hash, source URL/product/version, access
time, source and normalized hashes, transform ID, role, period, host class,
and tool/source commit. Confirmation metadata records no target-byte hash and
must state `confirmation_target_series_accessed=false`.

Revision 2 changes no revision-1 corpus bytes or role assignments. It makes the
already accepted Daymet transform, mask semantics, and consumer preflight
explicit after A10M5R8 exposed an invalid all-calendar-row completeness
assumption.
