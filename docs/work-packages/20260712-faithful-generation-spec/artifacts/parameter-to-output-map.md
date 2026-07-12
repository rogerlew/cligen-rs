# Station Parameter to Output Map

Status: static traceability artifact for `SPEC-FAITHFUL-GENERATION`.

## Scope and owners

This map covers every typed field read from records 1-83 of a legacy station
parameter file. The source read/distribution owner is `sta_dat` and
`sta_parms` (`reference/cligen532/cligen.f:2240-2480,2656-2967`). The Rust
read and distribution owners are `par::file::ParFile::parse` and
`par::sta_parms`. Records after 83 and the TP5 text in record 3 are not
station parameters in CLIGEN 5.32.3 because the source never reads them.

Daily-field abbreviations are the typed `modes::DailyRow` fields:

- `P`: `xr` precipitation (mm);
- `X/N/D`: `tmxg`, `tmng`, `tdp` (degrees C at the row boundary);
- `R`: `radg` (Langley/day);
- `V/A`: `wv` (m/s) and `th` (degrees);
- `U/T/I`: `dur` (h), `tpr` (fraction), and `xmav` (dimensionless).

“No daily effect” means no influence on a `DailyRow` in continuous or
observed mode. Some such fields still appear in the legacy `.cli` header,
station intake, or retained state.

## Scalar and identity fields

| Parameter (file units) | Load-time transformation / retained use | Daily output dependency | Interpolation | Source owner | Rust owner |
|---|---|---|---|---|---|
| `stidd` station name | retained verbatim | no daily effect; emitted in `.cli` header | none | record-1 reads `2430-2459`; header `3728-3729` | `ParFile::stidd`; `modes::run_to_cli`; `output::write_cli_header` |
| `nst` state code | intake/selection identity only | no daily effect or continuous `.cli` header field | none | `sta_dat:2285-2469` | `ParFile::nst`; `par::sta_dat` |
| `nstat` station code | intake/selection and legacy option-1/2/3 summary identity | no continuous/observed daily effect | none | `sta_dat:2285-2469`; `opt_calc:3196-3324` | `ParFile::nstat`; `par::sta_dat` |
| `igcode` wind/ET flag | retained; written to the three-integer `.cli` header record | no daily generator equation effect | none | record-1 read `2430-2459`; header `3723` | `ParFile::igcode`; `output::write_cli_header` |
| `ylt` latitude (degrees north) | `sin(ylt/57.296)` and `cos(ylt/57.296)` computed once | **R** through daily astronomical maximum `rmx` and its upper/lower clamps; also header | none | setup `885-887`; solar `1185-1202` | `StaParmsOut::ylt`; `modes::generation_setup`; `daily::solar_rmx` |
| `yll` longitude (degrees east) | retained | no daily effect; header only | none | read `2793`; header `3728-3729` | `StaParmsOut::yll`; `output::write_cli_header` |
| `years` observed record length | retained station metadata | does not control the simulated year count; header only | none | read `2793`; header `3728-3729` | `StaParmsOut::years`; `output::write_cli_header` |
| `itype` station storm type (1-4) | indexes fixed source peak-rate limits `tymax=[180.34,154.94,307.34,330.2]` mm/h | **I**: caps `r5p` on every positive-rain continuous/observed day before `xmav`; also used by deferred standalone storm modes | none | main DATA `602`; daily block `3147-3151` | `StaParmsOut::itype`; `storm::TYMAX`; `storm::storm_block` |
| `elev` (whole feet in file) | f32 multiply by `0.3048`, integer assignment truncates toward zero to metres | no daily effect; converted value appears in header | none | read/convert `2793,2884-2886`; header `3728-3729` | `ParFile::elev_ft`; `StaParmsOut::elev`; `output::write_cli_header` |
| `tp6` maximum 6-hour precipitation (in) | retained; the old `r5mon(tp6)` call is commented out | no daily effect in `iopt=5/6` | none | read `2793`; dead call near `877`; old `r5mon:1904-1978` | `ParFile::tp6`; `StaParmsOut::tp6` |

