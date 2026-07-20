# A10M5R13R2 — Semantic Plan Replay Authentication Remedy

Status: `SCAFFOLDED`
Date: 2026-07-20
Evidence mode: Zero-GPU operational successor; R13R1 evidence replay only
Starting branch and push target: current `main`, push `main`

## Objective

Authenticate and complete the pre-cleanup selector replay for the already-run
A10M5R13R1 candidate comparison. R13R1's replay command treated a raw input
plan as though it were the authenticated toolkit plan receipt. The raw plan
contains the evidence allowlist but no toolkit `plan_id`; the publication
receipt contains the authenticated `plan_id` but intentionally omits the
allowlist. Comparing those unlike records cannot establish the semantic plan
that authorized collection.

R13R2 separates those inputs. It authenticates the toolkit publication plan
receipt, reconstructs the toolkit semantic plan exactly from the frozen raw
plan, and proves its canonical SHA-256 equals the receipt's `plan_id` before
using the semantic plan's evidence allowlist.

## Frozen evidence and science

- Input package: `20260720-a10m5r13r1-admission-controller-materialization-remedy`.
- Input run: `a10m5r13r1-admission-controller-materialization-remedy-r0`.
- Input source commit: `927c6147f879ed3a9a56ff1218ffaa3953bef93c`.
- A committed R13R1 input pin freezes the raw-plan file, semantic plan ID,
  plan-receipt file and record, collection file and record, and asset-manifest
  file identities. The pin itself is part of the remedy publication binding.
- Candidate streams, collection receipt, asset manifest, comparator, corpus,
  data root, selector, temporal contract, scientific terminals, and protected
  role firewall are unchanged.
- The replay script and its predecessor pin must be byte-identical to the new
  published `origin/main` head. R13R1 input records remain bound to their own
  earlier source commit; they are not rewritten to the remedy commit.

## Semantic authentication rule

Given `--semantic-plan` and `--plan-receipt`, reconstruction performs the same
operation as Lemhi toolkit v2:

1. copy the raw frozen plan;
2. remove optional `created_at`;
3. set `cluster_profile_sha256` from the authenticated receipt; and
4. set `provider_stack` from the authenticated receipt.

The canonical JSON SHA-256 of that result must equal
`plan_receipt.plan_id`. Only then may replay read
`semantic.evidence_allowlist` to authenticate collected evidence.

The input source commit must be an ancestor of the remedy publication head.
The asset manifest must match both the committed R13R1 input pin and the exact
`asset-manifest.json` bytes/size entry in the authenticated semantic plan.
Collection `present` and `absent` rosters must be individually unique,
disjoint, and together equal the complete semantic allowlist; sanitized-file
identities must be unique and equal exactly the `present` roster.

## Resources and exclusions

This is a local, pre-cleanup authentication and selector replay. It creates no
authority, reserves no compute, submits no scheduler job, performs no remote
cleanup, and opens no protected or confirmation role. It does not retrain,
regenerate, alter either architecture, or change the R13 selector.

## Exit

Run the authenticated two-pass replay against the uncleaned R13R1 collection.
If both selector outputs are byte-identical and all inherited scientific and
firewall checks pass, preserve its unchanged R13 terminal and emit a signed
R13R2 replay identity. Cleanup remains downstream of that receipt.

## Execution status

Published attempt 1 at `72b6513f46f1f06292c7672b90593679d5f8cbae`
failed before selector execution because the integer-only record parser was
also applied to legitimate float-valued science JSON. No cleanup occurred.
The failure and bounded parser correction are recorded in
[`execution-note.md`](execution-note.md).
