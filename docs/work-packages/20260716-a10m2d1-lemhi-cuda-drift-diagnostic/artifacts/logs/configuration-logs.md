# Sanitized configuration logs

## Compile outcomes

All three login compiles and the C1/C2 node compiles emitted only:

```text
nvcc warning : Support for offline compilation for architectures prior to '<compute/sm/lto>_75' will be removed in a future release (Use -Wno-deprecated-gpu-targets to suppress warning).
```

C0 node compile emitted:

```text
nvcc warning : Support for offline compilation for architectures prior to '<compute/sm/lto>_75' will be removed in a future release (Use -Wno-deprecated-gpu-targets to suppress warning).
nvcc error   : 'gcc' died due to signal 4 (Illegal Instruction)
nvcc error   : 'gcc' core dumped
nvcc fatal   : Host compiler targets unsupported OS.
```

C0 login-built execution emitted:

```text
timeout: the monitored command dumped core
```

## Passing kernel runs

C1 login-built, C1 node-built, C2 login-built, and C2 node-built each emitted:

```text
device_count=1
device_name=NVIDIA L40
compute_capability=8.9
element_count=1048576
checksum=5241856
max_error=0
cuda_smoke=pass
```

## Compiler versions

```text
system: g++ (GCC) 8.5.0 20210514 (Red Hat 8.5.0-28)
advertised: g++ (GCC) 11.2.0
ambient: status 132 before version output
```

The passing system and advertised `cc1` binaries resolved their dependencies
from `/lib64`. The ambient `cc1` on login resolved MPC, MPFR, GMP, and zstd
from `linux-skylake_avx512` Spack prefixes. The C0 executable likewise loaded
Spack `libstdc++` and `libgcc_s`; C1/C2 loaded both from `/lib64`.
