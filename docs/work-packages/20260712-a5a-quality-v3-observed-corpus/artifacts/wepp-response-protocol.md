# A5 Downstream WEPP Response Protocol

Status: format/protocol fixed; execution belongs to A5b/A5c
Date: 2026-07-12
Protocol ID: `cligen-a5-wepp-response-protocol-v1`
Response schema ID: `cligen-a5-wepp-response-v1`

## Why this is separate

`cligen quality` sees only rendered daily climate rows. It has no snowpack,
soil freeze/thaw, runoff, management, slope, or erosion state. Those physical
responses therefore cannot be fields in metrics v3 and cannot be inferred
from its air-temperature proxies.

## Required execution binding

Each response record must validate against `a5-wepp-response-v1.schema.json`
and bind:

- schema ID `cligen-a5-wepp-response-v1`, protocol ID
  `cligen-a5-wepp-response-protocol-v1`, semantic validator ID
  `cligen-a5-wepp-response-semantic-v1`, and the exact SHA-256 identity of
  each corresponding normative artifact used for the record;
- climate `.cli`, provenance, and quality-report SHA-256 identities;
- station/profile/model/fit/horizon/replicate identities;
- exact WEPP executable bytes, version output, platform, and invocation;
- exact run, management, soil, slope, and any watershed input hashes;
- exact climate installation/substitution method;
- output-file hashes and a versioned extraction-adapter hash;
- every metric's source file, column/record meaning, units, aggregation, and
  missing-value rule.

## Required response families

General sites: annual runoff, annual peak runoff, annual soil loss, and their
upper-tail summaries.

Cold/snow-domain sites (Climax, Lake Yellowstone, International Falls,
McGrath, and New Meadows): the exact available WEPP analogues for maximum
snow water state, snowmelt, rain-on-snow runoff, winter runoff, winter soil
loss, annual runoff, peak runoff, and annual soil loss.

Each required family has exactly one representation: either four available
rows with the unique statistics `mean`, `sd`, `p95`, and `max`, or one
unavailable row. Available summaries cover complete simulation years; each
scalar retains its units, year count, output hash, selector/record meaning,
aggregation, and missing-value rule. Every source output hash must identify a
declared `outputs[].content.sha256`, and those declared hashes are unique.
Within an available family all four rows use the same units and complete
source definition, and every `n_years` equals the climate's 30- or 100-year
horizon. All eight named families are nonnegative physical magnitudes, so
every available scalar is nonnegative. Mean and p95 cannot exceed maximum.

An unavailable family is an explicit `{status: "unavailable", reason: ...,
source_audit: ...}`; it is never mixed with available rows or zero-filled.
“Rain on snow” requires a documented WEPP state/flux definition and may not be
inferred only from warm precipitation following a cold day.

## Contract enforcement layers

The Draft 2020-12 schema enforces closed object shapes, required domain
families, and the one-unavailable-versus-four-available cardinality. The
package's `verify-wepp-response-schema.py` adds the semantic constraints that
JSON Schema cannot express generically by an object property: unique statistic
names per family, horizon/year-count equality, identical units and source
semantics within a family, nonnegative values and summary-value ordering, unique
`outputs[].content.sha256` values, and every available row's cross-array
reference to one of those hashes. Its external-record interface also parses
strict JSON, rejecting duplicate object keys, explicit non-finite numeric
tokens, and finite JSON number lexemes that overflow binary64. A response
artifact is valid only when it passes both layers through that interface.

The version-1 layers are jointly normative and independently hash-pinned:

| Artifact | SHA-256 |
|---|---|
| `docs/specifications/a5-wepp-response-v1.schema.json` | `7d006023684f2079ce09e5ab1af21e1154a417eb4295ebf1a02c40d7f7a2e70d` |
| `artifacts/verify-wepp-response-schema.py` | `05e7a085f146e264c3b34e3f7c04f498f0f4d3dd0c9b0cd17a0f8176221b683b` |

The schema fixes all three contract IDs and their field shapes. The semantic
validator requires every record's schema, protocol, and validator hashes to
equal the exact files executing together. A5b must reproduce the normative
files byte-for-byte, bind all three identities in its package/analyzer and
response records, and reject any record produced under a different contract
identity.

## Reference-forcing label

The current legacy observed seam supplies precipitation and Tmax/Tmin only;
other variables and event descriptors remain generated. A WEPP run using
that seam must be labeled `hybrid_observed_pt`. It is a sensitivity/baseline
response, not fully observed meteorological truth.

## Execution hold

No native, reviewed, provenance-complete WEPP executable and scenario deck is
part of cligen-rs today. A5a therefore pins the protocol but does not execute a
mutable sibling checkout or an unverified binary. A5b must fulfill this
binding before producing candidate response evidence; A5c cannot promote a
candidate while the required response vector is absent.
