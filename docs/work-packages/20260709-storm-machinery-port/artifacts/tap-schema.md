# Tap Schema + Capture Manifest — Storm Machinery (Stage S)

Evidence mode: design (Static) + capture (Ran, 2026-07-09). Item-3/4/5
constraints inherited (additive patch, copied tree, Z8.8 EQUIVALENCE).

## Build

```
gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math -I. cligen.f -o cligen532-storm-tap   (exit 0)
GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0
```

- Base cligen.f (vendored, unmodified) SHA-256: 3dfd51db98fedfbfb155d4227099cf9133043d4d699093268ed21ce16ec4267c
- Patch tap-patch.diff (75 lines, additive) SHA-256: c6b08a6f60ad28017e118fe46c213cb887c6a5e76d53a05fe6a6d698917575f5
- Patched cligen.f SHA-256: bd5a29368be2e89775fe7e6569b7060fdb86e3504f5ba6f1f8fc0e0bf9738645
- Tap binary SHA-256: a0c273e1d4329eb240612f16ed4ef727b36ac5c577f72a5c65760c7d6f35a7ce

## Streams

### `cligen_sd.tap` — unit 83, two records per day inside day_gen

- `D Z(dur(mo,jd)) Z(r1)` — after the wet-day duration block
  (`cligen.f:3114-3127`), both branches (dry: dur = 0; `r1` is stale
  on dry days — replay ignores it there).
- `S jd mo iyear Z(xr) Z(dur) Z(tpr) Z(xmav)` — immediately before the
  unit-7 row write (`cligen.f:3175`), i.e. after the full chain incl.
  the iopt-4/7 overrides. This is the `.cli` daily-row numeric seam.

### `cligen_tp.tap` — unit 84, one record per `timepk` call

`T iopt dax k10(4i5) Z(z) Z(timepk)` — entry `iopt`/`dax`/`k10`, the
drawn/batch uniform, and the result. `iopt = 6` records advance `k10`
(fresh `randn`); all others read `zx(dax)` and leave `k10` untouched.

## Capture matrix and non-invasiveness (Ran)

The standard 24-run matrix (12 golden + 12 capture-only interp
variants). **All 12 golden `.cli` outputs byte-identical (12/12)**;
24/24 runs exit 0. Counts cross-check: tp records = wet days = ab
records / 2 (e.g. new-meadows-seed0: 2,411); sd lines = 2 × cg days.
Single-storm sd decodes to the exact iopt-4 override values
(xr = damt·25.4 = 57.15, dur = usdur = 6.0, tpr = ustpr = 0.4,
xmav = 4.0), pinning the transient-∞ path end-to-end.

## Committed samples vs local full captures

`fixtures/taps/storm/<case>/`: the 10 replay cases with first-500-day
`sd-sample.tap` (1,000 lines) and first-500-record `tp-sample.tap`
(sequential prefixes). Full streams local under gitignored
`tap-runs/`, digests below; full-stream verification is the
`#[ignore]` evidence gate.

## Full-capture digests (per case: sd/tp SHA-256)

