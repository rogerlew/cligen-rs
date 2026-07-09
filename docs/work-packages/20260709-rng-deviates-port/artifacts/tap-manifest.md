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

## Stage C build and direct vectors

```
gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math \
  -I. cligen.f stage-c-vector-driver.f -o cligen532-stage-c-tap
GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0
```

- Base source SHA-256 (vendored, unmodified):
  `3dfd51db98fedfbfb155d4227099cf9133043d4d699093268ed21ce16ec4267c`.
- Stage C patch SHA-256:
  `7e42fffa77d7c8338f43cb1b384a1fe7675aca590f536026c24fe5499ba70502`.
- Patched copied source SHA-256:
  `4600f60035391c238d875cc9938957993e648a51bf979eb6c652112609fc98c0`.
- Direct-vector driver SHA-256:
  `505948aa1d75c835f2ee4d2039881345b9bb8ef6c754f8188ae6c184ee732e90`.
- Stage C tap binary SHA-256:
  `0b94dc7993e30b168775c4818150e51df0942934923f9d1636c1dbadcae4e996`.
- `fixtures/taps/stage-c-vectors.tap`: 919 lines, SHA-256
  `ec85fb6e586220b28a3626e551fa7a6ab03bdaaf2bba45b959433ce359ebd5f3`.

Ran: the additive instrument was first exercised across all 12 fixture
commands, with every generated `.cli` byte-identical to its committed golden.
After the final direct-vector additions, `new-meadows-id-seed0` was rerun and
`cmp` again returned exit 0; the direct-vector hash above is that final run.

## Stage C full `ranset` captures

| Case | Lines | Calls | SHA-256 |
|---|---:|---:|---|
| fish-springs-ut-observed-padded-seed0 | 2016 | 84 | `6b398fcc235206d547a13123d4a628d78a5527cc0c59003763485abe2e6b124f` |
| fish-springs-ut-observed-padded-seed17 | 2016 | 84 | `43b050f190c890d56671d17e9d13aef4253fa685956f5ce42d77fdb533309dec` |
| fish-springs-ut-observed-truncated-seed0 | 1896 | 79 | `6b039247876d1213d1445a30f429570420779b5d7c2bb8691692c37279a113e5` |
| fish-springs-ut-observed-truncated-seed17 | 1896 | 79 | `ce07129aed4a8133adefe8c918fa5b731411db812d79ec68dfa3c2be18758b0b` |
| jeogla-au-seed0 | 12096 | 504 | `42d58d58c4d18ddd84f9f23d519a4bc5a341f60ba2b55cbcb7dab37267e86dc1` |
| jeogla-au-seed17 | 12096 | 504 | `0ff22d6d94c9a36cf6430cff7eb7bd93507f21744c2aa0e55f999e5bd287966c` |
| mt-wilson-ca-observed-seed0 | 6048 | 252 | `f85daa5e193d651391fe607fd4a85b1c6e91977f08d727883b48d181d286af28` |
| mt-wilson-ca-observed-seed17 | 6048 | 252 | `32c48270d3be017efc071cb73e4a2e0a238455da36e03fa86096ca15ff692bf8` |
| new-meadows-id-seed0 | 8928 | 372 | `49a8cd72710514e157b116bc644c101bf3f90eb62ea39ca7819e2a948b4e4dd0` |
| new-meadows-id-seed17 | 8928 | 372 | `b56280c034effa24e3057214fe74fadb67234c27a3c3319a9a9d5406b53a2ab2` |
| new-meadows-id-single-storm-seed0 | 24 | 1 | `d233409f329854f5236958572540aaf179873c27ae9050fcdb962120adc93802` |
| new-meadows-id-single-storm-seed17 | 24 | 1 | `0cc70ff8742c18f9912d9dcb79c224e0f282aad9edeed9383586819df4f0d23c` |

Total: 2,584 calls. Committed samples contain the first 12 complete records
per regular case and the complete one-record single-storm streams (122 calls,
856 KiB total). The full files remain under the gitignored `tap-runs/` tree
and are exercised by the ignored release evidence gate.
