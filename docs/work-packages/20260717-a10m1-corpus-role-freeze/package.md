# A10M1 — Corpus Inventory, Acquisition, Normalization, and Role Freeze

Status: `EXECUTED-COMPLETE`
Date: 2026-07-17
Evidence mode: Mixed
Terminal: `A10M1-CORPUS-READY`

## Objective

Build and freeze the research-only A10 fit corpus before model design or
candidate output exists. Inventory the available sources, acquire only the
permitted fit identities, normalize calendars and fields without inventing
observations, separate roles spatially, and leave immutable manifests suitable
for offline transfer to Lemhi.

## Scope

Included are Daymet V4 R1 single-pixel daily data, the current USCRN station
inventory and a bounded USCRN daily/subhourly fit surface, inherited A9
development objects, inherited synthetic fixtures, optional-source
adjudication, source and normalized identities, calendar tests, spatial tiles,
role partitions, field availability, event counts, leakage checks, fit-only
normalization statistics, shard identities, transfer identities, and notices.

Excluded are confirmation target bytes, candidate architecture or output,
threshold calibration, GPU use, Slurm submission, production runtime changes,
and silent substitution of gridMET or PRISM for a primary source.

## Authority

- `A10M0-PREDECESSORS-FROZEN` and its A10M1/A10M2 handoff authorize this
  package from `main`.
- [A10 study plan](../../planning/a10-study-plan.md) section 7 and milestone
  M1 define the corpus and gate.
- [SPEC-A10-CORPUS](../../specifications/SPEC-A10-CORPUS.md) defines the
  research-only normalized object and manifest surfaces.
- The accepted A9 role freeze and 18-site metadata-only confirmation roster
  remain authoritative. A10M1 may inventory confirmation metadata but must not
  request its Daily01 or Subhourly01 target series.

## Plan

1. Publish the package scaffold, exact sampling/role/access freeze, calendar
   contract, source inventory, schemas, and acquisition program to `main`.
2. From that clean published commit, verify the confirmation guard and acquire
   the current official source documents and permitted series within the
   frozen byte/request/wall ceilings.
3. Normalize Daymet and USCRN objects, preserve actual missingness and event
   frequencies, create deterministic shards, and hash every retained object.
4. Produce coverage, availability, rights, leakage, normalization, and
   offline-transfer evidence; run independent verification and repository
   gates.
5. Close honestly as complete or at the applicable frozen corpus/rights hold,
   reconcile the roadmap/catalog, commit, and push `main`.

## Execution & dispatch

Scaffold executor and package executor: Codex on operator host `rmm`, starting
from current synchronized `origin/main` and pushing only to `main`. Network
acquisition is local to `rmm`; A10M1 submits no Lemhi or other Slurm jobs.
Large public source objects and training shards live under the package's
ignored `raw/` tree. Git retains their hashes, retrieval identities, schemas,
and evidence, not the third-party bytes.

Execution began from published scaffold `399e2ee`; the exact pre-series role
partition was published at `7536707`. The failed v1 tile surface was preserved,
and the value-blind v2 repair freeze was published at `cdedd00` before v2
materialization. No Lemhi connection, Slurm job, or GPU allocation was used.

## Gates

- at least 200 `candidate_fit` Daymet locations per primary regime and at
  least 40 `fit_validation` locations per regime, assigned by spatial tile;
- multiple tiles per regime and no tile or station split across roles;
- all eligible USCRN stations are inventoried and every included/excluded use
  has a reason; development and confirmation stations never enter fitting;
- every field declares source, units, calendar/day boundary, missingness, and
  quality behavior;
- calendar test vectors prove Daymet leap-year February 29 retention, absent
  December 31 masking, and complete Gregorian generation semantics without
  fabricated observations;
- actual zero-event and sparse-event frequencies remain visible;
- confirmation metadata remains byte-hash-free and target access is false;
- every retained source is permitted for its named use;
- every ignored retained object has a verified manifest hash and the transfer
  index is sufficient for offline Lemhi staging;
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass; and
- no production function changes, so the coverage/CRAP gate is not triggered.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10M1-CORPUS-READY`, all gates above,
and a frozen corpus usable by A10M3/M4 without reopening roles. Failure to
meet source, coverage, calendar, leakage, or integrity requirements closes
`EXECUTED-HOLD-A10-CORPUS`. A source whose rights do not permit the declared
retention or public evidence closes `EXECUTED-HOLD-A10-DATA-RIGHTS`.

## Result

All exit criteria passed on corpus v2. The accepted surface contains 1,200
Daymet fit and 240 tile-held validation locations across 351 nonleaking tiles,
24 eligible USCRN daily stations, 14 event stations with 21,495 actual events,
32 hash-pinned inherited development objects, and 98 verified offline transfer
objects totaling 223,799,545 bytes. Calendar tests preserve 15,768,000 observed
values per Daymet field and mark 11,520 leap-year December 31 absences without
fabrication. Confirmation access is false and every overlap list is empty.

The first Daymet selection is retained as failed evidence because three of
four globally ambiguous boundary tiles entered opposite roles. The v2
correction excluded all four and restored exact quotas from 25 deterministic
surplus points with their prepublished roles; it read no climate value for
selection and made no new request. Both v1 and v2 external hashes verify at
distinct paths, but only v2 is authorized downstream.

## Artifacts

- `artifacts/design-freeze.md` — prospective acquisition, sampling, role, and
  resource contract.
- `artifacts/source-inventory.md` and `artifacts/third-party-notices.md` —
  product roles, authority, rights, and optional-source disposition.
- `artifacts/calendar-transform-contract.md` and test vectors — exact calendar
  semantics.
- `artifacts/field-glossary.md` and the registered A10 corpus JSON Schema —
  normalized fields, units, masks, and fail-closed object shape.
- `artifacts/a10m1-freeze-v1.json` — machine-readable immutable inputs.
- `artifacts/jobs/a10m1_corpus.py` — acquisition, normalization, audit, and
  independent verification entry point.
- execution manifests, coverage/availability analysis, leakage audit,
  transfer index, gate results, review, and verification — produced during
  execution.
- `artifacts/execution-receipt.md`, `coverage-availability-analysis.md`, and
  `leakage-audit.md` — human-readable execution and gate evidence.
- `artifacts/source-manifest-v1.json`, `normalized-manifest-v1.json`,
  `availability-cube-v1.json`, `normalization-statistics-v1.json`, and
  `offline-transfer-manifest-v1.json` — accepted machine-readable evidence.
- `artifacts/daymet-selected-v1.json` / `daymet-shard-manifest-v1.json` —
  preserved invalidated selection; not authorized for training.
- `artifacts/daymet-tile-repair-freeze-v2.json`, `daymet-selected-v2.json`, and
  `daymet-shard-manifest-v2.json` — accepted value-blind repair and v2 corpus.
- `artifacts/verification.md`, `review.md`, `gate-results.md`, and
  `a10m3-handoff.md` — closure, review, and bounded successor handoff.
