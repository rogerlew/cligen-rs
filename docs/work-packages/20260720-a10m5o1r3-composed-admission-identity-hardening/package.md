# A10M5O1R3 — Composed Admission Identity Hardening

Status: `EXECUTED-COMPLETE`
Date: 2026-07-20
Evidence mode: Local toolkit fixtures only; no HPC allocation
Starting branch and push target: current `main`, push `main`

## Objective

Extend the provider-v2 admission materialization contract so a plan can name
an ordered composition of checker assets and toolkit `submit` can authenticate
that exact composition from plan through prepare, stage, and the current-state
admission receipt. This removes the implicit assumption that every admission
controller is a single file named `admission_checker.py`.

R14R2 exposed the gap without submitting a job. Its outer
`admission_checker.py` authenticated occupancy and delegated to a distinct
`inherited_admission_checker.py`. Both assets were independently hash-pinned
and remotely verified, but the admission contract could not express their
relationship. The inherited checker consequently compared its own bytes to
the outer wrapper's logical plan entry and failed closed.

## Additive contract

The existing `admission_materialization` object gains one optional namespaced
object:

```json
"checker_assets": {
  "protocol": "ordered-plan-assets-v1",
  "logical_names": [
    "admission_checker.py",
    "inherited_admission_checker.py"
  ]
}
```

Absence retains the historical single/unmodeled behavior and does not
reinterpret old plans or receipts. When present, `checker_assets` is non-empty,
ordered, duplicate-free, and every member must be a frozen executable plan
asset. Order is semantic: entrypoint/wrapper first, followed by each delegate
in invocation order. Adding, removing, reordering, renaming, or changing a
member changes the semantic plan identity.

The package materializer publishes this exact projection in every covered
admission receipt:

```json
"input_identities": {
  "checker_assets": {
    "protocol": "ordered-plan-assets-v1",
    "assets": [
      {"logical_name": "admission_checker.py", "bytes": 1, "sha256": "..."},
      {"logical_name": "inherited_admission_checker.py", "bytes": 1, "sha256": "..."}
    ]
  }
}
```

While holding the run lock and before reservation, `submit` reconstructs the
ordered projection from the current semantic plan and requires exact equality
with the receipt. It also requires the same identities in current local files,
private prepared assets, and promoted transfer receipts. A stale, reordered,
omitted, duplicate,
renamed, non-executable, locally changed, transfer-record changed, or receipt-only
checker fails before ledger reservation and `sbatch`.

## Scope

Implementation is confined to the toolkit contract validator and admission
receipt authentication path in `research/a10/lemhi_toolkit/core.py`, plus
fixtures and specification text. The SCP adapter already stages and verifies
every logical asset independently; no transport or remote-shell change is
needed. Historical records remain immutable.

No R14 science, resource plan, model, objective, calendar, selector, or
confirmation surface changes. No HPC allocation is authorized or required.

## Exit criteria

`A10M5O1R3-COMPOSED-ADMISSION-IDENTITY-READY` requires all positive and adverse
fixtures, the complete toolkit suite, repository gates, specification update,
and an independent review with no unresolved finding. Only then may the
deferred R14R2R1 successor inherit this contract.

## Disposition

Reached `A10M5O1R3-COMPOSED-ADMISSION-IDENTITY-READY`. All 86 toolkit tests,
20 remote-shell syntax checks, JSON and diff checks, and repository Rust gates
passed without an allocation. The independent implementation disposition is
recorded in `scaffold-review.md`; detailed commands and terminal scope are in
`artifacts/gate-results.md` and `artifacts/execution-disposition.md`.
