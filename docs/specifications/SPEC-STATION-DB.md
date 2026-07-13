# SPEC-STATION-DB — Station Collections, Local Cache, and Location Query

Status: active (rev 2 — A4a adds the local-only `stations convert` bridge to
SPEC-STATION-DOCUMENT. Rev 1 was authored and implemented by
`20260710-q2-station-db`; operator rulings 2026-07-10: GitHub-hosted
payloads, verbatim collection trees, SQLite catalogs ship —
**python is the catalog producer**, Rust is a consumer)
Surface: the embedded collection manifests, the `cligen stations`
subcommand family (`list` / `nearest` / `sync` / `convert`), the local payload
cache, and the payload archive format.

## Purpose

CLIGEN is useless without station `.par` files, but ~250 MB of
climate parameters cannot ship inside a crates.io crate (10 MB
limit) and must not ride along with every `cargo build`. This spec
separates the **contract** (small, hash-pinned manifests embedded in
the crate) from the **payload** (archives hosted outside, fetched
once into a local cache by an explicit subcommand). Reproducibility
follows: a manifest identifies collection bytes exactly, and a run's
provenance can cite them.

## Producers / consumers

Producers: the payload build (`20260710-q2-station-db/artifacts/payload-build.md`)
and future collection revisions. **The SQLite station catalogs are
produced by Python tooling** (wepppy/jimf-cligen532 lineage) and ship
verbatim inside each payload; this crate never creates or mutates
them. Consumers: the `cligen` binary (`stations` subcommands),
wepppy / WEPPcloud station selection (which may read the cached
SQLite directly — that is why it ships), and any workflow feeding a
cache path into a runspec's `station.par`.

Authority basis: extension surface (no Fortran counterpart). The
**catalog of record is the collection's SQLite `stations` table**
(state, desc, par, latitude, longitude, years, type, elevation, tp5,
tp6); payload files not referenced by the catalog (working residue in
the historical trees) are carried verbatim but invisible to queries.
The typed SPEC-PAR parse governs the `.par` files themselves at run
intake, exactly as everywhere else. FSWEPP's `climNearest` is the
historical role model for the location query, not behavioral
authority.

## Collections (manifest set, version 2026.07)

| Name | Catalog rows | Lineage |
|---|---|---|
| `us-legacy` | 2,642 | original FSWEPP/Windows-WEPP US distribution |
| `us-2015` | 2,765 | US update, Anurag Srivastava 2015 |
| `ghcn-intl` | 12,704 | GHCN-Daily-derived international set |
| `au` | 7 | Australia (jimf-cligen532 lineage) |
| `chile` | 1 | Chile, NuevaAldea (jimf-cligen532 lineage) |

Payloads are the **verbatim collection trees** (operator ruling:
include everything) plus the collection's SQLite catalog at the
payload root. For `ghcn-intl` this includes the 10/20/30-year
subtrees — byte-identical duplicate subsets of `all_years` (verified
at build) retained as distributed; the catalog references the
`all_years` copies, and record-length tiers are equivalently the
query filter `--min-years N`. Known data-quality caveats ride along
undisturbed and undeduplicated: distinct GHCN stations share rounded
coordinates (63 exact latitude/longitude collisions) and names (158
duplicate `desc` values); the deterministic tie-break below makes
query results stable in their presence.

## Manifest (embedded, schema_version 1)

One JSON document embedded in the crate
(`crates/cligen/src/stations/manifests.json`) listing every
collection:

```json
{ "schema_version": 1,
  "collections": [ {
      "name": "us-2015",
      "version": "2026.07",
      "description": "US stations, 2015 update (Anurag Srivastava)",
      "lineage": "...",
      "catalog": "2015_stations.db",
      "catalog_rows": 2765,
      "archive": { "url": "https://...", "sha256": "<64 hex>", "bytes": 123 } } ] }
```

- `name`: `[a-z0-9-]+`, the cache key and CLI selector.
- `version`: opaque string; a payload revision is a new version and a
  manifest edit (crate release) — payload bytes for a published
  (name, version) are immutable.
- `catalog`: payload-root-relative path of the SQLite catalog;
  `catalog_rows` pins the expected `stations` count (sync
  cross-checks it).
- `archive.sha256`: SHA-256 of the `.tar.gz` payload; the sole trust
  anchor. `url` is a convenience, not a trust decision.
- Unknown manifest fields are rejected (fail closed at load — a crate
  always understands its own embedded manifest).

## Payload format

A gzipped tar of the collection tree: regular files only, paths
relative to the collection root (no absolute paths, no `..`, no
symlinks — extraction enforces this). The **station id** is the
catalog's `par` value, exactly as the Python producer wrote it
(`AK500026.PAR`, `id106388.par`); case is preserved and significant.

