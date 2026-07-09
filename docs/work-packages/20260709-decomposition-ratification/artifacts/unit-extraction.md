# Unit Extraction (mechanical)

Evidence mode: Ran (this script; see extract.py)

| Unit | Kind | Lines | Includes | Callees |
|---|---|---|---|---|
| `(preamble: header comments, no code)` | comments | 1-381 | — | — |
| `cligen` | program | 382-984 | cbk1.inc, cbk4.inc, cbk5.inc, cbk7.inc, cbk9.inc, cinterp.inc, command6.inc, crandom3.inc | getarg, r5monb, randn, sing_stm, sta_dat, usr_opt, wxr_gen |
| `alph` | subroutine | 985-1036 | cbk3.inc, cbk4.inc, cbk5.inc, cbk7.inc, cbk9.inc | dstg |
| `blockdata` | blockdata | 1037-1093 | cbk4.inc, cbk7.inc, cinterp.inc, command6.inc, crandom3.inc | — |
| `clgen` | subroutine | 1094-1515 | cbk1.inc, cbk3.inc, cbk4.inc, cbk5.inc, cbk7.inc, cinterp.inc, crandom3.inc | dstn1, fouri2, randn, ranset, ryf2 |
| `clmout` | subroutine | 1516-1650 | cbk4.inc, ccl1.inc, csumr.inc | — |
| `dstg` | function | 1651-1788 | crandom3.inc | ks_tst, randn |
| `dstn1` | function | 1789-1816 | — | — |
| `jdt` | function | 1817-1845 | — | — |
| `jlt` | subroutine | 1846-1903 | — | — |
| `r5mon` | subroutine | 1904-1979 | cbk4.inc, cbk7.inc, cbk9.inc | — |
| `randn` | function | 1980-2019 | — | — |
| `windg` | subroutine | 2020-2122 | cbk1.inc, cbk3.inc, cbk4.inc, cbk7.inc, crandom3.inc | dstn1 |
| `nrmd` | subroutine | 2123-2152 | — | — |
| `header` | subroutine | 2153-2187 | — | — |
| `timepk` | function | 2188-2239 | cbk4.inc, crandom3.inc | randn |
| `sta_dat` | subroutine | 2240-2485 | command6.inc | header, sta_name, sta_parms |
| `sta_name` | subroutine | 2486-2655 | command6.inc | — |
| `sta_parms` | subroutine | 2656-2970 | cbk1.inc, cbk7.inc, cbk9.inc, cinterp.inc, command6.inc | fouri1, ryf1 |
| `day_gen` | subroutine | 2971-3195 | cbk1.inc, cbk3.inc, cbk4.inc, cbk5.inc, cbk7.inc, cbk9.inc, ccl1.inc, cinterp.inc | alphb, clgen, jlt, lintrp, timepk, windg |
| `opt_calc` | subroutine | 3196-3324 | cbk4.inc, cbk5.inc, command6.inc, csumr.inc | clmout |
| `sing_stm` | subroutine | 3325-3496 | cbk4.inc, command6.inc | — |
| `usr_opt` | subroutine | 3497-3588 | cbk4.inc, command6.inc | — |
| `wxr_gen` | subroutine | 3589-3816 | cbk4.inc, cbk7.inc, ccl1.inc, cinterp.inc, command6.inc | day_gen, jdt, opt_calc |
| `alphb` | subroutine | 3817-3897 | cbk3.inc, cbk4.inc, cbk5.inc, cbk7.inc, cbk9.inc | dstg |
| `r5monb` | subroutine | 3898-4001 | cbk3.inc, cbk4.inc, cbk5.inc, cbk7.inc, cbk9.inc | — |
| `ranset` | subroutine | 4002-4341 | cbk4.inc, cbk7.inc, crandom3.inc | conflm, confls, dstn1, ks_tst, randn |
| `chitst` | subroutine | 4342-4452 | crandom3.inc | — |
| `ks_tst` | subroutine | 4453-4588 | crandom3.inc | — |
| `conflm` | subroutine | 4589-4649 | — | — |
| `confls` | subroutine | 4650-4704 | — | cdfchi |
| `cdfchi` | subroutine | 4705-4953 | — | cumchi, dinvr, dstinv, spmpar |
| `cumchi` | subroutine | 4954-5007 | — | cumgam |
| `cumgam` | subroutine | 5008-5069 | — | gratio |
| `dinvr` | subroutine | 5070-5418 | — | dstzr, dzror |
| `dzror` | subroutine | 5419-5702 | — | — |
| `erf` | function | 5703-5777 | — | — |
| `erfc1` | function | 5778-5889 | — | exparg |
| `exparg` | function | 5890-5941 | — | ipmpar |
| `gam1` | function | 5942-6006 | — | — |
| `gamma` | function | 6007-6157 | — | exparg, spmpar |
| `gratio` | subroutine | 6158-6574 | — | erf, erfc1, gam1, gamma, rexp, rlog, spmpar |
| `ipmpar` | function | 6575-7004 | — | — |
| `rexp` | function | 7005-7038 | — | — |
| `rlog` | function | 7039-7094 | — | — |
| `spmpar` | function | 7095-7251 | — | ipmpar |
| `lintrp` | subroutine | 7252-7337 | cinterp.inc | — |
| `fouri1` | subroutine | 7338-7386 | cinterp.inc | — |
| `fouri2` | function | 7387-7423 | cbk3.inc, cinterp.inc | — |
| `ryf1` | subroutine | 7424-7544 | cinterp.inc | — |
| `ryf2` | function | 7545-7657 | cinterp.inc | — |

