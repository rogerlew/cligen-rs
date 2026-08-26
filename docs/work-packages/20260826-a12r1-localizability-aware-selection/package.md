# A12R1 — Localizability-Aware Station Selection

Status: `EXECUTED-COMPLETE`

Date: 2026-08-26

Evidence mode: observed fit-validation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Implement the operator-authorized explicit independent-occurrence repair,
prove it resolves the exact A12 donor failure without changing default
behavior, and retain the full-localizability filter as the comparison arm for
later corpus-wide policy evaluation.

## Trigger

A12 stopped at `EXECUTED-HOLD-UNLOCALIZABLE-DONOR`: site
`p+3325_-11650` made all three raw policies select `ca040983.par`. Its June
`P(W/W)=P(W/D)=0` defines an all-dry stationary state, but gives zero source
expected precipitation for a positive PRISM target and an undefined `0/0`
persistence ratio. A12 emitted no scientific policy disposition.

## Authority

- [SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION](../../specifications/SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION.md)
- [A12 failure receipt](../20260826-a12-station-selection-heuristic-evaluation/artifacts/execution-failure-receipt-v1.json)
- [SPEC-A12-STATION-SELECTION-EVALUATION](../../specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md)

Immutable predecessor: A12 source commit
`d94f6eab53c9103c797b332ae51aea3a87341bcb`; failure-receipt file SHA-256
`ba103ab7d50fbc510910f980181aec9f3a8c188a05cdbee2b7780f7ce567fa7f`.

## Scope and plan

1. Freeze the opt-in CLI value, profile identity, zero-count limiting algebra,
   independence assumption, warnings, receipts, and default-behavior boundary.
2. Implement without breaking the existing public localization/run APIs.
3. Prove the ordinary profile still fails on the exact A12 point and the repair
   profile succeeds with complete cryptographic provenance.
4. Independently review and run all repository gates.
5. Retain the 2,400-candidate feasibility and policy-quality comparison as a
   separately published experimental stage; do not infer it from one repair.

## Exit

The implementation stage reaches `EXECUTED-COMPLETE` only with default-failure
and explicit-repair-success evidence on the A12 vector, structured and human
warnings, cryptographic receipts, all repository gates, and independent GO.
Corpus-wide comparative claims remain unauthorized until their own prospective
evaluator is published and executed.

## Disposition

`EXECUTED-COMPLETE`. Source commit
`de1502ad4d80a7205ac128c24e1851a42380f5b7` implements the explicit profile.
The exact A12 vector proves that the ordinary profile still fails atomically
and the explicit profile succeeds with a structured warning and complete
cryptographic provenance. June encodes `PWW=PWD=0.01`, mean wet-day
precipitation `0.21 in`, and expected monthly precipitation `0.063 in` against
the `0.06319291009677677 in` PRISM target. Independent review returned GO with
no P0/P1 findings and all repository gates passed.

Evidence:

- [build receipt](artifacts/build-receipt-v1.json)
- [execution receipt](artifacts/execution-receipt-v1.json)
- [independent review](artifacts/review.md)
- [test results](artifacts/test-results.md)

## Current boundary and successor

This package does not retroactively change A12, the ordinary runtime profile,
station selection, or confirmation access. The next scientific stage is a new
prospective corpus-wide comparison of raw selected-donor repair against the
full-localizability selector arms already specified here; no selector default
is inferred from this one exact-vector repair proof.
