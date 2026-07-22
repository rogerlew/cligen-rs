# A10 external-normal conditioning ExecPlan

This living ExecPlan follows `.agent/PLANS.md` and coordinates the
A10M5R15 package without merging its authority into earlier A10 records.

## Purpose / Big Picture

Determine whether immutable measured monthly site normals supply the missing
climatological-location information that seven descriptor-only A10 families
could not infer. The observable outcome is one authenticated development
terminal from two matched attribution pairs, with no confirmation access or
production change.

## Progress

- [x] 2026-07-21: accepted ADR-0006/0007 and drafted the successor contract.
- [x] 2026-07-21: corrected the runtime boundary, control labeling, capacity
  ceilings, E2 model identity, and matched-ablation design.
- [x] 2026-07-21: scaffolded A10M5R15 contracts, preflight, resources, and
  fail-closed verification.
- [ ] Implement and publish immutable execution/job sources on `main`.
- [ ] Authenticate PRISM coverage for 1,440 corpus objects and six temporal
  sites before any scarce-resource reservation.
- [ ] Execute control, four-arm portfolio, replay, runtime benchmark, cleanup,
  review, and terminal reconciliation.

## Surprises & Discoveries

- The draft called R14 arm B the strongest prior result, but arm D was slightly
  better on both frozen temporal statistics. Arm B remains only E1's matched
  control; arm D stays visible as the prior incumbent.
- The draft mixed a P2 frozen-input statement with a backbone-free E2 runtime
  claim. E2 is now explicitly a replacement and has an otherwise-identical
  descriptor-only E2C control.
- ADR-0006 amended Sections 4.5/10.5 but left other 10× prose apparently
  normative. The plan now makes the 30× boundary explicit in objectives,
  hypotheses, milestone gates, risks, and terminal semantics.

## Decision Log

- Decision: use two matched pairs, E0/E1 and E2C/E2. Rationale: ADR-0007
  requires attributable normals evidence; E0 cannot control E2's architecture
  change. Date/Author: 2026-07-21, Codex.
- Decision: E2C/E2 are backbone-free replacement models below 330,000 total
  parameters; E0/E1 retain P2 under R14's 340,000 ceiling. Date/Author:
  2026-07-21, Codex.
- Decision: freeze one shared strictly positive paired-attribution margin from
  candidate-blind null/control evidence before output while retaining the
  existing absolute temporal gates. Date/Author: 2026-07-21, Codex.
- Decision: reuse the proven two-L40/two-wave topology at a 515
  L40-minute-equivalent ceiling. Date/Author: 2026-07-21, Codex.

## Outcomes & Retrospective

Scaffolding is complete. No model output, GPU reservation, confirmation target,
or public runtime change exists yet. Complete this section after the terminal.

## Context and Orientation

The owning package is
`docs/work-packages/20260721-a10m5r15-external-normal-conditioning/`.
`docs/specifications/SPEC-A10-EXTERNAL-NORMAL-CONDITIONING.md` governs model
semantics. `SPEC-A10-CORPUS` governs Daymet calendar/missingness, and
`SPEC-A10-STOCHASTIC-PRISM-COMPARATOR` governs the immutable normals asset.
R14R2R2 supplies the accepted continuous-time implementation and temporal
evidence, but its failed candidates are not relabeled or rescored.

## Plan of Work

Milestone one implements exact local source and fixture tests without candidate
output. Milestone two publishes the source and prepares a fresh authenticated
asset tree. Milestone three completes calendar/normals preflight and the
control. Milestone four executes the two-wave portfolio. Milestone five
collects, replays, benchmarks, cleans, reviews, and closes the package.

Each milestone is independently verifiable. No later milestone may compensate
for a failed predecessor gate, and no output-time result can change an arm,
threshold, field, capacity, member roster, or resource bound.

## Concrete Steps

Run all commands from the repository root on `main`.

1. `python3 docs/work-packages/20260721-a10m5r15-external-normal-conditioning/artifacts/verify_scaffold.py`
2. Implement the source overlays and their focused fixture tests in the owning
   package; compile every Python source and run shell syntax checks.
3. Run `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
   `cargo test`, and `git diff --check`.
4. Publish to `main`; only the published commit may enter toolkit authority.
5. Follow the exact eleven-stage sequence in the package `plan.md`, recording
   commands, receipts, hashes, job IDs, resource use, cleanup, and terminal.

## Validation and Acceptance

Acceptance requires the owning package gates, zero unresolved P1/P2 independent
review findings, exact source/asset hashes, complete preflight before resource
use, all four arms, two byte-identical replays, all runtime classifications,
sealed protected roles, reconciled resources, and verified cleanup.

## Idempotence and Recovery

Local verification is repeatable and read-only outside generated scratch
directories. Asset preparation requires a fresh destination. A failed control
does not authorize portfolio submission. Candidate science is attempted once;
only cleanup ambiguity may consume recovery minutes. Never reset the ledger or
reuse predecessor authority. A successor after an operational failure receives
fresh package/run/authority identities without altering science.

## Artifacts and Notes

Commit only bounded contracts, source, tests, sanitized receipts, reviews, and
terminal summaries. Raw streams, checkpoints, restricted corpus objects, and
large evidence archives remain outside Git and are represented by hashes.

## Interfaces and Dependencies

Dependencies are the canonical Lemhi Python 3.11/L40 environment, the accepted
A10M1 corpus, the exact R14 source/evidence identities, the PRISM runtime bundle
version 2026.07, the portable CPU export path, and Lemhi toolkit revision 2.
No network lookup is allowed during generation; normals are read from the
verified immutable local bundle.

Revision note (2026-07-21): created after review of the proposed A10M5R15
candidate plan and incorporated all five review recommendations.
