# Frozen diagnostic matrix

## Configuration IDs

| ID | Build side | CUDA selection | Host compiler | GPU-side action |
|---|---|---|---|---|
| M0 | login + node | `/opt/modules/modulefiles` | module-selected/ambient | Compare directory and cache-bypassed module statuses |
| C0 | login + node | direct CUDA 12.8 | ambient `g++` | Compile independently; run each successful binary |
| C1 | login + node | direct CUDA 12.8 | `/usr/bin/g++` (OS GCC 8.5) | Compile independently; run each successful binary |
| C2 | login + node | direct CUDA 12.8 | advertised GCC 11.2 `g++` | Compile independently; run each successful binary |

The source is byte-identical across C0--C2. No optimizer, architecture flag,
unsupported-compiler override, or source edit varies by configuration.

## Node inventory

D1 records only bounded fields: CPU model, family, socket/core/thread counts,
presence of AVX/AVX2/AVX-512 feature flags, kernel, CUDA device/driver/toolkit,
filesystem types, compiler resolved paths, version/status, internal `cc1`
path/status, and loader dependencies. It does not dump the environment.

## Interpretation rules

- Ambient fails by `SIGILL`; C1/C2 pass: localize failure to the ambient Spack
  compiler tree, with H2 versus H3 separated by CPU/features and probe results.
- C1 passes and C2 fails: prefer the OS-native compiler as observed workaround;
  do not call the advertised GCC module valid.
- C2 passes and C1 fails: identify advertised GCC 11.2 as the bounded working
  candidate; administrator support remains required.
- Prestaged passes while corresponding node build fails: support H6 and a
  build-host contract rather than node-local compilation.
- Node-built and prestaged binaries compile but all runtime checks fail:
  classify H8 false and use the driver/runtime hold.
- All explicit configurations fail: close honestly at no-compiler-path and
  provide exact administrator evidence.

One successful configuration is necessary but not sufficient for
`ROOT-CAUSE-LOCALIZED`; the report must explain the original failure to the
strongest evidence available and label remaining ambiguity.
