# Amendment 01 — compute-node module registry

Date: 2026-07-16 PDT
Applied before any second submission

## Evidence

J1 attempt `1013515` was accepted on `gpu-icrews`, received typed
`gpu:l40:1`, and was placed on `node03`. It failed at time zero before CUDA
execution because the compute node's Lmod registry did not know `cuda/12.8`,
although the login node advertised it from `/opt/modules/modulefiles`.

The advertised CUDA modulefile only prepends `/usr/local/cuda-12.8/bin` and
its `lib64`, TensorRT, and NCCL library directories. The advertised Python
3.11.11 modulefile similarly only prepends
`/opt/modules/devel/python/3.11.11/bin` and `lib`. The failure therefore
exposes a login/compute module-registry inconsistency, not a different software
selection.

## Frozen correction

- J1 uses the advertised canonical CUDA 12.8 installation directly and fails
  closed unless `nvcc` exists there.
- J2/J4 use the advertised canonical Python 3.11.11 installation directly and
  fail closed unless it exists.
- Versions, resources, numerical tests, pass rules, partition, and typed GRES
  do not change.
- Attempt `1013515` and its original source identity remain in the ledger.

This is a functional environment-bootstrap correction, not an exact transient
rerun. It is authorized by the package's recorded-amendment clause. Under
conservative requested accounting, failed J1 plus revised J1 and J2--J4b total
50 GPU-minutes (0.833 GPU-hour), still below the hard one-GPU-hour ceiling.
The amendment consumes the package's only retry allowance; no further J1 retry
is permitted.
