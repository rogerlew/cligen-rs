# Live execution inventory

Date: 2026-07-16 PDT
Evidence mode: Ran

## Access and scheduler

- Both human-bootstrapped SSH control masters were live immediately before
  staging. All execution commands used `BatchMode=yes`.
- Slurm version: 25.05.6.
- The account association is eligible for `gpu-icrews`; group `icrews` is
  allowed there.
- `gpu-icrews` is tier 20 and covers `node03`/`node04`; `gpu-volatile` is tier
  10. No preemption was deliberately triggered.
- The user job inventory was empty before J1 and after cleanup.

## Allocation and device

- Both J1 attempts were accepted on `gpu-icrews` with typed `gpu:l40:1` and
  placed on `node03`.
- The amended attempt saw exactly one NVIDIA L40, 46068 MiB, driver 610.43.02.
- `node03` reports four configured L40s, x86-64, 64 configured CPUs/62
  effective CPUs, 512000 MB configured memory, and Linux
  4.18.0-553.137.1.el8_10.

## Software and storage

- Login Lmod advertises CUDA 12.8 and Python 3.11.11 from
  `/opt/modules/modulefiles`; compute-node Lmod did not know `cuda/12.8`.
- Direct CUDA inventory reported build
  `cuda_12.8.r12.8/compiler.35583870_0`.
- The login CUDA modulefile only adds the canonical CUDA 12.8 installation
  paths. The amended job used that installation directly.
- `nvcc` started but its host `gcc` died with `SIGILL`, core dumped, and was
  classified by `nvcc` as targeting an unsupported host OS.
- The login tree advertises GCC 11.2 at a separate canonical installation;
  that compiler was not tested because the retry/resource allowance was
  exhausted.
- The durable working filesystem reported Ceph. The job's `TMPDIR` reported
  XFS, establishing a node-local-or-temporary distinct filesystem without
  claiming a documented `SLURM_TMPDIR`.
