# Prospective design freeze

Frozen before the first allocation on 2026-07-17.

## Runtime and framework

- Runtime: `cpython-3.11.15+20260510-x86_64-unknown-linux-gnu-install_only.tar.gz`
- Runtime bytes: `48850850`
- Runtime SHA-256: `14b5843a3492925dab6fdb7cca7d09af83ddf1fe2851f72cf9b1edc8ed2b1db7`
- Runtime source: the `20260510` python-build-standalone GitHub release.
- Framework: `torch==2.7.1+cu128`, exact inherited 25-wheel Linux CPython 3.11
  closure from A10M2 completion scaffold commit `8b7e751`, rehashed here.
- Numerical extension: `numpy==2.2.6`, exact CPython 3.11 manylinux2014 x86-64
  wheel, SHA-256
  `ba10f8411898fc418a521833e014a77d3ca01c15b0c6cdcce6a0d2897e6dbbdf`.

The runtime is MPL-2.0-licensed. Wheel license provenance is retained inside
the hashed distribution archives; this package makes no relicensing claim.

## Resource and evidence boundary

- run/package ID: `a10-python311-smoke` /
  `a10-lemhi-python311-smoke`;
- confirmation classification: `development-only`;
- partition/GRES: `gpu-icrews` / `gpu:l40:1`;
- one attempt, 4 CPUs, 16,384 MiB, 20 minutes, one GPU;
- cumulative ceiling: 20 requested GPU-minutes;
- allowlist: `evidence.json`, `slurm/smoke.0.out`, and
  `slurm/smoke.0.err`;
- no retry, network, confirmation target, performance inference, or A10M3
  claim.

## Working hypotheses

H1: Lemhi's glibc 2.28 Linux x86-64 compute environment can execute the pinned
portable CPython artifact even though the advertised Python 3.11 module is not
visible on the compute node.

H2: the previously resolved CPython 3.11 / CUDA 12.8 PyTorch wheel closure,
augmented with NumPy, installs offline and is compatible with driver 610 and
one typed L40 allocation.

H3: avoiding ambient module/Spack state and using exact final prefixes prevents
the login/compute ISA and moved-venv traps observed in A10M2 and A10M2D1.

## Error traps

- Do not infer compute capability from the login probe; proof occurs only
  inside Slurm.
- Do not load advertised Python, compiler, or CUDA modules. Ambient Spack
  compiler state can select Intel AVX-512 binaries that die on AMD node03.
- Do not move a created virtual environment; its scripts embed the creation
  prefix.
- Do not resolve dependencies on Lemhi or permit pip index access in the job.
- Do not expose home paths, usernames, environment dumps, GPU UUIDs, or wheel
  installation logs in publication evidence.
- Do not accept Slurm `COMPLETED` alone; the toolkit must authenticate all
  booleans from the exact structured `evidence.json` gate receipt.
- Do not broaden allocation or retry after a failure. Collect the bounded
  evidence possible, clean exactly, and close at a registered hold.
