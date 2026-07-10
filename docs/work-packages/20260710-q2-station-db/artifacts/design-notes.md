# Design Notes — Q2 Station DB

Date: 2026-07-10
Evidence mode: **Ran** for every survey claim (commands run this
session against `/workdir/jimf-cligen532/db`).

## Collection survey (Ran)

| Collection | Tree | Catalog | Catalog rows | Files | Size |
|---|---|---|---|---|---|
| us-legacy | `stations/` | `stations.db` | 2,642 | 2,646 | 26 MB |
| us-2015 | `2015_par_files/` | `2015_stations.db` | 2,765 | 2,765 | 22 MB |
| ghcn-intl | `GHCN_Intl_Stations/` | `ghcn_stations.db` | 12,704 | 12,705 pars + docs | 201 MB |
| au | `au_par_files/` | `au_stations.db` | 7 | 7 | 60 KB |
| chile | `chile/` | `chile.db` | 1 | 1 | 12 KB |

All five catalogs share the `stations` table schema `(state, desc,
par, latitude, longitude, years, type, elevation, tp5, tp6)`;
`chile.db` adds an `annual_ppt` column and a `states` table (queries
select named columns, so the variance is harmless).

## Rulings (operator, 2026-07-10, mid-package)

1. **Hosting: GitHub** — release assets on this repo. The repo is
   currently **private** (Ran: `gh repo view` → `PRIVATE`), so `sync`
   carries optional bearer-token auth (`CLIGEN_SYNC_TOKEN`); public
   visibility is a standing operator decision.
2. **Payload scope: include everything** — verbatim collection
   trees. GHCN ships its full 201 MB tree including the 10/20/30-year
   subtrees even though they are byte-identical duplicate subsets of
   `all_years` (Ran: 0 subtree files missing from `all_years`;
   spot-compared byte-identical; all-pairs verified at payload
   build). Inert residue rides along (us-legacy `temp.par`,
   `wepp.cli`, `wepp2.cli`, an empty `__init__.py`; GHCN `.xlsx`,
   `.kmz`, coordinate `.csv`s) — the catalog makes it invisible to
   queries.
3. **Air-gap path: yes** — `sync --from <dir>`, identical hash
   verification.
4. **Catalogs ship; python is the producer** — the SQLite files are
   produced by Python tooling and ship verbatim at the payload root.
   Rust *consumes* the catalog (rusqlite, bundled SQLite) instead of
   deriving a competing index from the pars: one producer, one
   catalog of record, and wepppy can read the cached `.db` directly.
   The 4 uncataloged us-legacy files and the 1 uncataloged GHCN par
   (`additional/WukariNRA.par`) are therefore carried but unqueryable
   — faithful to the production catalogs.

## GHCN duplicate-record caveat (operator flag, confirmed Ran)

The catalog has no duplicate `par` values (12,704 distinct), but 63
exact (latitude, longitude) collisions and 158 duplicate `desc`
values — genuinely distinct neighboring stations sharing rounded
coordinates (e.g. `ASN00092024` "Mathinna (Fingal Road)" vs
`ASN00092106` "Mathinna (South Esk River)", both −41.47/147.89).
Handling: none — no dedup, no repair (python owns the catalog). The
nearest tie-break (distance, then collection, then `par` byte-wise)
makes results deterministic in their presence.

## Other pinned decisions

- **Station id = the catalog's `par` value verbatim** (case
  significant: us-legacy is `UPPER.PAR`, us-2015 lower).
- **Catalog-to-file resolution** by pinned probe order (root,
  `all_years/`, `additional/`, `30-year/`, `20-year/`, `10-year/`)
  because catalogs store bare names while GHCN's tree is nested.
  Verified exhaustively at sync; unresolvable row = failed sync.
- **Record-length tiers** (GHCN 10/20/30-year) are exactly
  `--min-years N` on the catalog `years` column (Ran: tier
  membership matches the `YEARS=` par field on spot-checks).
- **Payload health** (Ran census): all 18,124 pars across the five
  trees are LF-terminated ASCII with ≥ 83 records; the only anomaly
  is the empty `__init__.py` (not a par; carried inert).
- **`id106388.par` in us-2015 is byte-identical to the golden
  fixture par** (Ran: `cmp`) — the install → sync → nearest → run
  round-trip can assert a byte-identical golden `.cli`.
- **Haversine, R = 6371.0088 km, f64** — pinned in the spec; the
  oracle is an independent Python implementation over an independent
  catalog read.
- New dependencies: `rusqlite` (bundled), `ureq`, `tar`, `flate2` —
  adjudicated by `cargo deny` in the gate run.