## Reference counts (live code only)

| Callee | Callers (line) |
|---|---|
| `alphb` | day_gen:3119, day_gen:3141 |
| `cdfchi` | confls:4691 |
| `clgen` | day_gen:3094 |
| `clmout` | opt_calc:3264, opt_calc:3283 |
| `conflm` | ranset:4229, ranset:4245 |
| `confls` | ranset:4230, ranset:4246 |
| `cumchi` | cdfchi:4883, cdfchi:4883, cdfchi:4896, cdfchi:4896, cdfchi:4926, cdfchi:4926 |
| `cumgam` | cumchi:5003, cumchi:5003 |
| `day_gen` | wxr_gen:3788 |
| `dinvr` | cdfchi:4894, cdfchi:4906, cdfchi:4924, cdfchi:4936 |
| `dstg` | alph:1030, alphb:3882 |
| `dstinv` | cdfchi:4892, cdfchi:4922 |
| `dstn1` | clgen:1254, clgen:1283, clgen:1350, clgen:1356, clgen:1360, clgen:1472, windg:2109, ranset:4196, ranset:4197 |
| `dstzr` | dinvr:5293 |
| `dzror` | dinvr:5303 |
| `erf` | gratio:6556 |
| `erfc1` | gratio:6431, gratio:6473, gratio:6560 |
| `exparg` | erfc1:5856, gamma:6151 |
| `fouri1` | sta_parms:2831, sta_parms:2832, sta_parms:2833, sta_parms:2834, sta_parms:2835, sta_parms:2836, sta_parms:2837, sta_parms:2838, sta_parms:2839, sta_parms:2840, sta_parms:2841, sta_parms:2842 (+2 more) |
| `fouri2` | clgen:1245, clgen:1266, clgen:1267, clgen:1297, clgen:1298, clgen:1299, clgen:1300, clgen:1317, clgen:1379, clgen:1380, clgen:1381, clgen:1382 (+3 more) |
| `gam1` | gratio:6293, gratio:6401 |
| `gamma` | gratio:6306 |
| `getarg` | cligen:660 |
| `gratio` | cumgam:5062, cumgam:5062 |
| `header` | sta_dat:2343 |
| `ipmpar` | exparg:5916, exparg:5932, exparg:5936, spmpar:7138, spmpar:7139, spmpar:7144, spmpar:7145, spmpar:7152, spmpar:7153, spmpar:7154 |
| `jdt` | wxr_gen:3762 |
| `jlt` | day_gen:3088 |
| `ks_tst` | dstg:1732, ranset:4227, ranset:4243, ranset:4256 |
| `lintrp` | day_gen:3092 |
| `opt_calc` | wxr_gen:3797 |
| `r5monb` | cligen:878 |
| `randn` | cligen:727, cligen:728, cligen:729, cligen:730, cligen:731, cligen:732, cligen:733, cligen:734, cligen:735, cligen:888, cligen:891, cligen:894 (+26 more) |
| `ranset` | clgen:1209 |
| `rexp` | gratio:6414 |
| `rlog` | gratio:6312 |
| `ryf1` | sta_parms:2846, sta_parms:2847, sta_parms:2848, sta_parms:2849, sta_parms:2850, sta_parms:2851, sta_parms:2852, sta_parms:2853, sta_parms:2854, sta_parms:2855, sta_parms:2856, sta_parms:2857 (+2 more) |
| `ryf2` | clgen:1247, clgen:1269, clgen:1270, clgen:1302, clgen:1303, clgen:1304, clgen:1305, clgen:1319, clgen:1384, clgen:1385, clgen:1386, clgen:1387 (+3 more) |
| `sing_stm` | cligen:912 |
| `spmpar` | cdfchi:4863, gamma:6100, gratio:6272 |
| `sta_dat` | cligen:856 |
| `sta_name` | sta_dat:2357 |
| `sta_parms` | sta_dat:2470 |
| `timepk` | day_gen:3143 |
| `usr_opt` | cligen:905 |
| `windg` | day_gen:3095 |
| `wxr_gen` | cligen:913 |

## Commented-out call sites

| Callee | Sites |
|---|---|
| `alph` | day_gen:3118, day_gen:3140 |
| `argopt` | cligen:656 |
| `chitst` | dstg:1731, ranset:4225, ranset:4241, ranset:4255 |
| `conflm` | conflm:4636 |
| `getarg` | cligen:654 |
| `getcl` | spmpar:7186, spmpar:7226 |
| `gettim` | cligen:708 |
| `gratio` | cumgam:5064 |
| `header` | sta_dat:2342 |
| `opt_calc` | wxr_gen:3796 |
| `r5mon` | cligen:877 |
| `sta_dat` | cligen:855 |
| `sta_parms` | sta_dat:2468 |
