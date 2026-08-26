# A12R3 — Localizable Selector Quality Comparison

Status: `READY-TO-EXECUTE`

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
