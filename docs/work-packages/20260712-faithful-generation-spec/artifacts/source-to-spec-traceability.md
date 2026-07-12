# Faithful generation source-to-spec traceability

Status: Static review, 2026-07-12

This crosswalk covers the continuous (`iopt = 5`) and hybrid observed
(`iopt = 6`) behavior specified by `SPEC-FAITHFUL-GENERATION`. Source ranges
are inclusive and refer to `reference/cligen532/cligen.f`. The Fortran is the
behavioral authority; Rust symbols and tests identify the port and its existing
evidence. Standalone option-4/7 intake and overrides are deliberately absent.

## Evidence key

| Key | Existing executable or recorded evidence |
|---|---|
| PAR | `tests/par_state_identity.rs`: `sta_parms_matches_fortran_snapshots_full_matrix`, `monthlies_evaluators_match_fortran_tap_samples`, and the recorded full evaluator streams; committed samples under `fixtures/taps/par/` |
| RNG | `tests/tap_identity.rs`: `randn_matches_fortran_tap_samples`, `dstn1_matches_fortran_tap_samples`, `dstg_replays_fortran_tap_streams`, `ranset_replays_fortran_tap_samples`; recorded full streams are 19,784,955 `randn`, 26,402,148 `dstn1`, 30,268 `dstg`, and 2,584 `ranset` calls |
| QC | `tests/qc_vectors.rs`, `tests/acm_vectors.rs`, and `tests/qc_filter.rs::explicit_faithful_qc_is_byte_identical_to_the_golden` |
| CAL | `tests/calendar_vectors.rs::calendar_units_match_fortran_vectors` |
| DAY | `tests/daily_identity.rs`: per-unit `clgen`, `windg`, `alphb`, and `r5monb` sample replays plus recorded full replay of 189,205 in-scope daily calls and two standalone-storm calls, with 72,130 `alphb` calls total; committed samples under `fixtures/taps/daily/` |
| STM | `tests/storm_identity.rs::storm_chain_replays_fortran_samples` and the recorded full replay of 189,205 in-scope days plus two standalone-storm days and 36,065 `timepk` calls; committed samples under `fixtures/taps/storm/` |
| MODE | `tests/modes_identity.rs`: observed-parser vectors, `cold_start_reproduces_first_year_from_samples`, and the recorded cold-start replay of 189,205 in-scope rows plus two standalone-storm rows across 24 captures |
| E2E | `tests/cli_parity.rs::goldens_reproduced_byte_identically` and `tests/runspec_cli.rs::cligen_binary_runs_all_golden_runspecs_byte_identically` over 10 in-scope provenance-pinned `.cli` goldens plus two standalone-storm goldens |

Recorded full-stream totals above are the ran evidence in the 2026-07-09 port
packages' `artifacts/gate-results.md`; this documentation package does not
recapture or rerun the reference binary.

## Station state and interpolation