### fish-springs-ut-observed-padded-I0
- sd: 5114 lines `cf02a2bc90474bf4da64f66eb25ad0d3d374720bfc48f3f9ff4cc280af0e4a9b`
- tp: 534 lines `5fd497babe7df8abadcd13c6282f63cbcf22f9972d2d6e416761567b2aebcfe5`
### fish-springs-ut-observed-padded-I1
- sd: 5114 lines `d7ff17041c54d669c04a357c686eb805ac4dc3b9c6328d8ff79408d3e5bf0f0d`
- tp: 534 lines `5fd497babe7df8abadcd13c6282f63cbcf22f9972d2d6e416761567b2aebcfe5`
### fish-springs-ut-observed-padded-I3
- sd: 5114 lines `7235dbc6504e795596bed6933d663cf89672105498f0532e8ca181a6ba03ed7a`
- tp: 534 lines `5fd497babe7df8abadcd13c6282f63cbcf22f9972d2d6e416761567b2aebcfe5`
### fish-springs-ut-observed-padded-seed0
- sd: 5114 lines `823c1bafaa0d4ccc117de07caaaab1374cd0a540842eff8c803adbdcec6b8dfb`
- tp: 534 lines `5fd497babe7df8abadcd13c6282f63cbcf22f9972d2d6e416761567b2aebcfe5`
### fish-springs-ut-observed-padded-seed17
- sd: 5114 lines `8dc19f84aeecf7bd5a201ad928c051fd86d5a76f6d98209758fb912a761f3bad`
- tp: 544 lines `5d967084ed4b160025db963b5315e077793d25cde64d532041016eeb318fefb6`
### fish-springs-ut-observed-truncated-seed0
- sd: 4760 lines `ad5a557030aae83256e4dd0c10482c2acf5fd2627b8f828b8608a885615ed6b8`
- tp: 519 lines `6ffa65e1268829f73c9fc85cbbfb717223768a5ca8d6813ced244212027bb152`
### fish-springs-ut-observed-truncated-seed17
- sd: 4760 lines `be2cb9401087bf402d1108ac40d85da288375d9290ffda765b71c081876a1023`
- tp: 519 lines `6ffa65e1268829f73c9fc85cbbfb717223768a5ca8d6813ced244212027bb152`
### jeogla-au-I1
- sd: 30680 lines `144f4e122157f8ed38e21fa218a1906bb8a0b4be42e3c2b217099063195ad804`
- tp: 3317 lines `e1a07dfebc90afa8014106f11b640e97effc348f75a90776e4f36c5849a2d844`
### jeogla-au-I2
- sd: 30680 lines `47b18cc40b26ecff2aa62093949bd5fd3651e87002db53ca58c25dd8eae1252a`
- tp: 3317 lines `e1a07dfebc90afa8014106f11b640e97effc348f75a90776e4f36c5849a2d844`
### jeogla-au-I3
- sd: 30680 lines `61b04f0a3b8b6b738e26bf8171e3eabd4d7b44b259964cb0babb952e879d4f88`
- tp: 3317 lines `e1a07dfebc90afa8014106f11b640e97effc348f75a90776e4f36c5849a2d844`
### jeogla-au-seed0
- sd: 30680 lines `3dafd0ccd678408f8785a1e4412cfb230529da1f09223e308fd3ab8d362047d3`
- tp: 3317 lines `e1a07dfebc90afa8014106f11b640e97effc348f75a90776e4f36c5849a2d844`
### jeogla-au-seed17
- sd: 30680 lines `b90cced54c5f60361a78063fed403cf061e0d3267e818d4a59724060225d3a50`
- tp: 3425 lines `b7fb7805d0c1c8c802344978d410b628e745b0f3cff2d596c05d5717f213cc47`
### mt-wilson-ca-observed-I0
- sd: 15340 lines `37454c025ca2b7e1280c913dabff28cf02bf31c8338d7cf17d1c8272f98b51f7`
- tp: 715 lines `0ad2b8417f794f4583931587a75ea8157b7d0c144e6f3cee4620a16ce2faa680`
### mt-wilson-ca-observed-I1
- sd: 15340 lines `37454c025ca2b7e1280c913dabff28cf02bf31c8338d7cf17d1c8272f98b51f7`
- tp: 715 lines `0ad2b8417f794f4583931587a75ea8157b7d0c144e6f3cee4620a16ce2faa680`
### mt-wilson-ca-observed-I3
- sd: 15340 lines `37454c025ca2b7e1280c913dabff28cf02bf31c8338d7cf17d1c8272f98b51f7`
- tp: 715 lines `0ad2b8417f794f4583931587a75ea8157b7d0c144e6f3cee4620a16ce2faa680`
### mt-wilson-ca-observed-seed0
- sd: 15340 lines `37454c025ca2b7e1280c913dabff28cf02bf31c8338d7cf17d1c8272f98b51f7`
- tp: 715 lines `0ad2b8417f794f4583931587a75ea8157b7d0c144e6f3cee4620a16ce2faa680`
### mt-wilson-ca-observed-seed17
- sd: 15340 lines `570c62a3e5c7510f2bbb79371e2a39da3bd926cf87063e9a5ecf49f3182d0b09`
- tp: 715 lines `0ad2b8417f794f4583931587a75ea8157b7d0c144e6f3cee4620a16ce2faa680`
### new-meadows-id-I1
- sd: 22644 lines `ab6ed6d2468d29e406f5f8144bf46c42f0558f86b85c86e213b79ba4ac53fd1f`
- tp: 2411 lines `e779a65ef61483cbd969cf21e263a76aafee9c3c8dd1cc0bbee5fa1a67c772d5`
### new-meadows-id-I2
- sd: 22644 lines `2ed9b9927c8501bc02336762b3f66dd050a9a162642ea25620bf6526b18b8020`
- tp: 2411 lines `e779a65ef61483cbd969cf21e263a76aafee9c3c8dd1cc0bbee5fa1a67c772d5`
### new-meadows-id-I3
- sd: 22644 lines `4db4440372057a61b0bb1cdfb9748d6b41f597cad6007be26066b31897499f7e`
- tp: 2411 lines `e779a65ef61483cbd969cf21e263a76aafee9c3c8dd1cc0bbee5fa1a67c772d5`
### new-meadows-id-seed0
- sd: 22644 lines `53e738188269b138083afa061d3b29d510a3bd76b7ee250dc3b2cccdbc05556a`
- tp: 2411 lines `e779a65ef61483cbd969cf21e263a76aafee9c3c8dd1cc0bbee5fa1a67c772d5`
### new-meadows-id-seed17
- sd: 22644 lines `ac0b5b7f292c85c5940abdb681f4b71f9025922529f6dc747fd06ba36e79ea96`
- tp: 2435 lines `eb7a9c549fcac6a491d94dfbd63184cfe94710303e788f84cbab8bc4be6ca04a`
### new-meadows-id-single-storm-seed0
- sd: 2 lines `8c0d664b88343d38a6253fd52b90babbe00c528bdd347ce1e2bf4f0a7334d4b3`
- tp: 0 lines `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
### new-meadows-id-single-storm-seed17
- sd: 2 lines `8c0d664b88343d38a6253fd52b90babbe00c528bdd347ce1e2bf4f0a7334d4b3`
- tp: 0 lines `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
