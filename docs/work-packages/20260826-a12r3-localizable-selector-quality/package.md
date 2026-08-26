# A12R3 — Localizable Selector Quality Comparison

Status: `EXECUTED-COMPLETE — CLOSEST_PREFERRED`

Date: 2026-08-26

Evidence mode: observed fit-validation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Prospectively compare closest, current rank-sum, and elevation-reference
selection after the same ordinary-localizability filter over all 240
fit-validation sites, and issue an evidence-bound exploratory disposition.

## Authority

- [SPEC-A12R3-LOCALIZABLE-SELECTOR-QUALITY](../../specifications/SPEC-A12R3-LOCALIZABLE-SELECTOR-QUALITY.md)
- [SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON](../../specifications/SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON.md)
- [SPEC-A12-STATION-SELECTION-EVALUATION](../../specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md)

## Plan and gates

1. Authenticate A12R2 and calendar-preflight the 240-site corpus.
2. Independently reproduce all 2,400 feasibility cells and three filtered winners.
3. Score all three arms using the frozen A12 metrics and inference rule.
4. Replay evidence and decision byte-identically from separate staging.
5. Obtain independent GO, run package/repository gates, and reconcile records.

No production code changes are planned, so coverage/CRAP gates are not triggered.

## Exit

Complete on authenticated 240-site evidence, exact predecessor feasibility
reproduction, a frozen exploratory disposition, byte-identical replay, required
repository gates, and independent GO. Confirmation access and default changes
remain unauthorized.

## Disposition

Executed at source commit `5644a89185b087f7be2eb4b415db4a06a92203d4`.
All 240 sites and 2,400 nearest-ten feasibility cells reproduce A12R2 exactly;
the three localizable arms bind 720 selected station identities and source
`.par` SHA-256 values. The exact two-cell sparse-wet-month diagnostic also
reproduces before scoring.

The exploratory disposition is `CLOSEST_PREFERRED`:

- closest median composite: `0.1581536227790057`;
- current rank-sum median composite: `0.1599439791846449`;
- elevation-reference median composite: `0.15936730702600482`;
- current versus closest: paired median `0`, bootstrap 95% interval `[0, 0]`,
  strict win fraction `0.25833333333333336`, unsupported; its PWD family median
  worsened `9.1114%`, exceeding the `5%` safeguard;
- reference versus closest: paired median `0`, bootstrap 95% interval `[0, 0]`,
  strict win fraction `0.22916666666666666`, unsupported.

Current and reference selected a different donor from closest at 126 and 125
sites respectively, but neither met the prospective support rule. This result
does not change a runtime default and does not open confirmation.

First/replay preflight, evidence, and decision are byte-identical. The final
evidence file SHA-256 is
`5711af00c28fa4d55a9af913024fe1ddf2b9460496a053a929be4c1d77c91e3d`;
decision SHA-256 is
`243ef5d529dddb518fb4f01ce9337362189fdcde6214ca9369cd159b5e027b16`;
cligen binary SHA-256 is
`01d53ea3a61ed1c604c8b2201c4cce1267ca2d8f01143b999f1bcbe90cc66483`.

## Audit history

The first complete/replay pair produced the same scientific result but closure
review found shared mutable station records had corrupted 582 reported
distances. That full pair and its receipt remain preserved under `attempt1-`
names. The corrected evaluator snapshots site arms; final review independently
found zero distance mismatches across all 720 rows.

## Successor boundary

The scientific comparison is complete. A successor may design the public
station-choice surface—explicit user station, closest localizable, and an
optional sophisticated selector—or consider a default change. That is a
material CLI/product compatibility decision and requires separate authority.
Generalizing zero-target or one-sided dry-month repair remains a separate
scientific study, not a prerequisite for station selection.
