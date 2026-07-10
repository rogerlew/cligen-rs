# Tap Capture Manifest — Par + Monthlies (Stage S)

Evidence mode: Ran (2026-07-09).

## Build

```
gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math -I. cligen.f -o cligen532-par-tap
GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0        (exit code 0, verified directly)
```

- Base source = vendored reference, unmodified; `reference/cligen532/` untouched.
  `cligen.f` SHA-256: `3dfd51db98fedfbfb155d4227099cf9133043d4d699093268ed21ce16ec4267c`
- Patch `tap-patch.diff` (228 lines, additive only) SHA-256:
  `74c7f3ddcc59eac1511e98a10bc9844205e8f9143372d0bb471bb3c9af645dc4`
- Patched `tap-build/cligen.f` SHA-256:
  `30a8657a6bdf7a5d3cef50b14b84a912a78e80a45093f4829d1e8fc556493dc8`
- Tap binary SHA-256:
  `dc1d5a728d3b4cd5473c41de41e370bad3058efd4fed37226bf34480bb286ceb`
- The `.inc` files in `tap-build/` are unmodified copies of the vendored ones.

## Non-invasiveness gate

Ran: all 12 golden invocations (identical commands, stdin, and inputs to
the golden-fixture manifest, executed in fresh per-case directories under
`tap-runs/`) produced `wepp.cli` byte-identical to the committed goldens —
`cmp` IDENTICAL for every case, all exits 0.

## Capture-only invocations (seed 0; outputs are NOT goldens)

| Case | Command (in the case run dir) | Stdin |
|---|---|---|
| new-meadows-id-I1/I2/I3 | `cligen532-par-tap -I<n> -iid106388.par` | `fixtures/new-meadows-id/wepp.inp` |
| jeogla-au-I1/I2/I3 | `cligen532-par-tap -I<n> -iASN00057011.par` | `fixtures/jeogla-au/wepp.inp` |
| mt-wilson-ca-observed-I0/I1/I3 | `cligen532-par-tap -ica046006.par -Ows.prn -owepp.cli -t6 -I<n>` | none |
| fish-springs-ut-observed-padded-I0/I1/I3 | `cligen532-par-tap -iut422852.par -Ows.prn -owepp.cli -t6 -I<n>` | none |

All 24 runs exited 0.

## Committed samples (`fixtures/taps/par/<station>-I<n>/`)

Full 191-line `cligen_par.tap` per combo plus first-1,000-record
`f2-sample.tap` (I2), `y2-sample.tap` (I3), `li-sample.tap` (I1).
Combo → source run: `-I0`/`-I2` combos for the golden stations come from
the golden runs (`new-meadows-id-seed0`, `jeogla-au-seed0`,
`mt-wilson-ca-observed-seed0`, `fish-springs-ut-observed-padded-seed0`);
every other combo comes from its same-named capture-only run.

Snapshot equivalence classes (Ran): same (station, interp) ⇒
byte-identical snapshot across seeds and run modes — e.g. the
new-meadows I0 snapshot hash `d77e59d9…` is shared by seed0, seed17, and
both single-storm runs; fish-springs I2 `e36d2d9c…` is shared by
padded/truncated × seed0/seed17.

## Full captures (local, gitignored `artifacts/tap-runs/`)

