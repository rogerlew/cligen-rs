# Root cause and correction

## Root cause

The default compiler contract crosses incompatible CPU targets. The reachable
login host is Intel Skylake with AVX-512, and its ambient compiler/runtime is
installed under a `linux-skylake_avx512` Spack prefix. `node03` is AMD EPYC
7313 and lacks the tested AVX-512 features. On `node03`, the ambient GCC driver
and preprocessor die by `SIGILL`; a CUDA binary built with that compiler on the
login host also dies by `SIGILL` because it retains the Spack runtime through
RPATH.

CUDA 12.8, driver 610.43.02, the L40, the source, and the GNU version guard are
not the failing boundary. Both OS GCC 8.5 and advertised GCC 11.2 compile the
same source on both sides, and all four resulting binaries pass the complete
kernel smoke.

A separate configuration drift exists in Lmod: the alternative module
directory is present on `node03`, but cache-bypassed discovery and load cannot
resolve `cuda/12.8`, while the login host can show the modulefile. Direct CUDA
path selection is therefore required in the observed environment.

## Bounded operational correction

The simplest observed correction for a future authorized integration attempt
is:

```bash
/usr/local/cuda-12.8/bin/nvcc -ccbin=/usr/bin/g++ source.cu -o program
```

The advertised GCC 11.2 path also works when supplied explicitly. Neither
path is claimed to be the administrator-supported production contract;
administrative confirmation is still appropriate before longer A10 jobs.

## Administrator-ready actions

1. Expose a generic or Zen-compatible host compiler/runtime consistently on
   login and GPU nodes, or select compiler stacks by node architecture.
2. Prevent the `linux-skylake_avx512` default from reaching `node03`, including
   RPATH-bearing login-built executables.
3. Repair or remove the compute-node `/opt/modules/modulefiles` CUDA 12.8
   registry claim.
4. Update the GPU inventory, toolkit version, compile-host guidance, and
   explicit host-compiler selection in public examples.
5. Treat `Host compiler targets unsupported OS` as a secondary message when
   the host compiler has already died by signal 4.
