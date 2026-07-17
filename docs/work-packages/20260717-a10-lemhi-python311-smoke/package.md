# A10 Lemhi CPython 3.11 Smoke

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Mixed (local asset construction and live Lemhi execution)
Scaffold base: clean `main` at `cd537ce`
Execution branch and push target: `main`

## Objective

Prove that an agent operating from `rmm` can use the Lemhi toolkit to stage a
pinned portable CPython 3.11 runtime and fully hashed offline NumPy/PyTorch
closure, reconstruct it on an I-CREWS-priority one-L40 Slurm allocation, run a
bounded native/GPU smoke, collect sanitized evidence, and clean the exact run.
This is the final operational prerequisite before A10M3.

## Scope

Included:

- CPython 3.11.15 from the pinned `python-build-standalone` Linux x86-64,
  install-only artifact;
- NumPy 2.2.6 and PyTorch 2.7.1+cu128 with their exact offline wheel closure;
- standard-library, native-extension linkage, NumPy, NumPy/PyTorch interop,
  CUDA tensor/autograd, checkpoint/reload, and one-L40 gates;
- an exact final durable runtime prefix and scheduler-purged job-local wheel
  expansion;
- a single `gpu-icrews`, `gpu:l40:1`, 4-CPU, 16-GiB, 20-minute job with no
  retry; and
- toolkit-controlled probe, plan, staging, verification, submission,
  observation, collection, cleanup, and closure.

Excluded:

- performance or throughput claims, training, multi-GPU/NCCL, preemption,
  requeue, scientific evaluation, A10M3 execution, and confirmation data;
- administrator or system installation, cluster configuration changes, and
  module-based Python/CUDA claims; and
- network access from the compute job.

## Authority

- The operator explicitly directed execution of the Lemhi smoke package and
  grants agents authoring authority for the bounded repository and live
  workflow actions described here.
- The normative controller contract is
  [SPEC-LEMHI-AGENT-TOOLKIT](../../specifications/SPEC-LEMHI-AGENT-TOOLKIT.md).
- [A10M2 completion](../20260717-a10m2-completion/package.md) is authority for
  the observed L40/driver/CUDA and offline framework path; its abandoned
  CPython 3.11 wheel closure is reused only after fresh hash validation.
- [A10M2D1](../20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md) is
  authority for avoiding ambient Spack compiler/module state on compute.
- Confirmation classification is `development-only`; protected confirmation
  targets remain prohibited.

## Frozen design

See [design-freeze.md](artifacts/design-freeze.md). The portable runtime and
every wheel are content-addressed before remote use. The runtime is extracted
to a final Ceph prefix before `venv` creation; the environment is never moved.
The job clears Python and loader inheritance, uses `--no-index` and
`--require-hashes`, and records only allowlisted, path-sanitized evidence.

## Plan

1. Correct the foundation's live platform receipt and bind successful Slurm
   observation to the exact structured gate receipt.
2. Construct and verify the pinned runtime and 26-wheel closure on `rmm`.
3. Commit and push the immutable scaffold so live authority binds an exact
   source commit.
4. Use warm MFA SSH masters to run the complete toolkit lifecycle and one
   bounded L40 job.
5. Retrieve evidence, prove exact durable and job-local cleanup, close the
   toolkit run, run repository gates, and publish the terminal disposition.

## Gates

- interpreter reports exactly CPython 3.11.15 and ABI `cp311`;
- `ssl`, `sqlite3`, `ctypes`, `venv`, `subprocess`, and spawned
  `multiprocessing` work;
- representative native extensions resolve through `ldd` without a missing
  dependency;
- NumPy numerical operations and PyTorch/NumPy sharing pass;
- exactly one visible NVIDIA L40 is used by PyTorch;
- CUDA allocation, host/device conversion, autograd update, and
  checkpoint/reload pass;
- installation is offline and hash-locked, `pip check` passes, and inherited
  Python/loader paths are absent;
- the structured evidence gate is authenticated by the toolkit, all evidence
  is allowlisted/sanitized, and both job-local and exact remote cleanup pass;
- all 22 toolkit tests, `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10-LEMHI-PY311-SMOKE-READY` and every
gate above. A runtime/ABI incompatibility closes honestly at
`EXECUTED-HOLD-PYTHON311-PORTABILITY`; a framework/CUDA incompatibility at
`EXECUTED-HOLD-FRAMEWORK-ABI`; an authentication, transfer, scheduler, or
cleanup failure at the corresponding bounded operational hold. Beyond the two
prospectively frozen single-attempt runs below, no retry or broader resource
request is authorized by this package.

The first frozen run, source commit `1135a98`, used job `1013742` and failed
after 93 seconds because the test assumed the portable build's statically
linked `_sqlite3` module exposed `__file__`. Runtime extraction, venv creation,
the hash-locked 26-wheel installation, and `pip check` had already completed.
This is retained failed development evidence, not a Python portability hold.
The exact remote run was recovered and verified absent. The failure also
exposed that the foundation did not settle an exhausted failed matrix for
collection/cleanup; the corrective implementation and regression fixture are
part of revision 2.

Revision 2 is a prospective new toolkit run, not an automatic resubmission of
the exhausted Slurm intent. It removes only the invalid `_sqlite3.__file__`
assumption, retains native linkage proof through NumPy's compiled extension,
adds an atomic failure evidence receipt, and authorizes one fresh 20-minute
attempt under a fresh resource budget. Across both runs, the package ceiling is
40 requested GPU-minutes; there is still no retry within either frozen run.

## Artifacts

- `artifacts/design-freeze.md` — prospective versions, identities, budget,
  safety boundaries, and error traps;
- `artifacts/environment/build_assets.py` — deterministic local asset builder;
- `artifacts/environment/requirements.lock` — exact hash lock materialized by
  the builder;
- `artifacts/environment/wheel-manifest.json` — exact wheel identities
  materialized by the builder;
- `artifacts/jobs/smoke.sh` and `smoke.py` — bounded compute job; and
- `artifacts/execution.md` and `artifacts/toolkit/` — live receipts and final
  disposition, created during execution.
