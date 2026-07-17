# A10M1 leakage and firewall audit

Evidence mode: Ran

## Final v2 verdict

- Daymet locations: 1,440 identities, all unique.
- Daymet tiles: 351 identities; zero tile IDs carry more than one role.
- Minimum selected Daymet distance from every inherited A9 development or
  confirmation-metadata coordinate: 100.005749 km, above the frozen 100 km
  boundary.
- USCRN normalized stations: 24 unique daily plus 14 same-role derived event
  objects; zero station role splits.
- A9 development overlap: zero.
- 18-site confirmation overlap: zero.
- confirmation target-series access flag: false.
- confirmation target-byte hashes in the corpus: zero.

The machine-readable result is `leakage-audit-v1.json` and all three lists
(`tile_role_splits`, `station_role_splits`, `confirmation_overlap`) are empty.

## Failed v1 evidence

V1 correctly failed before transfer authorization. The complete candidate
partition had four boundary tile IDs with role disagreement across sampling
frames: `+32_-108`, `+37_-103`, `+45_-105`, and `+46_-105`; three entered the
first selected surface. V1 selection and shard manifests remain preserved and
their 60 external hashes verify, but they are explicitly invalid for training.

V2 excludes those four entire geographic tiles and restores quotas from the
prepublished, already role-labeled surplus. The correction does not rename a
tile, namespace geography by regime, relabel a role, or inspect climate values.
V2 has distinct selection, coverage, shard, and transfer identities.
