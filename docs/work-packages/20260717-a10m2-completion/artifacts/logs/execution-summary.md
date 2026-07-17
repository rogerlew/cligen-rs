# Sanitized execution summary

Raw scheduler logs were retrieved in evidence archive
`7935de3f026e1e4932667ff0dfdc750b8cbc424ab500801438f8f56633a1c439`
and reduced here. Usernames, home paths, GPU UUIDs, spool paths, and temporary
operator paths are intentionally omitted.

## P0 / C1

```text
P0: Python 3.11.11 missing on node03
P0: /opt/modules/devel/python/3.8.11/bin/python3.8 executable
P0: /usr/local/cuda-12.8/bin/nvcc executable
P0: /usr/bin/g++ executable
P0: writable local root, no candidate collision, NVIDIA L40 / driver 610.43.02

C1-02: visible_gpu_count=1
C1-02: NVIDIA L40, driver 610.43.02, 46068 MiB
C1-02: CUDA build 12.8 / GCC 8.5.0
C1-02: durable_fs_type=ceph / local_fs_type=xfs
C1-02: device_count=1 / compute_capability=8.9
C1-02: element_count=1048576 / checksum=5241856 / max_error=0
C1-02: wheelhouse_verified=23 / pip_check=pass
C1-02: PyTorch 2.4.1+cu124 / CUDA runtime 12.4 / cuDNN 90100
C1-02: loss 2.034698009490967 -> 1.6283613443374634
C1-02: framework_smoke=pass / stage2=pass / job_local_cleanup=pass
```

## C2

```text
C2-01: two L40s visible; stale relocated-venv torchrun shebang; no import
C2-02: visible_gpu_count=2; two distinct GPU UUIDs (redacted)
C2-02: NCCL 2.20.5+cuda12.4
C2-02: all_reduce=3.0 / backend=nccl / world_size=2
C2-02: device_names=[NVIDIA L40, NVIDIA L40]
C2-02: DDP loss=0.22476643323898315 / identical parameters / clean shutdown
C2-02: c2=pass
```

PyTorch warned that an available NumPy installation could not initialize. The
warning persisted after `PYTHONPATH`/user-site isolation. NumPy is not declared
by the PyTorch wheel, no test converted through NumPy, `pip check` passed, and
all registered tensor/DDP checks passed. It is retained as a downstream trap,
not silently treated as a passing NumPy integration.

## C3

```text
C3a: NVIDIA L40
C3a: Slurm USR1 checkpoint at step 29
C3a: checkpoint digest=16be3fcac9f06705414fc5c5fdcf555b392c051ddf3bc65a000bf8e7f5bca9d6
C3a: expected exit=75:0 / checkpoint=pass
C3b: checkpoint_step=29 / target_step=180
C3b: final_state=4580124774000342882
C3b: final_digest=4e7bb12bb23a6a3049aa29f412c3e3a27b6f766e88d1de9c51728d776bb03eff
C3b: resumed state and digest equal uninterrupted control / c3b=pass
```
