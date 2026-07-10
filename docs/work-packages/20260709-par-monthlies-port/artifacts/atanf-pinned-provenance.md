# `atanf_pinned` Provenance and Notice Resolution

Evidence mode: Static upstream inspection + Ran fixture adjudication
(2026-07-09).

## Source identity

- Runtime/source carrier: GNU C Library 2.39 release tarball,
  `https://ftp.gnu.org/gnu/glibc/glibc-2.39.tar.xz`.
- Tarball SHA-256:
  `f77bd47cf8170c57365ae7bf86696c118adb3b120d3259c64c502d3dc1e2d926`.
- Source file: `sysdeps/ieee754/flt-32/s_atanf.c`; SHA-256:
  `cc8a6b8845df93191e1ec3c4c95e8fc58daae14b52bfe795c2c81b0989ee4646`.
- Algorithm origin cross-check: Netlib fdlibm `s_atan.c`,
  `https://www.netlib.org/fdlibm/s_atan.c`. The 11-term odd/even
  polynomial and four argument-reduction intervals are the same source
  family specialized to REAL*4 by `s_atanf.c`.

The Rust code transcribes the control flow and constants from the glibc
2.39 float source because that is the reference host's runtime behavior.
The glibc carrier is not used as the license assertion for this unit:
glibc's `LICENSES` file separately identifies the Sun fdlibm files and
reproduces their permissive notice.

## Notice (preserved in `libm_pinned.rs`)

Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.

Developed at SunPro, a Sun Microsystems, Inc. business.
Permission to use, copy, modify, and distribute this software is freely
granted, provided that this notice is preserved.

R1 disposition: accepted. The grant expressly permits use, copying,
modification, and distribution subject to notice preservation; the full
notice now appears in the Rust module header. This replaces the Stage S
placeholder that named the origin but left the provenance review open.

## Empirical adjudication

- `libm::atanf` was rejected after a captured `fouri1` composition differed
  by one ULP at input bits `0xBE794977`.
- The 11-term transcription matched the system `atanf` on the recorded
  56,253,020-input C sweep and 3,721,018-pair Rust sweep.
- The committed full-matrix `sta_parms` snapshot gate verifies every
  `fouri1` composition for four stations × 14 parameters × six harmonics.

The behavioral evidence is detailed in `gate-results.md`; this artifact
resolves source identity and notice preservation only.
