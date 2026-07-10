# Daily-Core Transcendental Census and §1.3 Adjudication

Evidence mode: Static census (full source reads) + Ran adjudication
(2026-07-09; sweep methodology per the item-4 `atanf` record —
`-fno-builtin` argv-safe C pair dumps of the system libm, compared
bit-for-bit from Rust).

## Census (all four units)

| Unit | Site | Function | Argument domain (source-derived) | Disposition |
|---|---|---|---|---|
| `clgen:1186` | `sin((xi-80.25)/pit)` | f32 `sin` | \|arg\| ≤ ~5 | `sinf_pinned` (item 4, already adjudicated) |
| `clgen:1187` | `tan(sd)` | f32 `tan` | \|sd\| ≤ 0.4102 | **NEW → `tanf_pinned`** |
| `clgen:1194` | `acos(ch)` | f32 `acos` | \|ch\| < 1 (clamped at 1189-1192 before the call) | **NEW → `acosf_pinned`** |
| `clgen:1197,1200,1202` | `sin(sd)`, `cos(sd)`, `sin(h)` | f32 `sin`/`cos` | \|sd\| ≤ 0.4102; h ∈ [0, π] | pinned (item 3/4) |
| `clgen:1255,1324,…` | `**3`, `**2`, `sqrt`, `abs` | — | — | integer powers expand to multiplies (gfortran -O0); `sqrtf` IEEE-exact; no pinning |
| `windg` | (none — `dstn1` internal only) | — | — | — |
| `alphb:3852` | `exp(-tmax/ei)` | f32 `exp` | arg ∈ (−4.93, 0) | **NEW → `expf_pinned`** |
| `r5monb:3975` | `alog(f)` | f32 `log` | f ∈ (0, 2) | `logf_pinned` (item 3; covers all positive normals) |

`dstn1`/`dstg` interiors were adjudicated in item 3.

## Adjudication of the three new functions (Ran)

Reference = the system libm the golden/tap binaries link (glibc 2.39,
non-FMA SSE2 ifunc resolution on the pinned host). Candidate-first
policy per standard §1.3:

| Function | `libm` crate candidate | Verdict |
|---|---|---|
| `tanf` | 7,872,386 swept, **162,240 mismatches (2.06%)** | REJECTED |
| `acosf` | 8,290,688 swept, **6,597,515 mismatches (79.6%)** — diverges even at x = 0 | REJECTED |
| `expf` | 8,551,812 swept, **59,396 mismatches (0.69%)** | REJECTED |

Pinned transcriptions from the fetched glibc 2.39 sources (file
SHA-256s: `e_expf.c` `13c0e69d…801cd16`, `e_exp2f_data.c`
`f93dbc47…b90e65`, `e_acosf.c` `60a8c9b2…800d8ba`, `s_tanf.c`
`02f13627…c29733`, `k_tanf.c` `acd2297f…928d8`), every constant's bit
pattern verified against the compiled decimals (all source comments
honest this time — checked anyway per the `aT[0]` lesson):

| Function | Origin | Sweep result |
|---|---|---|
| `tanf_pinned` | fdlibm `k_tanf.c` 13-term kernel, `s_tanf.c` fast path only (generator domain \|x\| ≤ 0.4102 < π/4; carried domain \|x\| < 0.6744, reduction branches fail closed) | 7,833,328 in-domain, **0 mismatches** |
| `acosf_pinned` | fdlibm `e_acosf.c`, open interval \|x\| < 1 (clgen clamps `ch` before the call; \|x\| ≥ 1 fails closed) | 8,290,688, **0 mismatches** |
| `expf_pinned` | ARM optimized-routines `e_expf.c` (N=32, `__exp2f_data`), plain f64 internals, no contraction; \|x\| ≥ 88 fails closed | 8,551,812, **0 mismatches** |

Sweep domains: tanf ±[2^-31, 0.75] step 0x41; acosf ±[0, 1) step
0x101; expf ±[0, 16] step 0x101 — each a superset of the generator's
reachable arguments.

## License lineage

`tanf`/`acosf` are fdlibm/SunPro via NetBSD float conversions (rcsids
in the fetched sources), the same notice lineage adjudicated for
`atanf` in item 4 (`atanf-pinned-provenance.md`,
`fdlibm-sunpro-LICENSE.txt` — the notice covers these transcriptions
identically and is already preserved in the module header). `expf` is
ARM optimized-routines (MIT OR Apache-2.0 WITH LLVM-exception), the
same upstream as the item-3 `logf`/`cosf`/`exp` transcriptions whose
provenance Stage R1 of item 3 recorded. R1 of this package verifies
both mappings.