| Spec behavior or field | Fortran unit and lines | Rust symbol | State / RNG stream | Evidence |
|---|---|---|---|---|
| Wet-day precipitation mean, SD, and skew | `sta_parms` 2793-2796; consumers `clgen` 1232-1274 | `par::sta_parms`; `daily::gen_precip` | `Cbk7State::rst[12][3]`; no draw at load | PAR, DAY, E2E |
| Wet-after-wet and wet-after-dry probabilities | `sta_parms` 2796; consumers `clgen` 1214-1221 and `ranset` 4150-4159 | `par::sta_parms`; `daily::gen_precip`; `rng::draw_ranset_value` | `Cbk7State::prw[12][2]`; `k1`; separate daily `l` and refill `RansetState::ell` | PAR, RNG, DAY, E2E |
| Tmax/Tmin monthly means and SDs | `sta_parms` 2797-2799; `clgen` 1280-1446 | `par::sta_parms`; `daily::temp_params`, `temps_observed`, `temps_generated` | `obmx`, `obmn`, `stdtx`, `stdtm`; `k2`, `k3` when generated | PAR, DAY, MODE, E2E |
| Radiation monthly mean and SD | `sta_parms` 2800-2801; `clgen` 1469-1509 | `par::sta_parms`; `daily::gen_radiation` | `obsl`, `stdsl`; `k4` rolling pair | PAR, DAY, E2E |
| Maximum-30-minute precipitation parameter | `sta_parms` 2802-2812; `r5monb` 3931-3995 | `par::sta_parms`; `daily::r5monb` | `Cbk9State::wi`: input intensity -> half-hour depth -> dimensionless monthly ratio; no RNG | PAR, DAY (`r5monb`), E2E |
| Mean dew point | `sta_parms` 2814; `clgen` 1311-1342, 1390-1441 | `par::sta_parms`; `daily::temp_params`, `temps_observed`, `temps_generated` | `Cbk1State::rh`; `k9` rolling pair | PAR, DAY, MODE, E2E |
| Time-to-peak cumulative distribution | main sentinel 846; `sta_parms` 2815; `timepk` 2188-2236 | `par::sta_parms`; `storm::timepk` | `timpkd[0:12]`; `k10` batch column 9 or direct observed-mode draw | PAR, STM, MODE, E2E |
| Directional wind percentages, speed mean/SD/skew, and calm residual | `sta_parms` 2870-2883, 2910-2925; `windg` 2071-2116 | `par::sta_parms`; `daily::windg` | `wvl`, `calm`, cumulative `dir`; `k6` direction and `k8` speed | PAR, DAY, E2E |
| Station latitude drives the astronomical radiation bound | `sta_parms` 2793; setup 885-887; `clgen` 1185-1202 | `StaParmsOut::ylt`; `modes::generation_setup_with_process`; `daily::solar_rmx` | fixed `yls`/`ylc`; no RNG | PAR, DAY, MODE, E2E |
| Station type selects the fixed peak-rate ceiling | main `tymax` data 602; `sta_parms` 2793; daily block 3147-3151 | `StaParmsOut::itype`; `storm::TYMAX`, `storm_block` | `tymax[itype]` in mm/h; second `k7` event path supplies the uncapped value | PAR, STM, MODE, E2E |
| Elevation and CV summary derivations do not drive the daily equations | `sta_parms` 2884-2904 | `par::sta_parms` | `StaParmsOut::elev`; `cvtm`, `cvtx`, `cvs`; no RNG | PAR, E2E |
| Interpolation setup for indices 1-14; generation has no evaluator call for 4, 5, 12, or 14 | `sta_parms` 2829-2868; all live evaluator calls in `clgen` 1240-1490 | `par::sta_parms`; `daily::interp_val` | `CinterpState`; deterministic, no RNG | PAR, DAY |
| Linear midpoint interpolation | `lintrp` 7252-7335; caller `day_gen` 3087-3093 | `monthlies::lintrp`; `modes::day_gen`; `daily::interp_val` | daily `lf`, `rf`, `o_mo`; no RNG | PAR, DAY, MODE |
| Six-harmonic Fourier setup/evaluation and fixed `/366` phase | `fouri1` 7338-7384; `fouri2` 7387-7421 | `monthlies::fouri1`, `fouri2` | `x_bar`, `c`, `t`; Julian `ida`; no RNG | PAR, DAY, E2E |
| Monthly-mean-preserving setup/evaluation, noon and leap-February rules | `ryf1` 7424-7542; `ryf2` 7545-7657 | `monthlies::ryf1`, `ryf2` | `emv`, `pmt`, `pmv`, `xes`; month/day/`ntd`; no RNG | PAR, DAY |
| No station-level interannual latent state: the same 12 monthly values are reused | monthly storage/read 2793-2883; year loop 3767-3808 | `GenState`; fixed `Cbk1State`/`Cbk7State`/`Cbk9State` station arrays | persistence comes from daily chains, QC state, RNG state, and calendar only | MODE, DAY, E2E |

## Random streams, batching, and conditioners

