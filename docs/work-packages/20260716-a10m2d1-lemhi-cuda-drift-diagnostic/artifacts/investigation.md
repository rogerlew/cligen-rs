# Pre-scaffold investigation

Date: 2026-07-16 PDT
Evidence mode: Ran plus documentation comparison

## Observed A10M2 failures

1. Job 1013515 was allocated on `node03` with typed `gpu:l40:1`, then failed at
   time zero because compute-node Lmod did not know `cuda/12.8` after
   `module use /opt/modules/modulefiles`.
2. Job 1013516 bypassed Lmod and reached `/usr/local/cuda-12.8/bin/nvcc`. It
   saw one NVIDIA L40, driver 610.43.02, and CUDA build
   `cuda_12.8.r12.8/compiler.35583870_0`. `nvcc` then reported that host
   `gcc` died by signal 4 (`SIGILL`), core dumped, and targeted an unsupported
   OS. No kernel was built or run.

These are separate boundaries: module resolution failed first; the later
compiler crash occurred only after direct CUDA-path selection.

## Live compiler/module findings

- The CUDA 12.8 modulefile only prepends `/usr/local/cuda-12.8/bin` and CUDA,
  TensorRT, and NCCL library paths. It selects no host compiler.
- The ambient `gcc` resolves into a Spack prefix named
  `linux-skylake_avx512` and reports GCC 12.5.0.
- Its internal `cc1`, MPC, MPFR, GMP, and zstd dependencies resolve from the
  same architecture-named Spack tree.
- The reachable login host is an Intel Xeon Gold 6148 (Skylake) and advertises
  AVX-512 features, so that tree runs there.
- Slurm exposes `node03` as x86-64, two sockets, 64 logical CPUs/32 cores, four
  L40s, 512 GB, and Linux 4.18, but does not publish its CPU model or flags.
- ELF notes do not declare a decisive x86-64 ISA level for the GCC driver or
  `cc1`; the architecture-target inference therefore remains a hypothesis.
- `/usr/bin/gcc` reports Red Hat GCC 8.5.0. The alternative module tree
  advertises GCC 11.2.0 at `/opt/modules/devel/gcc/11.2.0`.
- Both explicit compilers run preprocessing probes on the login host.
- CUDA 12.8's installed host guard rejects GNU versions later than 14; GCC
  8.5, 11.2, and 12.5 are therefore within the installed version guard. The
  observed message is not evidence of a simple GCC-version rejection.

## Documentation drift clues

The public GPU guide records CUDA 12.2, two L40s on each of `node03` and
`node04`, and a successful historical `node03` vector-add result. Live state
instead exposes CUDA 12.8, four L40s on `node03`, and four RTX A6000s on
`node04`. The guide instructs users to compile CUDA on `staging1` and execute
the resulting binary in Slurm, while another C3+3 page says the Lemhi server
should be used for compilation because its processor generation matches the
compute nodes.

The current Ollama guide still claims `/opt/modules/modulefiles` is available
on GPU nodes and loads Python from it inside `sbatch`. That is inconsistent
with job 1013515. The general Getting Started module hierarchy documents an
older Core GCC layout, while the current ambient compiler comes from a newer
Spack production tree.

## Leading interpretation

The leading explanation is that login/staging software and documentation
evolved without a fully synchronized GPU-node module/compiler contract. The
ambient Spack compiler may additionally be CPU-targeted or dependency-targeted
for the login host and unsuitable on `node03`. This is an inference, not yet a
root-cause finding; A10M2D1 is designed to falsify it.
