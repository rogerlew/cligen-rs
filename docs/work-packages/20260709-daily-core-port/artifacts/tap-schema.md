# Tap Schema + Capture Manifest — Daily Core (Stage S)

Evidence mode: design (Static) + capture (Ran, 2026-07-09). Inherits the
item-3/4 constraints: bit-exact Z8.8 via EQUIVALENCE, additive writes
only, applied to a copied build tree (`reference/` untouched),
non-invasiveness gate = golden byte-identity.

## Build

```
gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math -I. cligen.f -o cligen532-daily-tap
GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0        (exit 0, verified directly)
- Base cligen.f (vendored, unmodified) SHA-256: 3dfd51db98fedfbfb155d4227099cf9133043d4d699093268ed21ce16ec4267c
- Patch tap-patch.diff (166 lines, additive) SHA-256: ca8a2b2dd4212eec6dad31145e94df242b6f7f75c7a4c888e9a6de2def227c29
- Patched cligen.f SHA-256: 99b0a11d8171bbd4750aada4e6cca260a1745c267e67d1f219e390d85dc60e5a
- Tap binary SHA-256: 8015338aee4cff98720c315afa4536dee291c7620c02e3a62607033ff87a465a
```

## Streams

### `cligen_cg.tap` — unit 85, five lines per `clgen` call

- `B mo ida ntd iyear nsim msim l mox dax` — entry scalars, **pre**
  month-boundary (`mox`/`dax` as clgen found them).
- `K 40i5` — entry `k1..k10` seed state (sequential-replay assertion
  surface; desync localizes ranset/draw-order errors to the record).
- `V 9×Z8.8` — entry `v1 v3 v5 v7 v9 v11 tmxg tmng rst(mo,3)`. Entry
  `tmxg`/`tmng` are **external inputs** at replay (day_gen converts
  them F→C in place between calls; observed mode overwrites them);
  the rolling v's and clamped skew are replay-asserted state.
- `C dax 6×Z8.8` — post-boundary `dax` and the batch columns consumed
  at it (`vvx v2x v4x v6x v8x v12x`), for column-desync localization.
- `A 6×Z8.8 l` — exit `r(ida) tmxg tmng tdp ra rmx` + exit `l`.

### `cligen_wg.tap` — unit 86, two lines per `windg` call

`W mo dax Z(v9_in) Z(fxx(dax))` + `X Z(wv) Z(th) Z(v9_out) j`.

### `cligen_ab.tap` — unit 87, two lines per `alphb` call

`G mo ida k7(4i5) Z(r(ida)) Z(wi(mo)) Z(sml)` + `H Z(r1)`. `k7` entry
pairs with the item-3 `dg` replay (alphb is `dstg`'s only caller —
call counts match the dg streams exactly, e.g. 4,822 for
new-meadows-seed0).

### `cligen_r5.tap` — unit 88, one record per run

`R5 12×Z8.8` — `wi(1..12)` after `r5monb`'s in-place conversion to the
α = R30/R ratio (called via an added `tapr5` subroutine at the end of
`r5monb`).

## Capture matrix and non-invasiveness gate (Ran)

The item-4 24-run matrix (12 golden invocations + 12 capture-only
interp variants at seed 0), identical commands/stdin. **All 12
patched-binary golden `.cli` outputs byte-identical** (`cmp`, 12/12);
all 24 runs exit 0. The capture-only `-I1`/`-I3` runs exercise clgen's
lintrp/ryf2 interp branches; the observed goldens exercise
`nsim`/`msim` = 0 gating and the `-I2` fouri2 branches.

## Committed samples vs local full captures

`fixtures/taps/daily/<case>/`: 10 representative cases (4 stations
across interp {0,1,2,3} and both modes, both seeds for new-meadows,
single-storm) with first-500-record `cg`/`wg`/`ab` samples (sequential
prefixes — valid replay inputs) and the full one-record `r5.tap`.
Full streams stay local under gitignored `tap-runs/`, pinned below;
full-stream verification is Stage C's `#[ignore]` evidence gate.

## Full-capture digests (per case: cg/wg/ab/r5 SHA-256)

