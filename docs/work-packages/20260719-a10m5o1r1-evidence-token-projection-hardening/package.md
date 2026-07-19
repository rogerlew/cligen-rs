# A10M5O1R1 — Evidence Token Projection Hardening

Status: `EXECUTED-COMPLETE`
Date: 2026-07-19
Evidence mode: Local plus retained private live evidence
ExecPlan: [`../../exec-plans/20260719-a10-multi-l40-qualification.md`](../../exec-plans/20260719-a10-multi-l40-qualification.md)

## Objective

Allow authentic third-party text logs containing reserved-looking
angle-bracket placeholders to pass publication projection without permitting
raw text to masquerade as a toolkit-authored sanitization token.

## Trigger and hypothesis

A10M5O2 completed all four live roles, but collection failed closed because
PyTorch `torchrun` emitted `<NO_OTHER_FAILURES>` in the controlled-failure
stderr. The only other forbidden content in that file is already covered by
the frozen durable-root and identity replacements. The hypothesis is that
escaping every raw reserved-looking token before typed replacement preserves
the diagnostic text, prevents token spoofing, and lets the unchanged raw
evidence project safely.

## Authority and scope

The operator's end-to-end multi-GPU toolkit instruction authorizes this direct,
bounded corrective successor. Agents have authoring authority for the local
projection implementation, tests, specification, guide, package records, and
resumption of the already-authorized A10M5O2 collection lifecycle. No new
Slurm allocation, retry, evidence mutation, plan widening, canonical-default
change, cross-node work, or scientific promotion is authorized.

## Plan and gates

1. Escape raw `<NAME>` tokens to `[[RAW_RESERVED_TOKEN:NAME]]` before applying
   authorized typed replacements and count the escapes in the private receipt.
2. Prove a PyTorch-shaped placeholder and a forbidden durable path project
   together, while invalid UTF-8 and unknown forbidden values still fail.
3. Update the normative toolkit specification and operator guidance.
4. Run all toolkit, package, shell, and repository gates, publish the repair,
   then resume projection from the retained private/raw evidence.

The terminal is `A10M5O1R1-EVIDENCE-PROJECTION-READY`. Any forbidden-value
leak, ambiguous transform, or failed gate yields `EXECUTED-HOLD` and leaves the
raw evidence and remote run intact.

## Artifacts

- `artifacts/verify.py` — deterministic surface verifier;
- `artifacts/gate-results.md` — local and retained-evidence results; and
- `artifacts/execution-disposition.md` — terminal and exact continuation.

## Disposition

Reached `A10M5O1R1-EVIDENCE-PROJECTION-READY`. Projection revision 4 escapes
and counts raw reserved-looking tokens before authorized replacements. The
exact PyTorch placeholder plus forbidden durable-path regression passes, all
56 toolkit tests pass, and every repository gate passes. The retained A10M5O2
raw evidence was reprojected without changing a job, plan, gate, or raw file.
The adapter policy label is now bound to the projector version constant.
