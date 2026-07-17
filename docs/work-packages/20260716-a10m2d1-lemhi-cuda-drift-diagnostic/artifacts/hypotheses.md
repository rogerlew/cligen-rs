# Working hypotheses

Ranked before execution. D1 must report every test even if an earlier
configuration fails.

| ID | Working hypothesis | Discriminating evidence | Falsifier |
|---|---|---|---|
| H1 | `/opt/modules/modulefiles` is absent, stale, or unregistered on `node03` although advertised on login/staging hosts. | Directory identity, `MODULEPATH` membership, `module --ignore_cache is-avail/show/load` statuses on both sides. | The same modulefile is readable and loads successfully on `node03`. |
| H2 | Ambient Spack GCC/`cc1` or a dependency was built for `linux-skylake_avx512`, while `node03` lacks a required instruction. | `node03` CPU model/flags plus isolated driver, `cc1`, and preprocessing statuses; explicit generic compilers survive. | `node03` has the required ISA and all ambient compiler probes run, or the crash persists identically with generic compilers. |
| H3 | The architecture-specific Spack compiler tree is corrupt or dynamically incompatible on `node03`, independent of CPU flags. | `file`, hashes where readable, `ldd`, loader resolution, and isolated dependency/compiler behavior versus login. | Ambient compiler and dependencies run normally when invoked outside `nvcc`. |
| H4 | CUDA 12.8 plus OS GCC 8.5 is a viable node-local compile/run path. | Explicit `nvcc -ccbin=/usr/bin/g++`, binary hash, and unchanged kernel result. | Compile or runtime fails under an otherwise valid L40 allocation. |
| H5 | CUDA 12.8 plus advertised GCC 11.2 is a viable node-local compile/run path and the intended missing compiler selection. | Explicit GCC 11.2 probes, compile, binary hash, and kernel result. | Compiler is absent/crashes or produced binary fails. |
| H6 | The historically documented compile-before-submit pattern remains viable even when compute-node compilation is not. | Login-built binaries from each available compiler execute on `node03`; compare with node-built outcomes. | Prestaged binaries fail for toolchain/loader reasons or node builds behave identically. |
| H7 | The `Host compiler targets unsupported OS` line is a secondary `nvcc` diagnostic after `SIGILL`, not an actual GNU version-guard rejection. | Installed guard accepts GNU <=14; explicit supported compilers work; ambient compiler fails before normal preprocessing. | A surviving compiler invocation reaches a precise CUDA OS/version rejection. |
| H8 | Driver/runtime is healthy once a valid host binary exists. | Every valid binary sees one L40 and passes allocation, transfer, kernel, synchronization, copy-back, and numerical checks. | Compilation succeeds but all binaries fail at CUDA runtime/device gates. |

H2 is the leading hypothesis, but it cannot be accepted solely from the Spack
directory name. H1 already has one observation but must be reproduced with
cache bypass and directory checks. H4/H5/H6 are configuration hypotheses, not
claims of institutional support.
