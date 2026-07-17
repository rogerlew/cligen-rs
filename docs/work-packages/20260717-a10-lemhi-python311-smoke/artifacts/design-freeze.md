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
- revision-1 ceiling: 20 requested GPU-minutes;
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

## Revision 2 prospective correction

The first run exhausted its one attempt on a test-harness assumption:
`_sqlite3` is statically linked in the selected portable runtime and therefore
has no `__file__`. Before another allocation, revision 2 removes only that
invalid native-path member; NumPy's compiled `_multiarray_umath` remains the
native `ldd` gate. It also makes a failed job emit an atomic structured failure
receipt and makes the controller settle an exhausted failed role so evidence
and exact cleanup remain reachable.

Revision 2 uses a new run ID and new 20-GPU-minute budget. The package-wide
ceiling is therefore 40 requested GPU-minutes across two single-attempt runs.
No scientific, confirmation, performance, multi-GPU, or training scope is
added.

## Revision 3 prospective correction

Revision 2's aggregate smoke reached all environment-dependent gates but the
harness did not publish their individual values before exiting. Static
arithmetic localizes its known failure: the matrix product was computed before
the shared NumPy tensor changed `array[0,0]`, so `product[0,0]` is 5, not 121.
Revision 3 corrects only that expected value and publishes individual gate
values before aggregate failure. It uses a third distinct run and fresh
20-GPU-minute budget, bringing the package ceiling to 60 requested GPU-minutes.
No fourth run is authorized.
