# Tap Capture Manifest

Evidence mode: Ran (2026-07-09).

## Build

```
gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math -I. cligen.f -o cligen532-tap
GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0
```

- Patched source `tap-build/cligen.f` SHA-256: 8a773a65ffeb30e4722afd64bf6c3861c7122a3d3461cdaccf2bbe07a4a8d2fe
- Patch: `tap-patch.diff` (99 lines, additive only)
- Tap binary SHA-256: d57fa53f094c3622b5fb3349b73ae1d924ed835d60765ab2740796eedb8c7db1
- Base source = vendored reference (unmodified); reference dir untouched.

## Non-invasiveness gate

All 12 patched-binary runs produced `wepp.cli` byte-identical to the
committed goldens (cmp, per-case IDENTICAL results in the execution log).

## Tap files (full captures, local under gitignored tap-runs/)

| Case | rn lines | n1 lines | dg lines | rn SHA-256 | dg SHA-256 |
|---|---:|---:|---:|---|---|
| fish-springs-ut-observed-padded-seed0 | 38200 | 54419 | 1068 | `59831cefc0587a6f…` | `13a1089bef6acd57…` |
| fish-springs-ut-observed-padded-seed17 | 1241714 | 54692 | 1088 | `a554ba7e6b3cde13…` | `458f6ca1b0ba447c…` |
| fish-springs-ut-observed-truncated-seed0 | 36646 | 52063 | 1038 | `a415bd56806ca168…` | `7d31b6700dbeb435…` |
| fish-springs-ut-observed-truncated-seed17 | 939643 | 51380 | 1038 | `29c71a5123dfcfb8…` | `cdd63c3b6952466e…` |
| jeogla-au-seed0 | 223062 | 271083 | 6634 | `542646b02d7be45f…` | `d5f2835774c0e877…` |
| jeogla-au-seed17 | 10549401 | 19338003 | 6850 | `86e0104b61304358…` | `3635ecca2a6c17e2…` |
| mt-wilson-ca-observed-seed0 | 132028 | 196544 | 1430 | `da3ada2a4fa866ac…` | `9b7b235c1a57f0cb…` |
| mt-wilson-ca-observed-seed17 | 5593092 | 5710265 | 1430 | `51c328b16ce4a678…` | `09af007a4134a7a3…` |
| new-meadows-id-seed0 | 545783 | 447193 | 4822 | `359283b3410dd04e…` | `0408e8b07708e558…` |
| new-meadows-id-seed17 | 484467 | 225404 | 4870 | `a32416974cef5570…` | `1e1aba21c562a735…` |
| new-meadows-id-single-storm-seed0 | 392 | 569 | 0 | `909fb59dfcb438f0…` | `e3b0c44298fc1c14…` |
| new-meadows-id-single-storm-seed17 | 527 | 533 | 0 | `cadd5b8f2604abc9…` | `e3b0c44298fc1c14…` |

Committed for in-repo tests (`fixtures/taps/`): full `dg.tap` per case
(empty single-storm dg omitted) and the first 1,000 records of each
rn/n1 stream. Full-stream verification runs `#[ignore]`-gated against
tap-runs/ and is recorded in gate-results.md.