| Spec behavior or field | Fortran unit and lines | Rust symbol | State / RNG stream | Evidence |
|---|---|---|---|---|
| Ten fixed initial stream states | block data 1037-1089, seeds 1054-1063 | `Cbk7State::default`; `rng::SeedState` | `k1` through `k10` exactly as listed in the spec | RNG, MODE, E2E |
| Burn discards one return from each of `k1`-`k9`, never `k10` | main 702-737 | `Cbk7State::burn_observed`; `modes::run_to_cli` | `k1`-`k9` advance equally by requested return count | RNG (`burn_and_warm_draw_reach_first_dstg_state`), MODE, E2E |
| Uniform update, assembly, and open-interval retry | `randn` 1980-2016, algorithm 1994-2013 | `rng::randn` | one selected four-integer `SeedState` | RNG |
| Cold setup, inverted-looking `l`, `k7` warm draw, and six rolling warm draws | main 865-902 | `modes::generation_setup_with_process` | `l`; `rn1`; rolling `v1`,`v3`,`v5`,`v7`,`v9`,`v11`; draws `k1`,`k7`,`k2`,`k3`,`k4`,`k5`,`k8`,`k9` in source order | RNG, MODE, E2E |
| Once-per-run snowmelt, alpha, angle, and latitude constants | main 865-887 | `modes::generation_setup_with_process` | `sml=0`, `ab=0.02083`, `ab1`, `pit`, `pi2`, `yls`, `ylc`; deterministic, no RNG | DAY, MODE, E2E |
| First-`ranset` predecessor initialization | `ranset` 4098-4118 | `rng::initialize_ranset_streams`; `RansetState::last_r` | one draw from `k1`,`k2`,`k3`,`k4`,`k5`,`k6`,`k8`,`k9`,`k10`; overwrites daily rolling predecessors where source does | RNG, MODE |
| Month boundary selects/refills a whole matrix; later days advance `dax` | `clgen` 1204-1212 | `daily::clgen`; `MonthlyBatchBackend::refill`; `rng::ranset` | `Crandom3State::{mox,dax,ranary}` | RNG, DAY, MODE |
| Column 1 `vvx`: occurrence uniforms | `ranset` 4140-4143 | `rng::draw_ranset_value` | `k1`; always drawn; daily consumer `gen_precip` | RNG, DAY |
| Column 2 `v2x`: Tmax pair uniforms | `ranset` 4143-4145 | `rng::draw_ranset_value` | `k2`; daily rolling predecessor `v1` | RNG, DAY |
| Column 3 `v4x`: Tmin pair uniforms | `ranset` 4145-4147 | `rng::draw_ranset_value` | `k3`; daily rolling predecessor `v3` | RNG, DAY |
| Column 4 `v6x`: radiation pair uniforms | `ranset` 4147-4149 | `rng::draw_ranset_value` | `k4`; daily rolling predecessor `v5` | RNG, DAY |
| Column 5 `v8x`: amount pair uniform only on refill-chain wet days | `ranset` 4149-4159 | `rng::draw_ranset_value` | `k5`; `RansetState::ell`; daily rolling predecessor `v7` | RNG, DAY |
| Column 6 `fxx`: wind direction uniforms | `ranset` 4160-4162 | `rng::draw_ranset_value` | `k6`; daily consumer `windg` | RNG, DAY |
| Column 7 `v10x`: wind-speed pair uniforms | `ranset` 4162-4164 | `rng::draw_ranset_value` | `k8`; daily rolling predecessor `v9` advances only on non-calm days | RNG, DAY |
| Column 8 `v12x`: dew-point pair uniforms | `ranset` 4164-4166 | `rng::draw_ranset_value` | `k9`; daily rolling predecessor `v11` | RNG, DAY, MODE |
| Column 9 `zx`: wet-mask-conditioned time-to-peak in continuous mode; all zero in observed mode | `ranset` 4166-4180 | `rng::draw_ranset_value`; `storm::timepk` | `k10`; zero mask follows column 5; option 6 draws `k10` only on positive-rain daily output | RNG, STM, MODE |
| Continuous time-to-peak has no recovery when refill and daily wet/dry chains disagree | `ranset` 4166-4180; `timepk` 2217-2233 | `rng::draw_ranset_value`; `storm::timepk` | an actual wet day can consume `zx=0`; a pre-drawn `k10` value is unused on an actual dry day | RNG, STM, MODE |
| Box-Muller deviate and `[-10,10]` clamp | `dstn1` 1789-1813 | `deviates::dstn1` | caller-owned rolling predecessor/current pair; skipped consumers do not shift it | RNG; downstream DAY and MODE |
| K-S test applies to all nine proposed columns except observed-mode column 9; mean/variance tests apply only columns 2, 3, 4, 5, and 8 | `ranset` 4185-4259; `ks_tst` 4453-4586; `conflm` 4589-4647; `confls` 4650-4700 | `rng::is_normal_parameter`, `add_ranset_attempt`, `ranset_quality_levels`; `qc`; `acm` | monthly `chicnt`, `g_dimi`, `g_dimp`, `g_dsum`, `g_ssum`; no distinct RNG stream | RNG, QC |
| QC state persists; rejection removes attempt statistics and restores only source-restored logical predecessor state, never seed state | `ranset` 4090-4097, 4120-4130, 4269-4337 | `RansetState`; `rng::remove_ranset_attempt`, `ranset` | all column seed streams continue from consumed draws; `last_r[j]` restored; `ell` restored for column 5 | RNG, QC, DAY |
| Retry counter is shared across columns and accepts the failing attempt at the 10,000 cap | `ranset` 4120-4125, 4274-4332 | `rng::ranset` | `iredo`; affected column's RNG stream continues | RNG, QC |
| Gamma rejection sampler and its independent K-S-conditioned batches | `dstg` 1651-1786 | `deviates::dstg`; `DstgState` | `k7`; saved 30-value `array`/`iarrct` can cross months/years; failed K-S rollback removes only the first 20 of 30 bin entries; mixed f32/f64 rejection expression and doubled reject counter follow source | RNG; downstream DAY and STM |

