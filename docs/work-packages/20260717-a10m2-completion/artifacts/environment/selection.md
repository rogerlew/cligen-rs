# Offline framework selection

Selected prospectively after A10M2D1 proved the corrected CUDA compiler path
and before the first completion-package allocation.

## Compatibility basis

- Lemhi live runtime: driver 610.43.02 and CUDA toolkit 12.8.
- Compute ABI: Linux x86-64, glibc 2.28, Python 3.11.11.
- Selected framework: `torch==2.7.1+cu128`, whose official CUDA 12.8 index
  publishes a CPython 3.11 `manylinux_2_28_x86_64` wheel.
- The wheel's Linux metadata declares the exact CUDA 12.8, cuDNN 9.7.1,
  NCCL 2.26.2, and Triton 3.3.1 dependency versions frozen here.

Resolver sources were limited to:

- `https://download.pytorch.org/whl/cu128` for the PyTorch CUDA wheel and
  general dependency links; and
- authoritative release files at `https://pypi.org/simple` for the exact
  NVIDIA/Triton versions declared by that wheel.

The macOS resolver initially omitted dependencies guarded by Linux platform
markers. That result was rejected. The executor explicitly resolved the
Linux-only metadata, added Triton's `setuptools` requirement, and then replayed
the 25-line hash lock with no index under CPython 3.11 / manylinux x86-64
constraints. The offline resolution passed.

## Frozen assets

- 25 wheels; 3,849,130,961 bytes before tar framing;
- wheelhouse tar: 3,849,154,560 bytes,
  SHA-256 `70dfe50e90a20b1a773baa8186be4df1dc34606176181612c3086f10b389890a`;
- corpus tar: 223,907,840 bytes,
  SHA-256 `7866833d79a22ebcc8d7cce4c61b5b2726a7cf4630e0e932769ba4289c1e9388`;
- `requirements.lock` pins every name/version/hash;
- `wheelhouse-manifest.json` pins filenames, byte counts, and hashes; and
- `license-metadata.json` records each distribution's embedded license-file
  inventory or metadata. The original license files remain inside the hashed
  wheels used for reconstruction.

Compute installation must use no index and must verify both the tar and every
wheel before `pip --require-hashes`. A successful `pip check` is still required
on the allocated compute node.
