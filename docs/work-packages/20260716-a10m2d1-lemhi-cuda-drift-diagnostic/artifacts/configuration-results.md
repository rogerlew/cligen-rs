# Configuration results

## Allocation and platform

- D1 job `1013558` completed `0:0` in six seconds on `node03`.
- Slurm exposed exactly one NVIDIA L40 with 46,068 MiB, driver 610.43.02,
  compute capability 8.9, and CUDA 12.8 V12.8.93.
- `node03` was an AMD EPYC 7313 system with AVX and AVX2 but without the four
  tested AVX-512 feature groups.
- The login host was Intel Xeon Gold 6148 and exposed all four tested AVX-512
  feature groups.

## Matrix outcome

| ID | Login compile | Node compile | Login-built run | Node-built run | Result |
|---|---:|---:|---:|---:|---|
| C0 ambient Spack GCC 12.5 | pass | `SIGILL`/fail | `SIGILL` | not produced | Invalid across the node boundary |
| C1 OS GCC 8.5 | pass | pass | pass | pass | Working observed configuration |
| C2 advertised GCC 11.2 | pass | pass | pass | pass | Working observed configuration |

Every passing run emitted the same result:

```text
device_count=1
device_name=NVIDIA L40
compute_capability=8.9
element_count=1048576
checksum=5241856
max_error=0
cuda_smoke=pass
```

The C0 login-built binary embedded an RPATH to the
`linux-skylake_avx512` GCC 12.5 runtime and loaded `libstdc++.so.6` and
`libgcc_s.so.1` from that prefix. C1 and C2 had no such RPATH and loaded those
libraries from `/lib64`. The ambient compiler driver and preprocessing both
returned 132 on `node03`; `/usr/bin/g++` and the advertised GCC 11.2 driver,
preprocessor, and internal `cc1` probes all returned zero.

The exact faulting instruction or member of the ambient runtime was not
captured. The controlled CPU-feature, compiler, RPATH, and executable outcomes
are sufficient to localize the operational root cause to the
architecture-targeted ambient toolchain/runtime rather than CUDA, the L40, or
the smoke source.