| Case | par lines | f2 | y2 | li | par SHA-256 | f2 SHA-256 | y2 SHA-256 | li SHA-256 |
|---|---:|---:|---:|---:|---|---|---|---|
| fish-springs-ut-observed-padded-I0 | 191 | 0 | 0 | 0 | `8f162c19111d1c6e…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| fish-springs-ut-observed-padded-I1 | 191 | 0 | 0 | 2557 | `817e8f954ac7b46c…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `39da1aad8e58069a…` |
| fish-springs-ut-observed-padded-I3 | 191 | 0 | 17944 | 0 | `f450f3b2da9ae2f5…` | `e3b0c44298fc1c14…` | `64cc77e5d7fd6f61…` | `e3b0c44298fc1c14…` |
| fish-springs-ut-observed-padded-seed0 | 191 | 17944 | 0 | 0 | `e36d2d9c07605882…` | `635b60141dab70ef…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| fish-springs-ut-observed-padded-seed17 | 191 | 17974 | 0 | 0 | `e36d2d9c07605882…` | `15b2975d4b4753bd…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| fish-springs-ut-observed-truncated-seed0 | 191 | 16660 | 0 | 0 | `e36d2d9c07605882…` | `c0c68c2790a928b4…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| fish-springs-ut-observed-truncated-seed17 | 191 | 16660 | 0 | 0 | `e36d2d9c07605882…` | `c0c68c2790a928b4…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| jeogla-au-I1 | 191 | 0 | 0 | 15340 | `bf8a7497ab65fe0c…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `6f47a9be27307960…` |
| jeogla-au-I2 | 191 | 117331 | 0 | 0 | `4c7f13664b080f1f…` | `a78818db626e4bc8…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| jeogla-au-I3 | 191 | 0 | 117331 | 0 | `776166b8779c4219…` | `e3b0c44298fc1c14…` | `44d84e772cb44d53…` | `e3b0c44298fc1c14…` |
| jeogla-au-seed0 | 191 | 0 | 0 | 0 | `b8b59d2d6f60bd22…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| jeogla-au-seed17 | 191 | 0 | 0 | 0 | `b8b59d2d6f60bd22…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| mt-wilson-ca-observed-I0 | 191 | 0 | 0 | 0 | `375f143d53cd19fc…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| mt-wilson-ca-observed-I1 | 191 | 0 | 0 | 7670 | `c427324f5f45d63a…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `33d0457640ab3c38…` |
| mt-wilson-ca-observed-I3 | 191 | 0 | 53690 | 0 | `40156c0af550dbd6…` | `e3b0c44298fc1c14…` | `211ad4d40de228f8…` | `e3b0c44298fc1c14…` |
| mt-wilson-ca-observed-seed0 | 191 | 53690 | 0 | 0 | `534712c463bad889…` | `31a0ce22373ac94b…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| mt-wilson-ca-observed-seed17 | 191 | 53690 | 0 | 0 | `534712c463bad889…` | `31a0ce22373ac94b…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| new-meadows-id-I1 | 191 | 0 | 0 | 11322 | `111e58e33b266122…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `4b87939a04e300c2…` |
| new-meadows-id-I2 | 191 | 86487 | 0 | 0 | `bc819e2570321351…` | `76ddd16d9c6d1513…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| new-meadows-id-I3 | 191 | 0 | 86487 | 0 | `56d19e45a0a251c4…` | `e3b0c44298fc1c14…` | `7d2cb4def4621541…` | `e3b0c44298fc1c14…` |
| new-meadows-id-seed0 | 191 | 0 | 0 | 0 | `d77e59d965499903…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| new-meadows-id-seed17 | 191 | 0 | 0 | 0 | `d77e59d965499903…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| new-meadows-id-single-storm-seed0 | 191 | 0 | 0 | 0 | `d77e59d965499903…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |
| new-meadows-id-single-storm-seed17 | 191 | 0 | 0 | 0 | `d77e59d965499903…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` | `e3b0c44298fc1c14…` |

`e3b0c44298fc1c14…` is the empty-file hash (streams not exercised by that
run's interp mode). Full 64-hex digests: regenerate with
`sha256sum tap-runs/*/cligen_*.tap`; the committed samples are prefixes
of (or equal to) these files by construction.

### Stage C exercised-stream digests (full SHA-256)

R1 found that the capture table above retained only display prefixes even
though the kickoff treats the manifest hashes as the identity of the local
evidence tree. Stage C reran `sha256sum` over every non-empty stream consumed
by its ignored full-stream gate and records the complete digests here.

| Case | Stream | SHA-256 |
|---|---|---|
| new-meadows-id-I2 | f2 | `76ddd16d9c6d1513f94f9a171c88acd3ecb567be4e46e02cf6b577806c7198d9` |
| jeogla-au-I2 | f2 | `a78818db626e4bc8d35afd6d2086725c05a05baad63d27cbbe7220cf54d55503` |
| mt-wilson-ca-observed-seed0 | f2 | `31a0ce22373ac94b5e238e065a70cee09dcb4df271939d05b4ec66ea8c2d043c` |
| mt-wilson-ca-observed-seed17 | f2 | `31a0ce22373ac94b5e238e065a70cee09dcb4df271939d05b4ec66ea8c2d043c` |
| fish-springs-ut-observed-padded-seed0 | f2 | `635b60141dab70ef1c0103134f126344be99fd3a67151835dd592a234ff75716` |
| fish-springs-ut-observed-padded-seed17 | f2 | `15b2975d4b4753bd0efc73b30af4545c4089819483cab4981a317576282b45fe` |
| fish-springs-ut-observed-truncated-seed0 | f2 | `c0c68c2790a928b475ad1ab532546501474962ace9ee16168e69396f9422b24a` |
| fish-springs-ut-observed-truncated-seed17 | f2 | `c0c68c2790a928b475ad1ab532546501474962ace9ee16168e69396f9422b24a` |
| new-meadows-id-I3 | y2 | `7d2cb4def46215410a38c8b61c6ebabc00beab4fcb4e9fb6d147347ecf353b30` |
| jeogla-au-I3 | y2 | `44d84e772cb44d53c0c1f8412845f0c345e1c3ae4b892082248a1b6b3c8e6f55` |
| mt-wilson-ca-observed-I3 | y2 | `211ad4d40de228f8525ff981bc8a730ea51353fe25cb41cf8dbebd20fa7b2721` |
| fish-springs-ut-observed-padded-I3 | y2 | `64cc77e5d7fd6f61f8ba36752bcf517f497c8f43434c52f9c5b3c38d5a2a9704` |
| new-meadows-id-I1 | li | `4b87939a04e300c25caa4ce4328cd1722087b43e05dc34294079b079e775b222` |
| jeogla-au-I1 | li | `6f47a9be27307960278e306bb0ef28df937829b8c2a1be4211932f5c541f5187` |
| mt-wilson-ca-observed-I1 | li | `33d0457640ab3c389b2557c0cd2e000aa32efe00fc452da6c4d120938371bd4c` |
| fish-springs-ut-observed-padded-I1 | li | `39da1aad8e58069ae8f6e23cac427fde428c7533e334aed02d60e29521147571` |

Stream-count cross-checks observed at capture: `f2` (I2) and `y2` (I3)
counts match per station (86,487 new-meadows; 117,331 jeogla; 53,690
mt-wilson observed) — same generation call pattern, different evaluator.
Fish-springs truncated `f2` is seed-invariant (16,660 both seeds; the
hard-EOF record fully determines which fields generate), while the
padded case varies with seed (17,944 vs 17,974) — sentinel-tail
regeneration draws differ.
