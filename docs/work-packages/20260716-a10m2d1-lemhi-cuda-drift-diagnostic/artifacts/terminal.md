# Terminal

`A10M2D1-ROOT-CAUSE-LOCALIZED`

A10M2D1 reproduced and localized both observed environment drifts. The CUDA
12.8 module is visible on login but not resolvable through cache-bypassed Lmod
on `node03`. More importantly, the Intel AVX-512 login host defaults to a
`linux-skylake_avx512` Spack GCC/runtime, while the AMD EPYC 7313 GPU node lacks
the tested AVX-512 features. That compiler dies before preprocessing on the
node, and its login-built RPATH-bearing executable dies there as well.

The unchanged CUDA smoke compiled and ran with both explicit OS GCC 8.5 and
advertised GCC 11.2, whether built on login or `node03`. All four valid
binaries saw exactly one L40 and passed the full numerical kernel check. The
driver/runtime and CUDA GNU-version guard are therefore not the failed
boundary.

Disposition: `EXECUTED-COMPLETE`. The simplest observed correction is direct
CUDA 12.8 plus explicit `/usr/bin/g++`; administrator support is not inferred.
One job used 5 requested GPU-minutes and six seconds of actual allocation, no
retry occurred, all evidence was retrieved, and the exact remote run was
removed. A10M2 remains immutable and A10M3 remains unauthorized.
