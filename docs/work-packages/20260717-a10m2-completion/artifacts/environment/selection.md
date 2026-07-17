# Offline framework selection

## Initial selection — rejected before installation

The published scaffold selected Python 3.11.11 and
`torch==2.7.1+cu128`. Its 25-wheel hash lock remains immutable in git commit
`8b7e751`. C1-01 failed before output or installation, and P0 then proved that
`/opt/modules/devel/python/3.11.11/bin/python` is absent on `node03` even
though it is visible on the login host. That lock is therefore ineligible for
compute use. Copying the login installation across the Intel/AMD boundary was
rejected because A10M2D1 already proved architecture-targeted login binaries
can die by `SIGILL` on `node03`.

## Active selection

- Compute Python: `/opt/modules/devel/python/3.8.11/bin/python3.8`, directly
  observed executable by P0.
- Compiler toolkit: `/usr/local/cuda-12.8`, with `/usr/bin/g++` via
  `nvcc -ccbin`.
- Framework: `torch==2.4.1+cu124`. The official CUDA 12.4 index publishes its
  CPython 3.8 Linux x86-64 wheel. Driver 610.43.02 is newer than the packaged
  CUDA 12.4 runtime; runtime viability remains a C1 measurement, not an
  inference.
- The PyTorch wheel declares the exact CUDA 12.4, cuDNN 9.1.0, NCCL 2.20.5,
  and Triton 3.0.0 dependency versions frozen here.

Resolver sources were limited to:

- `https://download.pytorch.org/whl/cu124`; and
- authoritative release files at `https://pypi.org/simple` for the exact
  NVIDIA/Triton versions declared by the PyTorch wheel.

The executor explicitly resolved Linux-only platform markers and Triton's
`setuptools` requirement, then replayed the 23-line lock with no index under
CPython 3.8 / Linux x86-64 constraints. The offline resolution passed.

## Frozen active assets

- 23 wheels; 2,884,771,888 bytes before tar framing;
- wheelhouse tar: 2,884,792,320 bytes,
  SHA-256 `0c87139ffd0886a4b7fbd66562e71ded7ab421ee8dcbe10e92c8a34bc366daf7`;
- corpus tar: 223,907,840 bytes,
  SHA-256 `7866833d79a22ebcc8d7cce4c61b5b2726a7cf4630e0e932769ba4289c1e9388`;
- `requirements.lock` pins every name/version/hash;
- `wheelhouse-manifest.json` pins filenames, byte counts, and hashes; and
- `license-metadata.json` records each distribution's embedded license-file
  inventory or metadata. Original license files remain inside the wheels.

Compute installation must use no index and must verify both the tar and every
wheel before `pip --require-hashes`. A successful node-local `pip check` is
still required.
