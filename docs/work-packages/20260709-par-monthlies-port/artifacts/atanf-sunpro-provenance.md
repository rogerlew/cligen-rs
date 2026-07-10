# `atanf_pinned` License and Lineage Provenance

Evidence mode: Ran (2026-07-09) — every file fetch, diff, and sweep
below was executed this session; hashes and counts are from those runs.
Resolves the Stage S open item "atanf_pinned SunPro license provenance"
(spine-handoff.md); Stage R1 verifies this record rather than
performing the adjudication.

## Why this record exists

`libm_pinned::atanf_pinned` is transcribed from glibc 2.39's
`sysdeps/ieee754/flt-32/s_atanf.c` because that is what the reference
runtime executes (the pinned fixture builds link the system libm; the
`libm` crate's `atanf` was rejected on captured 1-ULP evidence —
gate-results.md). glibc as a project is LGPL-2.1+, and this repository
is Apache-2.0 with a no-GPL/LGPL policy, so the transcription's true
origin had to be established rather than assumed. `cargo deny` cannot
see source transcriptions — this document is the enforcement.

## Lineage (verified against fetched sources)

1. **Sun fdlibm** — `s_atan.c`, double precision, Copyright (C) 1993
   Sun Microsystems under the SunPro permissive notice ("Permission to
   use, copy, modify, and distribute this software is freely granted,
   provided that this notice is preserved."). SPDX recognizes this
   notice as the `SunPro` license.
2. **Float conversion** — "Conversion to float by Ian Lance Taylor,
   Cygnus Support" (header of the NetBSD file), under the preserved
   Sun notice. The same conversion also ships in newlib
   (`newlib/libm/math/sf_atan.c`, fetched and checked this session).
3. **NetBSD** — `src/lib/libm/src/s_atanf.c` rev 1.4 (1995-05-10,
   jtc). This exact revision is the rcsid glibc still carries
   (`$NetBSD: s_atanf.c,v 1.4 1995/05/10 20:46:47 jtc Exp $`).
   Fetched: `https://cvsweb.netbsd.org/bsdweb.cgi/~checkout~/src/lib/libm/src/s_atanf.c?rev=1.4`,
   SHA-256 `3cc3ad28fca91d98397fdfa9981f19538080576796903e9b12e95f0cd44254af`.
4. **glibc 2.39** — `sysdeps/ieee754/flt-32/s_atanf.c`. Fetched:
   `https://sourceware.org/git/?p=glibc.git;a=blob_plain;f=sysdeps/ieee754/flt-32/s_atanf.c;hb=glibc-2.39`,
   SHA-256 `cc8a6b8845df93191e1ec3c4c95e8fc58daae14b52bfe795c2c81b0989ee4646`.
   (glibc replaced this file with a CORE-MATH implementation *after*
   2.39 — commit `a357d627` in the file's history — so future host
   glibc upgrades change runtime `atanf` behavior; `atanf_pinned`
   pins the 2.39/fdlibm behavior the golden fixtures were built
   against.)

## Diff adjudication: NetBSD 1.4 vs glibc 2.39

The transcribed arithmetic surface is **identical** between the two,
verbatim: all three constant tables with their original decimal
literals and comments (`atanhi`, `atanlo`, the 11-term `aT` —
including the stale `/* 0x3eaaaaaa */` comment on `aT[0]`, which is
therefore Sun/NetBSD-era, not glibc's; the compiled constant is
`0x3EAAAAAB`), the small/reduction thresholds (`0x31000000`,
`0x3ee00000`, `0x3f300000`, `0x3f980000`, `0x401c0000`), all four
reduction formulas, the odd/even polynomial split, and both tail
combinations. glibc's remaining deltas are scaffolding the
transcription does not carry (`math_check_force_underflow`,
`libm_alias_float`, include plumbing, `__STDC__` cleanup).

**Exactly one arithmetic-surface element is glibc-original**: the
huge-argument threshold, `0x50800000` (2^34) in NetBSD 1.4 →
`0x4c000000` (2^25) in glibc. Origin pinned:

- Commit `9a71f1fcf53615c00b5f9e5da4bba92bccb0efb4`, Joseph Myers,
  2015-05-14, first released in glibc 2.22 (`glibc-2.22~322`),
  Bugzilla #18196 — "Fix atanf spurious underflows": the reduction
  path computes x^-4-scale intermediates that raise spurious underflow
  for large arguments; the fix returns ±π/2 directly from 2^25 up.
- Newlib's permissively-licensed copy still carries 2^34 (checked this
  session), so the 2^25 constant has no permissive carrier — its
  origin really is this glibc commit.
- The change is **not result-inert**: compiled side-by-side (both
  `-O2`, no FMA — matching the reference host, whose CPU has no
  FMA/AVX2 so the ifunc resolves the plain SSE2 build), NetBSD 1.4
  and system glibc diverge by 1 ULP on 277,032 of 32,604,782 swept
  inputs in ±[2^25, 2^34]: glibc's early return yields
  `float(atanhi[3]+atanlo[3])` = `0x3FC90FDB`, while NetBSD's
  reduction path is correctly rounded to `0x3FC90FDA` in the low
  sub-band where π/2 − 1/x still rounds down. Faithful mode follows
  the reference runtime, so the transcription carries glibc's
  constant.

**License disposition of the one glibc element**: a single integer
threshold constant selected for a documented functional property
(avoid spurious underflow; return the ±π/2 approximation once the
1/x correction is sub-half-ULP) is a functional/factual element, not
copyrightable expression — there is no creative choice to protect,
and the value is dictated by the mathematics (merger). Every element
of protectable *expression* in `atanf_pinned` traces to the
Sun/NetBSD original under the SunPro notice. Disposition: accepted,
with this record as the audit trail; R1 reviews the reasoning.

## Notice preservation

The SunPro grant's sole condition is notice preservation. Satisfied
at two sites:

- `crates/cligen/src/libm_pinned.rs` module header (copyright line +
  grant text + carrier citation);
- `artifacts/fdlibm-sunpro-LICENSE.txt` (this package), the notice
  verbatim with its scope.

## Behavioral verification of the transcription (Ran)

Rust `atanf_pinned` vs the reference runtime's `atanf` (system glibc
2.39, SSE2 ifunc), inputs dumped by a `-fno-builtin` C driver and
compared bit-for-bit:

| Band | Inputs | Mismatches |
|---|---:|---:|
| ±[2^-31, 2^26), step 0x101 | 3,721,018 | 0 |
| ±[2^25, +∞], step 0x1001, incl. exact ±inf and the 0x4C000000 boundary | 421,788 | 0 |
| NaN payloads (qNaN/sNaN, both signs) | 3 | NaN-out asserted |

Plus the C-level cross-check already in gate-results.md (glibc source
compiled locally vs system libm: 56,253,020 inputs, 0 mismatches) and
the composition gate (all snapshot `t`/`c` values bit-exact).

## Probe hazard, recorded for every future adjudication

GCC constant-folds libm calls through MPFR at `-O2` — including
**peeled first iterations of loops** — substituting *correctly
rounded* results that legitimately differ from glibc's runtime
behavior (e.g. exactly at 2^25, MPFR gives `0x3FC90FDA`, runtime
glibc `0x3FC90FDB`). This contaminated two probes this session (a
constant-input probe and the first record of a pair-dump) before
being caught by cross-checks. Rule: **every C probe of reference
libm behavior must be runtime-opaque** — inputs via argv/file, built
with `-fno-builtin` — and pair dumps should be spot-checked against
an argv-driven probe at boundary values.
