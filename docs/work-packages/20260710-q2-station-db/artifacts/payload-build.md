# Payload Build — station collections 2026.07

Date: 2026-07-10
Evidence mode: **Ran** (all commands run this session).
Builder: `build-payloads.sh` (this directory) over
`/workdir/jimf-cligen532/db`; deterministic tar (sorted names, fixed
owner/mtime, `gzip -n`) so a rebuild from the same tree reproduces
the same hash.

## Archives (SHA-256 pinned in the embedded manifests)

| Collection | Archive | SHA-256 | Bytes |
|---|---|---|---|
| us-legacy | `us-legacy-2026.07.tar.gz` | `6c84662d4dd2e614b2dd4248dad417960610944840afc7f4c1dce254029972e4` | 6,884,908 |
| us-2015 | `us-2015-2026.07.tar.gz` | `f3bf68bb39e65378c1eefc9a956b514fc7cf0fb8e3377e868852f7b3f7b25ab9` | 5,907,330 |
| ghcn-intl | `ghcn-intl-2026.07.tar.gz` | `119053deacd1ff8b51cece29bd7e400611ad5da04a1ce72f67ef0fc7274eac21` | 46,934,522 |
| au | `au-2026.07.tar.gz` | `01082c6067dcb630f8b6e69e38f1a81728b9db7e3114efb3ac971cec03073ffb` | 5,301 |
| chile | `chile-2026.07.tar.gz` | `9c3b1f1869927991bc6bfa3807e4da3967231f787fba2961374bff6fa64f920e` | 3,249 |

Total ~60 MB compressed (source trees ~250 MB). Contents: the
verbatim collection tree (operator ruling: include everything) plus
the collection's python-produced SQLite catalog at the payload root.

## Hosting (Ran)

GitHub release `station-db-2026.07` on `rogerlew/cligen-rs`
(https://github.com/rogerlew/cligen-rs/releases/tag/station-db-2026.07),
one asset per archive. The repository is **private**, so the
manifests carry the API asset URLs
(`https://api.github.com/repos/rogerlew/cligen-rs/releases/assets/<id>`),
which work with a bearer token today and continue to work if the
repository goes public. Asset ids: au 472864209, chile 472864205,
ghcn-intl 472864204, us-2015 472864208, us-legacy 472864206.

## Pre-build verification (Ran)

- GHCN tier duplication, **all pairs**: every file in
  `10-year`/`20-year`/`30-year` is byte-identical to its `all_years`
  namesake — 12,703 identical, 0 mismatches, 0 missing.
- Payload health census: all 18,124 pars across the five trees are
  LF-terminated ASCII with ≥ 83 records.
- Golden cross-links: `us-2015/id106388.par` and
  `ghcn-intl/all_years/ASN00057011.par` are byte-identical (`cmp`) to
  the committed golden fixture pars — the sync round-trip can assert
  byte-identical golden `.cli` output through both collections.

## Test fixture

`au-2026.07.tar.gz` (5,301 bytes) is additionally committed at
`crates/cligen/tests/fixtures/stations/` so the CLI-level sync test
exercises the real embedded `au` manifest entry (same bytes, same
hash) through `--from` without network.

## Known catalog caveats carried verbatim (producer is python)

- `au` catalog stores Victorian stations with **negative longitude**
  values (e.g. Beechworth −146.71; the stations are at ~146.71°E) —
  location queries against `au` reflect the catalog as produced.
- `ghcn-intl`: 63 exact coordinate collisions, 158 duplicate names
  (distinct neighboring stations); no dedup.
- `us-legacy`: 3 tree files uncataloged (`temp.par`, `wepp.cli`,
  `wepp2.cli`; plus an empty `__init__.py`); `ghcn-intl`:
  `additional/WukariNRA.par` uncataloged. Carried, unqueryable.