## Calendar, observed substitution, and stop control

| Spec behavior or field | Fortran unit and lines | Rust symbol | State / RNG stream | Evidence |
|---|---|---|---|---|
| Gregorian 365/366 selection and bounded year loop | `wxr_gen` 3767-3808, leap test 3773-3777 | `modes::run_to_cli` | `iyear`, `ii`, `numyr`, `ntd`; all generator state otherwise persists | CAL, MODE, E2E |
| Observed beginning year uses the requested value or first-record year; omitted year count defaults to 100 | `sing_stm` 3400-3405, 3419; first-record read `usr_opt` 3572-3574 | `storm::sing_stm`; `observed::PrnReader::initial_year`; `modes::run_to_cli` | `ibyear`, `ioyr`, `numyr`; no RNG | MODE, E2E |
| Year-grid reset | `wxr_gen` 3778-3786 | `Ccl1State::zero_year` in `modes::run_to_cli` | `prcip`, `tgmx`, `tgmn`, `radg`, `dur` only; RNG/rolling/QC state is not reset | MODE, E2E |
| Julian-day to month/day resolution | `jlt` 1846-1900; caller `day_gen` 3087-3088 | `calendar::jlt`; `modes::day_gen` | `bk3.ida` -> `bk4.mo`, local `jd`; no RNG | CAL, MODE |
| Daily operation order from read through row and cursor advance | `day_gen` 3065-3183 | `modes::day_gen` | all daily state; stream use is delegated to `clgen`, `windg`, and storm functions | MODE, DAY, STM, E2E |
| First observed record supplies an optional non-consuming initial year; later dates are positional and ignored | `usr_opt` 3524-3575; per-day format/read 3052, 3067-3073 | `observed::PrnReader::initial_year`, `next`; `modes::run_to_cli` | observed cursor; columns 11-15 only for initial year, 1-15 ignored by daily reads; no RNG | MODE parser vectors, MODE cold start, E2E |
| Every observed record resets flags and assigns all three integers before generation branches | `day_gen` 3067-3083 | `modes::day_gen` | `msim`, `nsim`; `r(ida)`, `tmxg`, `tmng`; no RNG in the read itself | MODE, E2E |
| Present observed precipitation skips occurrence/amount and does not update daily `l` | `day_gen` 3078, 3080; skipped `clgen` block 1214-1277 | `modes::day_gen`; `daily::clgen` | `nsim=0`; `l` and rolling `v7` unchanged; batch `k1`/`k5` work already occurred | MODE, DAY, E2E |
| Missing precipitation (`9999`) regenerates it and sets persistent stop flag | `day_gen` 3077-3080; generated block 1214-1277 | `modes::day_gen`; `daily::gen_precip` | `nsim=1`, `q_gen_started=true`; `k1` batch occurrence, `k5` amount/recovery | MODE, DAY, E2E |
| Both present temperatures are retained; dew point alone is generated | `day_gen` 3079, 3081-3082; `clgen` 1280-1345 | `modes::day_gen`; `daily::temps_observed` | `msim=0`; only rolling `k9` pair advances | MODE, DAY, E2E |
| Either missing temperature regenerates both; only missing Tmax sets persistent stop flag | `day_gen` 3077, 3079, 3081-3082; `clgen` 1346-1446 | `modes::day_gen`; `daily::temps_generated` | `msim=1`; `k2`, `k3`, `k9` rolling pairs advance; `q_gen_started` excludes Tmin-only sentinel | MODE, DAY, E2E |
| EOF stops before calendar conversion, refill, random use, or row emission | `day_gen` 3067-3074, branch to 3184 | `observed::PrnReader::next`; `modes::day_gen` -> `DayGenExit::Stop` | `msim`/`nsim` were reset before the read; climate and RNG state otherwise unchanged for the absent day | MODE, E2E |
| Sentinel stop flag is SAVE state and returns the same stop signal at natural year end | `day_gen` 3039-3042, 3077, 3188-3189 | `modes::DayGenState::q_gen_started`; `DayGenExit::Stop` | persists across yearly `day_gen` calls; no RNG | MODE, E2E |
| Observed mode still performs every month refill and QC attempt | unconditional `clgen` call 3094 and refill 1204-1212; option-6 column-9 exception 4166-4169, 4204-4205 | `modes::day_gen`; `daily::clgen`; `rng::ranset` | `k1`-`k6`, `k8`, `k9` and QC advance; column 9 zero; daily wet `timepk` later draws `k10` | RNG, MODE, E2E |