## Monthly precipitation, temperature, radiation, and dew-point fields

All values below contain 12 calendar-month entries. `sta_parms` prepares
Fourier/Yoder-Foster state for indices 1-14 when selected, but generation
calls evaluators only for indices 1-3, 6-11, and 13.

| Parameter (file units) | Transformations and equation role | Generated fields | Generation-time interpolation | Source owner | Rust owner |
|---|---|---|---|---|---|
| `rst(:,1)` wet-day P mean (in) | wet generated amount location; zero guarded to `0.001` only in `r5monb` denominator; also combines with `prw` in header monthly precipitation | **P**; indirectly **U/I** through final rain and `wi` ratio | index 1: none/fixed month, linear, Fourier, or Yoder-Foster at wet-amount site; `r5monb` and header always use fixed monthly value | read `2794-2795`; daily `1258-1274`; `r5monb:3898-4001`; header `3741-3746` | `ParFile::rst`; `Cbk7State::rst`; `daily::{gen_precip,r5monb}`; `output::write_cli_header` |
| `rst(:,2)` wet-day P SD (in) | scale of Pearson-III-style wet amount | **P**, hence **U/I** | index 2: all four daily interpolation modes at wet-amount site | read `2794-2795`; daily `1258-1274` | `daily::gen_precip` |
| `rst(:,3)` wet-day P skew | current calendar month's stored value is clamped to `[-4.5,4.5]` on a generated wet day; effective zero becomes local `0.01`; cubic shape transform | **P**, hence **U/I** | index 3: none uses the clamped current value; linear blends that value with an adjacent value not clamped by this step; Fourier/Yoder-Foster use load-time coefficients prepared before any daily clamp | read `2794-2795`; setup `2829-2868`; daily `1232-1257` | `daily::gen_precip`; `monthlies::{fouri1/fouri2,ryf1/ryf2}` |
| `prw(:,1)` P(wet\|wet) | daily generated occurrence threshold indexed by `l`; also expected-wet-day calculation in `r5monb` and header; refill-time amount mask indexed by `ell` | **P**, hence **U/T/I**; changes availability/trajectory of `k5` and continuous `k10` batches | fixed calendar month only. Index-4 Fourier/Yoder-Foster setup exists but no evaluator call | read `2796`; occurrence `1214-1221`; `ranset:4140-4182`; `r5monb:3898-4001`; header `3741-3746` | `Cbk7State::prw`; `daily::{gen_precip,r5monb}`; `rng::ranset`; `output::write_cli_header` |
| `prw(:,2)` P(wet\|dry) | same paths as `prw(:,1)` for the dry predecessor; zero uses source wet-day guard `0.0006944` in `r5monb` | **P**, hence **U/T/I**; random-batch trajectory | fixed calendar month only. Index-5 setup is unused at generation time | same as preceding row | same as preceding row |
| `obmx` monthly Tmax mean (degrees F) | generated Tmax mean/delta; observed-temperature dew-point offset/branch inputs; Rankine CV `cvtx=stdtx/(obmx+459.67)` derived but not used by daily equations; header converts to C | **X** when temperatures generated; **D** on all days; **I** through generated X/N freezing override; header | index 6: all four daily interpolation modes | read `2797`; CV `2894-2898`; temperature blocks `1280-1446`; header `3747-3752` | `Cbk7State::obmx`; `par::sta_parms`; `daily::{temp_params,temps_observed,temps_generated}`; `output::write_cli_header` |
| `obmn` monthly Tmin mean (degrees F) | generated Tmin mean/delta and dew-point anchoring; derives unused daily `cvtm`; header converts to C | **N** when temperatures generated; **D** on all days; **I** through generated X/N freezing override; header | index 7: all four daily interpolation modes | read `2798`; CV `2894-2898`; temperature blocks `1280-1446`; header `3747-3752` | corresponding `obmn` owners in `Cbk7State`, `par::sta_parms`, and `daily` |
| `stdtx` Tmax daily SD (degrees F) | selects smaller-SD branch and scales generated Tmax/delta and dew point; derives `cvtx`, which daily generation does not read | **X** when generated; **N** through paired construction; **D** on all days; **I** through generated X/N freezing override | index 8: all four daily interpolation modes | read `2799`; temperature blocks `1280-1446` | `Cbk7State::stdtx`; `daily::{temp_params,temps_observed,temps_generated}` |
| `stdtm` Tmin daily SD (degrees F) | selects branch and scales paired temperature/dew-point equations; derives unused `cvtm` | **N** when generated; **X** through paired construction; **D** on all days; **I** through generated X/N freezing override | index 9: all four daily interpolation modes | read `2799`; temperature blocks `1280-1446` | corresponding `stdtm` owners in `Cbk7State` and `daily` |
| `obsl` mean solar radiation (Langley/day) | daily normal location; derives `cvs=stdsl/obsl` with `obsl<=0 -> 0`, but daily generation does not read `cvs`; emitted in header | **R**; header | index 10: all four daily interpolation modes | read `2800`; CV `2899-2903`; radiation `1469-1509`; header `3752` | `Cbk7State::obsl`; `par::sta_parms`; `daily::gen_radiation`; `output::write_cli_header` |
| `stdsl` radiation SD (Langley/day) | daily normal scale; participates in derived but unused `cvs` | **R** | index 11: all four daily interpolation modes | read `2801`; radiation `1469-1509` | `Cbk7State::stdsl`; `daily::gen_radiation` |
| `wi` max 30-minute P intensity (in/h in file) | multiply by `0.5` to depth (in); `r5monb` circular three-month smooth plus expected-wet-day and wet-mean normalization overwrites it with dimensionless monthly max-30-min/total-P ratios; `alphb` uses current month | **U/I** on positive-rain days; no effect on occurrence or daily P depth | fixed calendar month in `r5monb`/`alphb`. Index-12 Fourier/Yoder-Foster setup is computed on halved depths but never evaluated | read/halve `2802-2812`; `r5monb:3898-4001`; `alphb:3817-3895` | `ParFile::wi_raw`; `Cbk9State::wi`; `par::sta_parms`; `daily::{r5monb,alphb}` |
| `rh` mean dew point (degrees F) | mean/offset in observed and generated dew-point constructions; final dew-point clamps also depend on resulting X/N | **D** | index 13: all four daily interpolation modes | read `2814`; dew point `1311-1320,1390-1399` | `Cbk1State::rh`; `daily::{temp_params,temps_observed,temps_generated}` |
| `timpkd(1:12)` cumulative time-to-peak CDF | caller prepends `timpkd(0)=0`; `timepk` selects/interpolates a 1/12 bin; values above resulting `tpr=0.99` are clamped by caller | **T** on positive-rain days | fixed station CDF. Index-14 setup is behaviorally unused and, due to the array-name/lower-bound quirk, receives `[0,timpkd(1:11)]`, excluding December | read `2815`; setup `2844,2859`; `timepk:2188-2236` | `StaParmsOut::timpkd`; `par::sta_parms`; `storm::timepk` |

