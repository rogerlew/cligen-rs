# A10M2D1 — Lemhi CUDA Environment Drift Diagnosis

Status: `EXECUTED-COMPLETE`
Date: 2026-07-16
Evidence mode: Mixed
Scaffolding authorization: operator direction on 2026-07-16 from clean
`main` at `1f8d24e5353a936c205f5c265e38e7a3b47bb3ec`, targeting `main`

## Objective

Localize why the currently advertised Lemhi GPU module/compiler workflow no
longer reproduces the documented successful CUDA path, and identify at least
one explicit, supportable configuration that compiles and runs the unchanged
A10M2 CUDA smoke on `node03`. Distinguish documentation drift, module-registry
drift, CPU/ISA incompatibility, architecture-specific dependency failure, and
host-compiler selection without treating a workaround as an administrator-
supported production environment.

## Scope

Included:

- compare current C3+3 documentation with timestamped login and compute-node
  state;
- inventory module visibility, modulefile content, CPU model/features, CUDA
  driver/toolkit, ambient compiler resolution, compiler internal executables,
  and dynamic dependencies on both sides of the Slurm boundary;
- compile the same CUDA source with the ambient compiler, OS GCC 8.5, and the
  advertised GCC 11.2 on the reachable login host and on `node03`;
- execute every successfully produced binary on one typed L40 allocation;
- test the documented compile-before-submit pattern separately from
  compute-node compilation;
- retain exact commands, versions, hashes, statuses, sanitized logs,
  accounting, review, and an administrator-ready root-cause summary; and
- issue a bounded correction recommendation for A10M2 without reopening its
  immutable terminal record.

Excluded:

- PyTorch, NCCL/DDP, checkpoint/restart, model training, or A10 data;
- performance or portability claims beyond the observed hosts;
- `--allow-unsupported-compiler`, `-march=native`, compiler replacement,
  modulefile edits, package installation, or administrator-owned changes;
- direct SSH to a compute node outside a Slurm allocation;
- deliberate preemption, confirmation-series access, or production Rust
  changes; and
- credentials, usernames, unrestricted environment dumps, or absolute user
  paths in committed evidence.

## Authority

- [A10M2 terminal](../20260716-a10m2-lemhi-gpu-integration/artifacts/terminal.md)
  requires a newly authorized package for another submission.
- [A10M2 J1 evidence](../20260716-a10m2-lemhi-gpu-integration/artifacts/j1-result.md)
  is the immutable failure baseline.
- [C3+3 GPU guide](https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html),
  [Getting Started](https://docs.c3plus3.org/docs/help/Getting_Started/), and
  [Ollama example](https://docs.c3plus3.org/docs/help/Tutorials/Ollama.html)
  are claims to test, not assumed live truth.
- Timestamped live host/Slurm evidence outranks stale documentation where they
  conflict.

## Frozen resource envelope

| Job | Partition and GRES | CPU / memory / time | Purpose |
|---|---|---|---|
| D1 | `gpu-icrews`, `gpu:l40:1`, `node03` | 2 CPU, 8 GB, 5 min | Complete comparison matrix |

Base use is 5 requested GPU-minutes. At most one exact rerun invalidated by a
documented infrastructure transient may add 5 GPU-minutes. The hard ceiling is
10 requested GPU-minutes (one-sixth GPU-hour). A compiler/configuration edit is
not an exact rerun and requires a published amendment before submission.

## Plan

1. Freeze the source commit, predecessor identity, hypotheses, comparison
   matrix, commands, pass rules, sanitization, and 10-GPU-minute ceiling.
2. Verify the existing MFA-bootstrapped SSH masters and refresh read-only
   module/partition/node state. Stop for human bootstrap if either master is
   absent.
3. Run `jobs/prestage.sh` on the reachable Lemhi login host. Compile the
   unchanged smoke independently with ambient, OS, and advertised compilers;
   retain statuses and hashes but do not attempt GPU execution there.
4. Submit D1 once. Record `node03` CPU identity/features, module-path
   existence and `--ignore_cache` results, CUDA device/driver, resolved ambient
   GCC/`cc1`, dependencies, and compiler probes with core dumps disabled.
5. In the same allocation, compile independently with ambient GCC, explicit
   `/usr/bin/g++`, and explicit advertised GCC 11.2. Continue after individual
   failures, then execute every successful node-built and prestaged binary.
6. Retrieve and sanitize evidence; map observations to the registered
   hypotheses; classify documentation claims; account resources; clean the
   exact remote run; review; run repository gates; and close with one terminal.

## Execution & dispatch

Scaffolded on `main` at
`1f8d24e5353a936c205f5c265e38e7a3b47bb3ec`; push target is `main`. This
scaffold performs no remote write or Slurm submission. Execution requires a
kickoff naming the then-current published `origin/main`, approving the
10-GPU-minute ceiling, and confirming that `A10M2D1` is diagnostic authority
only.

MFA remains human-supervised. Automation may use only existing SSH control
masters with `BatchMode=yes`; it never receives or stores password/Duo
material.

Executed from clean published `main` at
`3bc543f2404bc6a2d6ab81931f6eb7e9eb033029` on 2026-07-16. D1 job
`1013558` completed in six seconds with one L40 and no retry. The package
closed at `A10M2D1-ROOT-CAUSE-LOCALIZED`; see `artifacts/terminal.md`.

## Gates

- all hypothesis tests and configuration IDs are frozen before remote staging;
- D1 is the only base submission and every individual probe has an explicit
  status even when another probe crashes;
- core files are disabled and no unsupported-compiler override is used;
- at least the ambient, OS GCC 8.5, and advertised GCC 11.2 paths are tested on
  both the login/staging side and `node03`, or their absence is proven;
- every successfully compiled binary is hashed and run on the allocated L40;
- conclusions distinguish observed fact, inference, and untested alternative;
- documentation claims are classified as current, drifted, contradictory, or
  untestable from available authority;
- submitted resources do not exceed 10 GPU-minutes;
- logs contain no credentials, usernames, absolute user paths, or unrestricted
  environment dumps;
- review has zero open P1/P2 findings;
- shell passes `bash -n` and applicable static checks;
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass; and
- coverage/CRAP is not triggered unless a production function changes.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10M2D1-ROOT-CAUSE-LOCALIZED`: the
matrix identifies a reproducible compile/run path, explains the failed ambient
path to the strongest evidence available, and produces a bounded A10M2
correction plus an administrator-ready drift report. A working explicit
compiler does not by itself certify that configuration as institutionally
supported.

Legitimate holds are:

- `EXECUTED-HOLD-NODE-INTROSPECTION` — D1 cannot obtain the registered node
  evidence;
- `EXECUTED-HOLD-NO-COMPILER-PATH` — none of the three bounded compiler paths
  can compile and run the smoke;
- `EXECUTED-HOLD-DRIVER-RUNTIME` — compilation succeeds but no retained binary
  runs on the allocated L40; or
- `EXECUTED-HOLD-RESOURCE-BOUND` — diagnosis cannot complete within 10
  requested GPU-minutes.

## Artifacts

- `artifacts/investigation.md` — pre-scaffold observations and drift evidence.
- `artifacts/hypotheses.md` — ranked working hypotheses and falsifiers.
- `artifacts/test-matrix.md` — frozen configuration comparison and decisions.
- `artifacts/jobs/` — unchanged CUDA smoke, login prestage, and D1 scripts.
- `artifacts/README.md` — execution artifact registry.
- `kickoff-prompt.md` — bounded execution dispatch template.