## Daily equations and typed output fields

| Spec behavior or `DailyRow` field | Fortran unit and lines | Rust symbol | State / RNG stream | Evidence |
|---|---|---|---|---|
| Generated precipitation occurrence | `clgen` 1214-1221, 1275-1277 | `daily::gen_precip` | `prw[mo,l]`, batch `vvx` from `k1`; updates daily `l` | DAY, MODE, E2E |
| Generated precipitation amount, current-month skew mutation, zero-predecessor recovery, and 0.01-in floor | `clgen` 1232-1274 | `daily::gen_precip` | batch `v8x`/rolling `v7` from `k5`; recovery draws `k5` directly; `rst[mo][skew]` mutates | DAY, MODE, E2E |
| Generated correlated Tmax/Tmin/Tdew and Tmin correction | `clgen` 1346-1446 | `daily::temps_generated`, `temp_params` | rolling `k2`, `k3`, `k9` pairs; monthly/interpolated mean and SD state | DAY, MODE, E2E |
| Observed-temperature dew-point anchoring | `clgen` 1280-1345 | `daily::temps_observed`, `temp_params` | observed `tmxg`/`tmng`; rolling `k9` pair | DAY, MODE, E2E |
| Dew-point upper and `< -10 F` corrections; diagnostic is mode-independent | `clgen` 1457-1467 | `daily::clgen`; `ClgenEvents::tdew_low_rangecheck` | `tdp`, `tmxg`, `tmng`; no additional RNG | DAY, MODE, E2E |
| Solar astronomical bound | `clgen` 1185-1202 | `daily::solar_rmx` | Julian `ida`, fixed latitude sine/cosine; no RNG | DAY, MODE, E2E |
| Daily radiation with upper and 5%-of-bound floors | `clgen` 1469-1509 | `daily::gen_radiation` | batch `v6x`/rolling `v5` from `k4`; `obsl`, `stdsl`, `rmx` | DAY, MODE, E2E |
| Wind direction, calm residual, and radian wrapping | `windg` 2071-2102 | `daily::windg` | batch `fxx` from `k6`; cumulative `dir`; calm skips speed chain | DAY, MODE, E2E |
| Wind speed cubic transform, zero-skew mutation, and 0.1-m/s negative correction | `windg` 2103-2116 | `daily::windg` | batch `v10x`/rolling `v9` from `k8`; selected `wvl` sector | DAY, MODE, E2E |
| Dry normalization and first wet-day `alphb` duration draw | `day_gen` 3114-3127; `alphb` 3817-3895 | `storm::wet_day_duration`; `daily::alphb` | `r(ida)`, `wi[mo]`, first `k7`/`dstg` deviate; `dur` capped at 24 h | DAY, STM, MODE, E2E |
| Second independent `alphb`, time-to-peak, and peak-ratio chain | `tymax` data 602; `day_gen` 3138-3157; `timepk` 2188-2236; `alphb` 3817-3895 | `storm::storm_block`, `timepk`, `TYMAX`; `daily::alphb` | second `k7`/`dstg` deviate; `k10` batch/direct draw; `tymax`, Celsius mean temperature | DAY, STM, MODE, E2E |
| `jd`, `mo`, `iyear` | `day_gen` 3087-3088, row 3175-3176; year loop 3769-3803 | `modes::DailyRow`; `modes::day_gen` | calendar/caller state; no direct RNG | CAL, MODE, E2E |
| `xr` daily precipitation, mm | `day_gen` 3142, 3154 | `storm::storm_block`; `modes::DailyRow::xr` | generated `k1`/`k5` path or observed `irida`; conversion `r*25.4` | STM, MODE, E2E |
| `dur` duration, h | `day_gen` 3114-3127, row 3175 | `storm::wet_day_duration`; `DailyRow::dur` | first wet-day `k7`/`dstg` path; zero on dry days | DAY, STM, MODE, E2E |
| `tpr` time-to-peak fraction | `day_gen` 3139-3145, 3156; `timepk` 2217-2233 | `storm::timepk`, `storm_block`; `DailyRow::tpr` | `k10`: `zx[dax]` in option 5, fresh draw in option 6; zero when dry; cap 0.99 | STM, MODE, E2E |
| `xmav` maximum/mean intensity ratio | `day_gen` 3147-3155 | `storm::storm_block`; `DailyRow::xmav` | second wet-day `k7`/`dstg` path; `tymax`; temperature freeze/floor; zero when dry | STM, MODE, E2E |
| `tmxg`, `tmng`, Celsius | generation `clgen` 1280-1446; conversion `day_gen` 3107-3111 | `daily::temps_observed`/`temps_generated`; `DailyRow::{tmxg,tmng}` | observed fields or rolling `k2`/`k3`; F -> C after yearly-grid F snapshot | DAY, MODE, E2E |
| `radg`, Langley/day | `clgen` 1185-1202, 1469-1509; store 3113 | `daily::gen_radiation`; `DailyRow::radg` | rolling `k4` pair and solar bound | DAY, MODE, E2E |
| `wv`, m/s | `windg` 2071-2116; row 3176 | `daily::windg`; `DailyRow::wv` | `k6` direction selects calm/sector; non-calm speed uses rolling `k8` | DAY, MODE, E2E |
| `th`, degrees | `windg` 2071-2102; conversion `day_gen` 3104; row 3176 | `daily::windg`; `modes::day_gen`; `DailyRow::th` | batch direction `k6`; radians multiplied by source `57.296` | DAY, MODE, E2E |
| `tdp`, Celsius | `clgen` 1280-1467; conversion `day_gen` 3112; row 3176 | `daily::temps_observed`/`temps_generated`, `clgen`; `DailyRow::tdp` | rolling `k9` pair, observed/generated temperature anchors; F -> C | DAY, MODE, E2E |