### Interpolation index summary

| Index | Parameter | Daily evaluator called? | Other fixed-month use |
|---:|---|---|---|
| 1-3 | P wet mean/SD/skew | yes | mean also in `r5monb` and header |
| 4-5 | wet transition probabilities | no | occurrence, refill mask, `r5monb`, header |
| 6-9 | Tmax/Tmin means/SDs | yes | means also in header |
| 10-11 | radiation mean/SD | yes | mean also in header |
| 12 | max-30-minute depth/ratio | no | `r5monb`, then `alphb` |
| 13 | dew-point mean | yes | none |
| 14 | time-to-peak CDF | no | `timepk` |

The four interpolation choices therefore alter only the “yes” rows. The
existence of prepared coefficient state is not evidence that CLIGEN consumes
it.

## Wind and retained interpolation metadata

Each `wvl` family is a 16-direction by 12-month array. Wind generation uses
the current calendar month unchanged; it has no monthly interpolation path.

| Parameter (file units) | Transformations and branch role | Generated fields | Source owner | Rust owner |
|---|---|---|---|---|
| `wvl(:,1,:)` directional frequency (%) | cumulatively sum directions 1-16 and scale by `0.01` into `dir`; `dir(:,17)=1` is prepared but `windg` searches only 1-16 with strict `>` | **A** direction sector/within-sector position; residual above cumulative direction 16 produces calm and thus **V=0,A=0** | read `2881`; derive `2910-2925`; select `2071-2101` | `Cbk1State::{wvl,dir}`; `par::sta_parms`; `daily::windg` |
| `wvl(:,2,:)` directional mean speed (m/s) | location for selected sector's skew transform | **V** | read `2881`; speed `2103-2114` | `Cbk1State::wvl`; `daily::windg` |
| `wvl(:,3,:)` directional speed SD (m/s) | scale for selected sector | **V** | same | same |
| `wvl(:,4,:)` directional speed skew | selected zero is changed in stored state to `0.01`; cubic transform; negative generated speed becomes `0.1 m/s` | **V** | same | same |
| `calm(:)` monthly calm percentage | parsed and copied to state, but never read by `windg`; faithful calm probability is the residual `1-dir(month,16)` implied by directional frequencies | no effect if changed alone | read `2882`; source's calm branch `2081-2088` reads only `dir` | `ParFile::calm`; `Cbk1State::calm`; `par::sta_parms` (no daily consumer) |
| `site(1:3)` wind-station names | retained/read for optional station-data display; no runtime interpolation is performed | no daily effect | read `2883`; display `2961` | `ParFile::site`; `StaParmsOut::site` |
| `wgt(1:3)` wind-station weights | retained/read for optional display; not applied to `wvl` | no daily effect | read `2883`; display `2961` | `ParFile::wgt`; `StaParmsOut::wgt` |

