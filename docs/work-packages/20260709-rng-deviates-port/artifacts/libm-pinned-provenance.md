# `libm_pinned` Provenance

Evidence mode: Static upstream inspection + Ran fixture adjudication
(2026-07-09).

## Upstream identity

- Repository: `https://github.com/ARM-software/optimized-routines.git`
- Commit: `e17e986041ac820069515b25b89919278a53bb82`
  (2026-06-29, `math/aarch64/advsimd: Implement correctly rounded expf`)
- License declared by the upstream files: `MIT OR Apache-2.0 WITH
  LLVM-exception`.
- Complete upstream license: `arm-optimized-routines-LICENSE.txt`, SHA-256
  `650afbf29f214451e02241adc42534e82c9d6ae2b38e2444b92b5a1ffcaf9346`.

The Rust module is a direct algorithm/constants transcription from ARM
upstream. It does not copy from the LGPL glibc carrier; glibc 2.39 was only
the runtime whose results supplied the Stage S reference observations.

## Source files

| Upstream file | SHA-256 | Rust surface |
|---|---|---|
| `math/logf.c` | `f12013b42b8c73f6879cd9b83364bd859812c17fb0b432605666aea267723e0f` | `logf_pinned` control flow |
| `math/logf_data.c` | `5262907466c069677dd0690de5d1919a31c72fef5f57aa78e217a94b389494af` | `logf_pinned` table/polynomial |
| `math/cosf.c` | `84068b509762ae5c3ba4f1488f73cce099ffbbf1df3f410aa1c7538562d41b4c` | `cosf_pinned` control flow |
| `math/sincosf.h` | `ae5b8962056f72fa9f844b980bed0c50a3612f96e7a17629eb10e6c9b428463b` | range reduction/polynomial helpers |
| `math/sincosf_data.c` | `9887da2fb996658a88e98ec7ea5142be2b4a8db5650f7fd3290228d67d405cdb` | sine/cosine coefficients |
| `math/exp.c` | `219b5f666c84864e80ef5ef33bc5453b4702ea74fc5cbf997c3dfacdcf5738cf` | `exp_pinned` control flow |
| `math/exp_data.c` | `a5e84677e7693c7d22195f86faac5fdc6f92bff7ea2e54c0e7888203a78ffc24` | `exp_pinned` table/polynomial |

## Empirical adjudication

- Ran: Stage S compared `logf_pinned`/`cosf_pinned` through all 26,402,148
  captured `dstn1` calls. There were zero result-bit divergences. The `libm`
  crate alternatives diverged on 1,975,439 `logf` inputs and 334,643 `cosf`
  inputs.
- Ran: Stage C direct ACM vectors found `libm::exp(-10)` one ULP below the
  Fortran/reference-runtime result through `gratio(8, 10, 0)`. The pinned
  ARM scalar binary64 `exp` restored exact identity. The final vector fixture
  exercises all ACM callers of the function, including `erf`, `erfc1`,
  `gamma`, `gratio`, and `rexp` branches.
- Ran: f64 `pow` and `dstg`'s narrower `exp` domain remain on the locked
  `libm` crate because the 30,268-record full `dstg` replay is bit-identical.

R1 disposition: provenance and licensing are accepted after replacing the
ambiguous “MIT via glibc” note with direct ARM attribution, exact upstream
identity, copyright notice, SPDX expression, and the complete upstream
license in the package artifacts.