## Profile and failure boundary

| Spec boundary | Fortran unit and lines | Rust symbol | State / RNG stream | Evidence |
|---|---|---|---|---|
| `faithful_5_32_3` plus faithful QC selects the source conditioner; `qc_filter: off` is a declared divergent profile choice | faithful baseline `ranset` 4002-4340 | `GenerationProfile::Faithful5323`; `QcFilter::Faithful`; `MonthlyBatchBackend` | faithful QC state and all source streams above | QC, E2E |
| Malformed `.par`, `.prn`, or runspec fails closed at the typed Rust boundary; no scientific default is inferred | source formatted-read surfaces `sta_parms` 2793-2883, `usr_opt` 3524-3575, `day_gen` 3052, 3067-3083 | `ParFile::parse`; `PrnReader::{new,initial_year,next}`; `runspec` validation | no generator draw occurs past a rejected intake operation | `par_state_identity::par_parse_fails_closed`; MODE parser rejection tests; `runspec_vectors` |

## Review disposition

The source/port/spec comparison found no unrepresented generated output field
or random stream. Draft findings covered the exact QC column/count rules,
current-month-only precipitation-skew mutation, mode-independent dew-point
diagnostic, station-wide `timpkd` CDF, scalar latitude/type dependencies,
`r5monb` guards, `dstg` retry arithmetic/state, continuous time-to-peak mask
mismatch, observed EOF flag reset, and in-scope evidence counts. The package
owner dispositioned those findings in the specification and traceability
artifacts; the independent review artifact records the final audit.