## Output dependency summary

| Daily field | Station parameters that can affect it |
|---|---|
| `xr` P | `rst(:,1:3)`, `prw(:,1:2)`; observed mode may substitute P completely |
| `tmxg` X | `obmx`, `obmn`, `stdtx`, `stdtm`; observed mode may substitute both temperatures |
| `tmng` N | `obmx`, `obmn`, `stdtx`, `stdtm`; observed mode may substitute both temperatures |
| `tdp` D | `rh`, `obmx`, `obmn`, `stdtx`, `stdtm`, plus final X/N anchors whether observed or generated |
| `radg` R | `ylt`, `obsl`, `stdsl` |
| `wv` V | `wvl(:,1:4,:)`; the directional frequencies also choose calm |
| `th` A | `wvl(:,1,:)` through `dir` |
| `dur` U | final P plus transformed `wi`; the `wi` transformation also consumes `prw(:,1:2)` and `rst(:,1)` |
| `tpr` T | `timpkd` when final P is positive; in continuous mode `prw` also affects generated occurrence and the `k10` batch mask/trajectory |
| `xmav` I | final P, transformed `wi`, and `itype`; final X/N control the freezing override; the `wi` transformation also consumes `prw(:,1:2)` and `rst(:,1)` |

Parameters absent from this summary have no continuous/observed daily-model
effect. This distinction is important for a modern schema: preserving byte
parity of headers and provenance can require metadata that is not a climate
equation input, while a faithful-equivalent model schema must preserve every
live parameter and its fixed-month/interpolated status exactly.