### Catalog-to-file resolution

The catalog stores bare par names. A name resolves to a payload file
by probing, in pinned order, relative to the payload root: the name
itself, then `all_years/<name>`, then `additional/<name>`, then
`30-year/<name>`, `20-year/<name>`, `10-year/<name>`. First hit wins.
Sync verifies every catalog row resolves; an unresolvable row fails
the sync.

## Cache

- Root: `$CLIGEN_DATA_DIR`, else `$XDG_CACHE_HOME/cligen`, else
  `~/.cache/cligen`.
- Layout: `<root>/stations/<name>/<version>/` holding the extracted
  payload. Extraction goes to a temporary sibling directory first and
  is renamed into place, so a cache entry is either absent or
  complete.
- The cache is disposable: deleting it and re-running `sync`
  reproduces it bit-for-bit from the manifest (hash-verified).

## Subcommands

- `cligen stations list [<collection>]` — every manifest collection
  with version, sync state, and catalog row count (queried from the
  cached catalog when synced).
- `cligen stations nearest --lat <deg> --lon <deg> [--collection <name>]
  [-n <count>] [--min-years <y>] [--json]` — the `climNearest`
  successor. Distance is the great-circle haversine on a sphere of
  radius 6371.0088 km, computed in f64 over the catalog's
  latitude/longitude (degrees, sign conventions as the catalog states
  them). Ordering: ascending distance, ties by collection name then
  `par` id (byte-wise ascending); `-n` defaults to 5; `--min-years`
  filters on the catalog `years` column (the GHCN record-length-tier
  successor). Output rows carry collection, id (`par`), desc,
  latitude, longitude, years, distance_km, and the absolute cache
  path — the path is what a runspec's `station.par` consumes.
  Without `--collection`, all synced collections are searched.
- `cligen stations sync [<collection> ...] [--from <dir>] [--force]` —
  the **only network-touching operation in the tool**. Default: all
  collections. For each: download the archive (or read
  `<name>-<version>.tar.gz` from the `--from` directory), verify
  SHA-256 **before extraction**, extract with traversal guards, open
  the catalog and cross-check `catalog_rows` and per-row file
  resolution, atomically publish the cache entry. A collection
  already cached at (name, version) is skipped unless `--force`.
  `--from` is the air-gap path: bytes may arrive by any transport;
  verification is identical.
- `cligen stations convert <par> <document> [--overwrite]` — parse one
  explicit legacy `.par` through SPEC-PAR and write deterministic
  SPEC-STATION-DOCUMENT JSON. This command never reads a catalog or touches
  the network; an existing destination fails closed unless `--overwrite` is
  explicit.
- Authentication: if `CLIGEN_SYNC_TOKEN` is set, `sync` sends it as a
  bearer token (with `Accept: application/octet-stream`) — required
  while the hosting repository is private. Token material is never
  written to the cache or logs.

## Network posture (normative)

`cligen run`, `cligen validate`, `cligen quality`, `cligen stations convert`,
and every library
simulation path perform **no network I/O, ever**. Only
`stations sync` fetches, only from manifest URLs, and nothing is
trusted until its hash matches. A hash mismatch aborts before
extraction and leaves the cache untouched.

## Provenance obligations

The manifest carries lineage per collection. A future SPEC-PROVENANCE
block citing a station should record the collection name, version,
and archive sha256 alongside the `.par` content hash (the quality
report already carries the latter).

## Non-goals

- No implicit or automatic sync; no network fallback in `run`.
- No station-by-id runspec field (SPEC-RUNSPEC is untouched;
  `nearest` emits paths).
- No catalog production or mutation in Rust (python owns it); no
  dedup or "repair" of catalog data-quality quirks.
- No PRISM localization or par mutation (A4).
- No crates.io publication in the implementing package (`--dry-run`
  only; publication is an operator action).

## Acceptance (implementing package)

- `cargo publish --dry-run` clean, package under the crates.io size
  limit, no payload bytes in the tarball.
- Fresh `cargo install --path` → `stations sync` → `nearest` → a
  runspec consuming the emitted cache path → `cligen run`, end to
  end; on `us-2015`/id106388 the produced `.cli` byte-equals the
  golden (the cached par is byte-identical to the golden fixture
  par).
- Manifests carry SHA-256 + lineage for all five collections.
- `nearest` matches a pinned oracle computed by an independent
  implementation (independent catalog read **and** independent
  haversine) across all five collections.
- Corrupted payload (hash mismatch) and traversal-attack archive
  vectors fail closed.
