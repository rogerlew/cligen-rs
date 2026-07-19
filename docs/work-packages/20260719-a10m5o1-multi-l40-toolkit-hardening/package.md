# A10M5O1 — Multi-L40 Toolkit Hardening

Status: `EXECUTED-COMPLETE`
Date: 2026-07-19
Evidence mode: Mixed
ExecPlan: [`../../exec-plans/20260719-a10-multi-l40-qualification.md`](../../exec-plans/20260719-a10-multi-l40-qualification.md)

## Objective

Make multi-GPU Slurm requests safe and auditable by enforcing one exact typed
GRES count across the plan, Slurm submission, resource reservation, settled
accounting, and recovery paths before any multi-L40 live allocation occurs.

## Scope

Included are typed-GRES parsing, one-to-four homogeneous L40 validation,
primary/recovery count equality, multi-GPU resource-ledger fixtures, toolkit
specification and README changes, deterministic local tests, and repository
gates. Excluded are live allocation, canonical designation changes, scientific
model work, cross-node execution, and heterogeneous GPUs.

## Authority

The operator's 2026-07-19 instruction authorizes repository authoring and
end-to-end execution of the linked multi-GPU packages from `main`, pushing only
`main`. `SPEC-LEMHI-AGENT-TOOLKIT` revision 2 remains normative. Agents have
authoring authority for package-owned code, tests, specifications, plans, and
evidence within this scope.

## Plan

1. Freeze the GRES/count/accounting defect and additive capability boundary.
2. Add one parser and fail-closed equality/capacity validation for primary and
   recovery jobs.
3. Add adverse mismatch and valid one/two/four-GPU ledger fixtures.
4. Update specifications, toolkit guidance, and examples.
5. Run package, toolkit, shell, and repository gates and issue a terminal.

## Execution and dispatch

Execute in `/Users/roger/src/cligen-rs` on `rmm`, starting from current
`origin/main` and pushing only `main`. This package performs no remote mutation
or allocation. Its published terminal commit is the source prerequisite for
A10M5O2.

## Gates

- mismatched `gpus`/`gres` fails at plan time before adapter mutation;
- non-GPU, untyped, non-L40, zero, and greater-than-four GRES fail closed;
- valid counts 1, 2, and 4 pass and settle correct GPU-seconds/minutes;
- recovery count equality and charge are enforced;
- toolkit unit tests, remote shell syntax, package verifier,
  `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered because this package changes no production
function under `crates/`.

## Exit criteria

`A10M5O1-MULTI-L40-TOOLKIT-READY` requires every gate and authorizes the frozen
A10M5O2 live package to consume the published implementation. Any mismatch,
accounting, provider, or test defect produces an exact `EXECUTED-HOLD` and no
live allocation.

## Artifacts

- `artifacts/design-freeze.md` — defect, invariants, and exclusions;
- `artifacts/verify.py` — deterministic package verifier;
- `artifacts/gate-results.md` — populated during execution; and
- `artifacts/execution-disposition.md` — terminal record.

## Disposition

Reached `A10M5O1-MULTI-L40-TOOLKIT-READY`. The toolkit now parses the typed
GRES once for resource, model, and count; authenticates it against the selected
provider; requires the same count in the ledger multiplier for primary and
recovery jobs; and rejects counts above the provider maximum. The existing
provider remains capped at one. The additive provider accepts one, two, or four
L40s on one node. All 55 toolkit tests, shell syntax, package verification, and
repository gates passed without a live allocation.