### fish-springs-ut-observed-padded-I0
- cg: 12785 lines `c7107747c684ffbe128b3781da7627abc99dda974f7016ec4fdc60b71cf09baf`
- wg: 5114 lines `3170b2de3fd05c6812339b175ac3f177f864eb6f59d0d012a7d84f37ee034130`
- ab: 2136 lines `7d0547fd148e70452377ea908c7c985864d3a7ffed26eb6080c30c119c3ab124`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### fish-springs-ut-observed-padded-I1
- cg: 12785 lines `fd1bb1e60af1a63c1660bea2e42c1d1db5d8d2bafded61e389bc62feb03af06e`
- wg: 5114 lines `3170b2de3fd05c6812339b175ac3f177f864eb6f59d0d012a7d84f37ee034130`
- ab: 2136 lines `db14f11feecc55aa585894267b0cb7cc2254b05dc1bec43ee9faa159b0ede3fd`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### fish-springs-ut-observed-padded-I3
- cg: 12785 lines `d82a8c45e10b25f8b466b8d8a4930b5272a3fbf39bc568daabf635315ed070e9`
- wg: 5114 lines `3170b2de3fd05c6812339b175ac3f177f864eb6f59d0d012a7d84f37ee034130`
- ab: 2136 lines `586e65eee7936ed2c34d324b77f751b4f806421e54571a3b5174217b58787007`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### fish-springs-ut-observed-padded-seed0
- cg: 12785 lines `faaa2ac5dadda01d544f0176fa8e517bc7ac97fc5eb1422dfc0374f8806875ce`
- wg: 5114 lines `3170b2de3fd05c6812339b175ac3f177f864eb6f59d0d012a7d84f37ee034130`
- ab: 2136 lines `36ac5e7d9404837b1c67ea0cf8e649590aaa70731e572281b68058ad35b0dabd`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### fish-springs-ut-observed-padded-seed17
- cg: 12785 lines `481363027d347dcf7a1e00b113ab030a679fd12b908041729dc0ec8e33b07cd8`
- wg: 5114 lines `e71ccb5665c93e7b7222ce115722c032198b7151c422c8992aa8ea4938d80e33`
- ab: 2176 lines `b88cc89cb8fafaef8602f96f80b5a9f45e24a224727a93e5e80f4e393095b4ff`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### fish-springs-ut-observed-truncated-seed0
- cg: 11900 lines `0929058b8a2353ff8d7ccf6f47d2a9d47ae4f07a81d112fc4f46bf587703e5bf`
- wg: 4760 lines `80c5687a5b878ea0ac145b882a01d4c5fce4dbb2b186fd1a4b34e10690455f69`
- ab: 2076 lines `4e8617948d0a60fae52b1ec15f47d894208f69a4ee7ea052d7fb1315c23e039a`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### fish-springs-ut-observed-truncated-seed17
- cg: 11900 lines `63edfc42dd7877d5bd20b78dfa9ffa9202f3dfb6cfcaa4672392d92868be909c`
- wg: 4760 lines `86788558c3b16df5f387638d8b39ea4a855a6660662251b2346460d8996a67f7`
- ab: 2076 lines `f95ee95d8e45afa030e2ae1557a19ab409e0e8ef2ca3a389be7a678daf8ffd0c`
- r5: 1 lines `64b8720aec8486227c71ed98fb7b8d942f6867f661950d018cf9a19b0139fe21`
### jeogla-au-I1
- cg: 76700 lines `c855ee322a872c374fc3275011341b8e707080ef5bc7ad4b72e9acf727e92391`
- wg: 30680 lines `7c6efbcd8d14609e0afd0e31e53c28b5ff95659fb9141c9efd33b1af2eff754a`
- ab: 13268 lines `41822fd8457c33e2ff1d556a17a00f34f6978bea4a2295a84b4bfcea713b4ebd`
- r5: 1 lines `ba0d5b30d46a1a64dde3b3659b97a5b57140815737da54016ea410f220fdda1a`
### jeogla-au-I2
- cg: 76700 lines `3101ace3b9e424d5d76e1a0d92ae3df8e09bc3cc8a71b131ff95c886e7313ae1`
- wg: 30680 lines `7c6efbcd8d14609e0afd0e31e53c28b5ff95659fb9141c9efd33b1af2eff754a`
- ab: 13268 lines `ea5530bd813732a1416aa54effcf9daaeae4faf93a44263615ecaefe794bc175`
- r5: 1 lines `ba0d5b30d46a1a64dde3b3659b97a5b57140815737da54016ea410f220fdda1a`
### jeogla-au-I3
- cg: 76700 lines `7a762abef938c121bfca927e103afd4663dfdfaa282e82f67d17486ebd5b89b9`
- wg: 30680 lines `7c6efbcd8d14609e0afd0e31e53c28b5ff95659fb9141c9efd33b1af2eff754a`
- ab: 13268 lines `6fa8856c1eda74b15c58ad1811d9668359ace63fd589fa0e21630c109b4a3da0`
- r5: 1 lines `ba0d5b30d46a1a64dde3b3659b97a5b57140815737da54016ea410f220fdda1a`
### jeogla-au-seed0
- cg: 76700 lines `5dbfe135c49673cee8c51d91423e9ab7233f5e8bac70927f9d530dfdf5598e63`
- wg: 30680 lines `7c6efbcd8d14609e0afd0e31e53c28b5ff95659fb9141c9efd33b1af2eff754a`
- ab: 13268 lines `d0be8d63a21b05e5a538c52ec0d5c1f380ea0f28976c39726c2f920444a48d58`
- r5: 1 lines `ba0d5b30d46a1a64dde3b3659b97a5b57140815737da54016ea410f220fdda1a`
### jeogla-au-seed17
- cg: 76700 lines `bbe414a8deacc5d8392c918cb47842e3aca62f9b59948b8fb423e3e4403792f2`
- wg: 30680 lines `2ca7a7a98a77653528bd3f49a5a33a856dde8e8b392d59acf109c987e766c11d`
- ab: 13700 lines `c73beb6284cbb58f29f6f3cd7272c8df3195f0c72f53f3dfb7b9a6473e2b3de2`
- r5: 1 lines `ba0d5b30d46a1a64dde3b3659b97a5b57140815737da54016ea410f220fdda1a`
### mt-wilson-ca-observed-I0
- cg: 38350 lines `c07339eec6a801032d7f12f5301b1aea418f656224dfa68c46578fe9b368f79b`
- wg: 15340 lines `e52c8bbd7140a9f2e1080be8c4dd909e643d0e9f96a8855706203a3c97769c31`
- ab: 2860 lines `e71691875ba7dc68e5a39d79cc60dfa499d21f7d05cb011bf1161117a4724b62`
- r5: 1 lines `6fa9c578963f2bd15002f5345460c8d476b07122499df14bced2c9b5455fb0db`
### mt-wilson-ca-observed-I1
- cg: 38350 lines `59c8943894d5cb6a4023fb4c9b1ed43517e16114bf1da8bcd5a8d24f35c8e5ea`
- wg: 15340 lines `e52c8bbd7140a9f2e1080be8c4dd909e643d0e9f96a8855706203a3c97769c31`
- ab: 2860 lines `e71691875ba7dc68e5a39d79cc60dfa499d21f7d05cb011bf1161117a4724b62`
- r5: 1 lines `6fa9c578963f2bd15002f5345460c8d476b07122499df14bced2c9b5455fb0db`
### mt-wilson-ca-observed-I3
- cg: 38350 lines `8ab7709fd49605c7f7f29eeb9fbd507b4a489fd63dbd96caa7bac4727db95c3a`
- wg: 15340 lines `e52c8bbd7140a9f2e1080be8c4dd909e643d0e9f96a8855706203a3c97769c31`
- ab: 2860 lines `e71691875ba7dc68e5a39d79cc60dfa499d21f7d05cb011bf1161117a4724b62`
- r5: 1 lines `6fa9c578963f2bd15002f5345460c8d476b07122499df14bced2c9b5455fb0db`
### mt-wilson-ca-observed-seed0
- cg: 38350 lines `af7e0eb53ad405bbaf5587918237447cfcd7cb5b3547f80125037cc16d52bfa5`
- wg: 15340 lines `e52c8bbd7140a9f2e1080be8c4dd909e643d0e9f96a8855706203a3c97769c31`
- ab: 2860 lines `e71691875ba7dc68e5a39d79cc60dfa499d21f7d05cb011bf1161117a4724b62`
- r5: 1 lines `6fa9c578963f2bd15002f5345460c8d476b07122499df14bced2c9b5455fb0db`
### mt-wilson-ca-observed-seed17
- cg: 38350 lines `d5b5c2e26f59ad059c98e289e778eae2ce981124e56349ecf7f06d4092de3bed`
- wg: 15340 lines `870f1b12c97d664ff25998fc2f894478de76295174cd15dc93afc3e26fe1fed8`
- ab: 2860 lines `af0797827921201f185d06a4c4e373dbda6c8a2ff5b327a7c6953dc32dc9be9b`
- r5: 1 lines `6fa9c578963f2bd15002f5345460c8d476b07122499df14bced2c9b5455fb0db`
### new-meadows-id-I1
- cg: 56610 lines `94c7914d4dfe19f510dc45467bf0cad890b82d5adea6e33a6a8585bedbe947df`
- wg: 22644 lines `a67b3d8588d635e64740070129c39fa5a1aabad1060711a88c77e4778af8d676`
- ab: 9644 lines `055fa2ea7cce3cccbc59065ccd1286aaaaa4750d3f9f0a077d32ed55ae9572b4`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
### new-meadows-id-I2
- cg: 56610 lines `3634b847dfbaee279dc3e0c4bbf6ea454cc7172df03979725e6f49b0e6368fd8`
- wg: 22644 lines `a67b3d8588d635e64740070129c39fa5a1aabad1060711a88c77e4778af8d676`
- ab: 9644 lines `276ddee0459ec320deb6076b42be08bf1c44b8dc204a2db514a015d388d2f626`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
### new-meadows-id-I3
- cg: 56610 lines `97f44f60a4a4554f018226a0816364fe5b6ca697f86359503d9d720b290bec88`
- wg: 22644 lines `a67b3d8588d635e64740070129c39fa5a1aabad1060711a88c77e4778af8d676`
- ab: 9644 lines `c0f39d79935eeb45638df48a6893fb2e07f6f285ed6f727b628d339dcd218477`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
### new-meadows-id-seed0
- cg: 56610 lines `0d87d5e4ef891b2d54a7a99bbbf62336042cab5c8f7388343fcb1d021a8e720e`
- wg: 22644 lines `a67b3d8588d635e64740070129c39fa5a1aabad1060711a88c77e4778af8d676`
- ab: 9644 lines `ec6b99d3adc43e1345178ee24492db12caddc21cbcaa90a60fff6bc67174a13d`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
### new-meadows-id-seed17
- cg: 56610 lines `f4a50102fac7f50670dc8f9f96d6baf1aa8592df4d48471f3a4c2bbb311125af`
- wg: 22644 lines `a8c1cb2509bcf50745cab97cada125f8941b9caf626a8ab0751f448d6d2a2ea4`
- ab: 9740 lines `53c4b46efa878e08e08c774debfd2073d38d1866f1e76b258efd539676eee701`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
### new-meadows-id-single-storm-seed0
- cg: 5 lines `1ff9a2cd55a7b7e364ef2ab5c999285a773a80bcf8f49a2f126e7dfc70552284`
- wg: 2 lines `abed54fecebb8cfdf5a85be3f9ef1d363d4b241a9a9b927c9c55d651ac88f38f`
- ab: 0 lines `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
### new-meadows-id-single-storm-seed17
- cg: 5 lines `d33fb7f40fe1da9a797d88d0b2c358c52e2c7db08c6ee1190276ddc611e97982`
- wg: 2 lines `7f3c1b41cdf60542a5155eeecaa9a6f303c611bed73ed089284c244a3ef623c2`
- ab: 0 lines `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- r5: 1 lines `84d4a09e31cd48c2eccdbf64c7a6af8d4af06afe08666841b09ea0b36832c144`
