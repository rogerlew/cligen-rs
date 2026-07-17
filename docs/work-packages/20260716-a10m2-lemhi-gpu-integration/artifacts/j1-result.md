# J1 CUDA result

Disposition: FAIL — CUDA environment

## Gates established

- Slurm accepted the typed `gpu:l40:1` request on `gpu-icrews` twice.
- Amended J1 saw exactly one NVIDIA L40 with driver 610.43.02 and 46068 MiB.
- CUDA toolkit identity was 12.8, build
  `cuda_12.8.r12.8/compiler.35583870_0`.
- Durable working storage was Ceph; temporary storage supplied through
  `TMPDIR` was XFS.

## Failed gate

The CUDA smoke did not compile. Attempt 1013515 failed because compute Lmod
could not resolve the login-advertised module. After published Amendment 01,
attempt 1013516 reached `nvcc`, whose host `gcc` died by signal 4 (illegal
instruction), core dumped, and produced `Host compiler targets unsupported
OS.` No allocation/transfer/kernel/result assertion executed.

This is a hard J1 failure under the frozen rules. It is not evidence that the
L40 or CUDA driver is unusable, but it is sufficient evidence that the current
documented compile environment is not compute-ready for A10.

Exact sanitized output is retained in `logs/`. Scheduler receipt:

```text
1013515|a10m2-j1|gpu-icrews|FAILED|1:0|00:00:00|00:10:00|2|8G|node03
1013516|a10m2-j1|gpu-icrews|FAILED|1:0|00:00:01|00:10:00|2|8G|node03
```
