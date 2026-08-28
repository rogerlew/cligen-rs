# A11E7 — Faithful Temperature QC Attribution

Status: `EXECUTED-COMPLETE — QC_MATERIAL_AND_STRUCTURAL_DEFICIT_REMAINS`

Date: 2026-08-28

Evidence mode: prospective observed-target development ablation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Measure the contribution of faithful `RANSET` conditioning to temperature
underdispersion before choosing the base for a temperature temporal overlay.

## Authority

- [SPEC-A11-FAITHFUL-TEMPERATURE-QC-ATTRIBUTION](../../specifications/SPEC-A11-FAITHFUL-TEMPERATURE-QC-ATTRIBUTION.md)
- A11E6 faithful baseline evidence
- A11E6S static source review
- implemented, provenance-declared `qc_filter` seam
- operator authorization to scaffold and execute A11E7

## Scope

Included: 20 stations, 32 burns, conditioned/off paired generation, observed
temperature scoring, process-QC attribution, cryptographic provenance, exact
A11E6 overlap replay, full replay, review, gates, and reconciliation.

Excluded: generator changes, overlay implementation, precipitation decisions,
station selection changes, confirmation, promotion, defaults, and WEPP claims.

The first exact-source attempt found a quality-report relational-validator
defect at station `co050130`, burn `53`: one valid correlation estimator was
undefined while the other was defined. The published schema permits the two
nullable estimators independently, and their estimators have independent
finite-result gates. A bounded specification, validator, and regression-test
correction is therefore included before restarting the source-bound run. This
does not alter generated climate values or the frozen A11E7 estimand.

## Plan and gates

1. Freeze specification, manifest, schema, executor, and synthetic tests.
2. Publish exact execution source on `origin/main`.
3. Build release CLIGEN and execute the 1,280-stream grid.
4. Replay scientific outputs byte-identically, review, run gates, and close.

The quality-report validator correction changes one production Rust function,
so the workspace coverage/CRAP gates are required.

## Resource bound

One execution and one replay, each limited to 1,280 local CPU streams. No
external service or scarce accelerator is used.

## Exit

Close with the frozen attribution disposition or an exact integrity HOLD.

## Outcome

The first exact-source attempt from `84baddf0e5e26adb0e9b8a6cd819bfbd172e742f`
failed closed when a valid quality report had independently nullable Pearson
and Spearman results. No scientific output was published. The bounded
specification, validator, and regression-test correction was published as
`984b983e6d058aa8b190cef02667e328aad39ebc`; it changes no generated climate
value. The corrected source built release binary SHA-256
`2136e940208b134e7bbaac677abdc038030fb406a62014847ab2dad67d4db665`
identically on the execution and replay.

Both complete runs generated 1,280 streams and 7,480,320 daily rows, replayed
all 160 A11E6 overlap streams exactly, preserved the 20 source `.par`
identities, and left confirmation sealed. The preflight, 640-pair evidence,
and decision artifacts replayed byte-identically.

QC removal materially relieves temperature underdispersion. Median annual
generated/observed variance rises from `0.07875` under faithful QC to
`0.10240` with QC off; the paired off/on median is `1.29357`. Median absolute
log variance error falls to `0.89666` of faithful. QC-off is closer for 425 of
640 members, and every one of the 20 stations and all six regimes has a median
paired variance increase. Monthly temperature mean error remains noninferior
at `1.01053` times faithful.

The conditioner is highly active: faithful temperature columns record 201,460
rejected attempts for 245,760 accepted batches, with no cap give-ups. On the
diverged QC-off paths, 178,060 of 245,760 temperature batches (72.45%) would
have failed the faithful verdict. This supports a causal QC contribution, but
not a complete explanation: QC-off retains only `0.10240` of observed median
annual variance and never reaches the frozen `0.95` structural threshold.

The disposition is therefore
`QC_MATERIAL_AND_STRUCTURAL_DEFICIT_REMAINS`. QC-off is not promoted and no
default changes. The simplest successor is a temperature-only annual-state
overlay pilot using faithful as operational control, QC-off as the declared
development base, and QC-off plus overlay as treatment. It should preserve the
monthly-mean noninferiority gate and measure the complete temperature metric
family before any confirmation or production decision.
