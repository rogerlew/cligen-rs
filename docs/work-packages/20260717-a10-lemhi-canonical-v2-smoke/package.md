# A10 Lemhi canonical v2 bounded smoke

Status: `EXECUTED-HOLD`
Date: 2026-07-17
Evidence mode: Live, after separate operator dispatch
Starting branch and push target: current `origin/main`, push `main`

## Objective

Validate immutable candidate `lemhi-a10-py311-l40-v2-candidate` at semantic
SHA-256 `5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`
on one Lemhi L40 under the revision-2 toolkit. Produce a separate immutable
smoke attestation without editing the candidate or canonical v1.

## Dispatch boundary

Scaffolding authorizes repository files and local verification only. A later
explicit operator dispatch authorizes VPN/warm-master use, exact staging, one
primary `gpu-icrews` allocation, conditional exact-node recovery, evidence
collection, and exact cleanup. It does not authorize A10M5, development or
confirmation target access, administrator changes, interactive automation, or
direct compute-node SSH.

## Frozen resources

- primary: one `gpu:l40:1`, 4 CPUs, 16,384 MiB, 15-minute limit;
- recovery contingency: at most one exact-node `gpu:l40:1`, 2 CPUs, 1,024
  MiB, 5-minute limit, submitted only for authenticated
  `CLEANUP_INCOMPLETE`;
- cumulative requested ceiling: 20 L40-GPU-minutes;
- maximum concurrency: one allocation; no requeue and no retry; and
- partition: `gpu-icrews` only.

The primary reservation includes the recovery contingency before submission.
Ambiguous scheduler or cleanup state retains the reserve and stops.

## Required gates

1. Verify the candidate semantic hash, profile hash, seven v2 provider hashes,
   runtime, wheelhouse, Rust toolchain, and vendor identities before staging.
2. Initialize one authority/ledger anchor, reconcile the immutable authority
   token, and run only from an immutable derived run revision.
3. Reconstruct from `--export=NONE`; prove exact runtime/compiler paths,
   absence of prohibited ambient Python/loader state, and
   `CUBLAS_WORKSPACE_CONFIG=:4096:8` before Python import.
4. On compute, validate CPython 3.11.15, stdlib/native linkage, NumPy 2.2.6,
   PyTorch 2.7.1+cu128, exactly one L40, CUDA tensor/autograd/checkpoint, and
   offline installation.
5. Validate Rust 1.92.0 `cargo` plus `rustc`, target standard library,
   `/usr/bin/g++`, loader resolution, exact source/vendor relationship,
   `cargo metadata --locked --offline`, and a bounded locked offline build.
6. Admit the marked job-local root using expanded bytes/inodes, products,
   checkpoint, fixed margin, and minimum-free floor. Exercise normal and
   catchable-failure supervisor paths; publish durable status before exact
   cleanup and prove absence.
7. Record integer transfer telemetry and immediately revalidate any skipped
   identity. SCP partials cannot be represented as resumed.
8. Authenticate `RAW_COLLECTED` before typed publication projection. Confirm
   gates are identical across the projection receipt and no private path,
   identity, endpoint, or unrestricted environment reaches publication.
9. Retrieve and verify all allowlisted evidence, prove exact durable and
   job-local cleanup, settle all scheduler records, and remove the exact remote
   run root.

## Terminal

`A10-LEMHI-CANONICAL-V2-SMOKE-READY` requires every gate and an immutable
`lemhi-canonical-smoke-attestation-1` binding the candidate hash. It does not
designate the candidate current. The next package is a local-only canonical
designation-index revision.

Any failed gate, unavailable accounting, incomplete cleanup, unexpected
allocation, identity drift, or ceiling issue yields the exact hold and no
attestation. A failed smoke cannot mutate the candidate, designation, or v1
and cannot fall back to v1 storage semantics.

## Scaffold gate

Run:

```sh
python3 docs/work-packages/20260717-a10-lemhi-canonical-v2-smoke/artifacts/verify-scaffold.py
```

## Result

Terminal: `HOLD-A10-CANONICAL-V2-SMOKE-ENVIRONMENT-CLOSURE`

The bounded primary allocation failed before job-local root creation or Python
import because at least one prohibited ambient Python/loader variable was
present on entry despite Slurm `--export=NONE`. The exact-node recovery
allocation proved `JOB_LOCAL_ABSENT`; both scheduler records settled and the
marker-bound durable run root was removed. No smoke attestation or designation
was created. A10M5 remains held.
