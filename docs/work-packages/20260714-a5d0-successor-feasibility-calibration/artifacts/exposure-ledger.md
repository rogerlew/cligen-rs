# A5d0 Exposure Ledger

Status: `CLEAN`
Closure date: 2026-07-14

## Rules applied

- A5a/A5b/A5c results were treated as exposed development evidence.
- No existing station or period was relabeled as untouched confirmation.
- Raw A5a Daymet/GHCN value rows were not opened; only file names, accepted
  corpus identities, and already published aggregate results were inspected.
- No A5d candidate climate, metric, quality report, or WEPP response was
  generated or read.
- Synthetic fixtures contain no station or observed target values.

## Access record

| Date | Actor | Role | Input/artifact | Values exposed | Authorized purpose | Consequence |
|---|---|---|---|---|---|---|
| 2026-07-14 | Codex | development audit | A5b/A5c report, advisory, specifications, decisions, analyses, and manifests | Previously accepted aggregate development results | Reconstruct constraints and access boundary | Remain development only |
| 2026-07-14 | Codex | corpus inventory | File names under `references/observed/a5a-v1`; corpus config and derived-corpus identities | Station/source IDs and existing metadata; no raw value rows | Count exposed inputs and test whether untouched confirmation exists | 17 Daymet and 8 GHCN records classified exposed |
| 2026-07-14 | Codex | synthetic derivation | Six artificial two-day year blocks | Synthetic numeric values only | Test variance decomposition, stationary kernel, counterexample, and power arithmetic | No confirmation exposure |
| 2026-07-14 | Codex | evidence lock | Accepted public A5 inputs and A5c public-surface lock | File bytes and hashes | Freeze authority and prove no public-surface mutation | No candidate exposure |

## Closure

`CLEAN`: zero A5d confirmation candidate outputs exist; zero confirmation
target metric values were accessed. The package holds before a confirmation
corpus or candidate contract is frozen.
