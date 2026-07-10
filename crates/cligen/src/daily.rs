//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:1094-1515 (`clgen`),
//!   2020-2122 (`windg`), 3817-3897 (`alphb`), and 3898-4001
//!   (`r5monb`).
//! Precision-Map: REAL*4 throughout (census: transcendental-census.md;
//!   no f64 site, no SAVE state)
//! Faithful-Acceptance: per-unit and combined sequential replay against
//!   the cg/wg/ab/r5 tap streams (fixtures/taps/daily/,
//!   tests/daily_identity.rs) — entry seed/rolling-state assertions
//!   localize any desync to the record
//!
//! Transcendental adjudication (standard §1.3, Ran 2026-07-09,
//! transcendental-census.md): the solar geometry routes through
//! `libm_pinned::{sinf_pinned, cosf_pinned, tanf_pinned, acosf_pinned,
//! expf_pinned, logf_pinned}` — the `libm` crate's `tanf`/`acosf`/
//! `expf` were REJECTED against the reference runtime (2.06% / 79.6% /
//! 0.69% sweep divergence); `logf_pinned` was adjudicated by the RNG
//! package.
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `ntd` | `ntd` | days in this year | day |
//! | `iyear` | `iyear` | simulation year index (ranset input) | yr |
//! | `sd` | `sd` | solar declination angle | rad |
//! | `ch`,`h` | same | cos(half-day length) and its clamped acos | — / rad |
//! | `ys`,`yc` | same | latitude/declination products | — |
//! | `rmx` | `rmx` | max possible solar radiation for the day | Langley/day |
//! | `vv` | `vv` | precip-occurrence uniform (batch column 1) | — |
//! | `xlv` | `xlv` | Pearson-III standardized deviate (cube transform) | — |
//! | `r6` | `r6` | skew/6 | — |
//! | `tmpvr1..tmpv13` | same | interp-dispatched monthly parameters | param units |
//! | `twiddle`,`twiddld` | same | SD-delta and mean-delta anchors (2004 Tmax/Tmin/Tdew correlation scheme) | param units |
//! | `xx` | `xx` | literal 1.0 scale on every dstn1 result (source shape) | — |
//! | `dax` | `dax` | day-of-month cursor into the ranary batch | day |
//! | `fx` | `fx` | wind-direction uniform (batch column 6) | — |
//! | `wv`,`th` | same | generated wind speed and direction | m/s / rad |
//! | `ei` | `ei` | liquid daily precipitation above snowmelt | in |
//! | `ai` | `ai` | gamma scaling parameter for `dstg` | — |
//! | `ajp` | `ajp` | precipitation-dependent upper bound for alpha | — |
//! | `sm` | `sm(12)` | three-month-smoothed maximum 30-minute rain | in |
//! | `smm` | `smm(12)` | expected wet days per month | day |
//! | `r25` | `r25` | mean rain per wet day, guarded above zero | in/day |

use crate::cbk1::Cbk1State;
use crate::cbk3::Cbk3State;
use crate::cbk4::Cbk4State;
use crate::cbk5::Cbk5State;
use crate::cbk7::Cbk7State;
use crate::cbk9::Cbk9State;
use crate::cinterp::CinterpState;
use crate::crandom3::Crandom3State;
use crate::deviates::{dstg, dstn1, DstgState};
use crate::libm_pinned::{
    acosf_pinned, cosf_pinned, expf_pinned, logf_pinned, sinf_pinned, tanf_pinned,
};
use crate::monthlies::{fouri2, ryf2};
use crate::rng::{randn, ranset, RansetState};

use crate::acm::AcmState;

/// Screen-side events `clgen` raises on ranges the source reports to
/// stdout (`cligen.f:1466`). The port surfaces them as data instead of
/// printing; the clamp behavior itself is faithful.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct ClgenEvents {
    /// "Tdew -10 rangecheck executed." — fires in the golden fixtures
    /// (7-11 times per new-meadows run).
    pub tdew_low_rangecheck: bool,
}

/// Interpolation dispatch shared by every `clgen` parameter site
/// (`cligen.f:1240-1248` and its five repetitions). The source repeats
/// this four-branch block verbatim per parameter; the port factors it
/// with identical per-branch arithmetic (`direct`/`other` are the
/// `(mo)`/`(o_mo)` monthly values; `p` the cinterp parameter index).
#[allow(clippy::too_many_arguments)]
fn interp_val(
    ci: &CinterpState,
    mo: i32,
    dax: i32,
    ntd: i32,
    ida: i32,
    p: usize,
    direct: f32,
    other: f32,
) -> f32 {
    if ci.interp == 1 {
        direct * ci.lf + other * ci.rf
    } else if ci.interp == 2 {
        fouri2(p, ida, ci)
    } else if ci.interp == 3 {
        ryf2(mo, dax, ntd, p, ci)
    } else {
        direct
    }
}

/// Solar geometry (`cligen.f:1185-1202`): declination from the Julian
/// day, half-day length with the ±1 clamp before `acos`, max possible
/// radiation.
// The source literal `3.1416` (cligen.f:1192) resembles PI but is the
// specification's constant.
#[allow(clippy::approx_constant)]
fn solar_rmx(ida: i32, bk7: &Cbk7State) -> f32 {
    let xi = ida as f32;
    let sd = 0.4102 * sinf_pinned((xi - 80.25) / bk7.pit);
    let ch = -bk7.yls * tanf_pinned(sd) / bk7.ylc;
    let h = if ch >= 1.0 {
        0.0
    } else if ch <= -1.0 {
        3.1416
    } else {
        acosf_pinned(ch)
    };
    let ys = bk7.yls * sinf_pinned(sd);
    let yc = bk7.ylc * cosf_pinned(sd);
    711.0 * (h * ys + yc * sinf_pinned(h))
}

/// Precipitation block (`cligen.f:1214-1277`), `nsim ≠ 0` only.
#[allow(clippy::too_many_arguments)]
fn gen_precip(
    ntd: i32,
    mo: i32,
    ida: i32,
    bk5: &mut Cbk5State,
    bk7: &mut Cbk7State,
    ci: &CinterpState,
    cr: &mut Crandom3State,
) {
    let m = (mo - 1) as usize;
    cr.vv = cr.vvx(cr.dax as usize);
    let l = bk7.l as usize;
    if bk7.prw[m][l - 1] <= 0.0 || cr.vv > bk7.prw[m][l - 1] {
        bk5.r[(ida - 1) as usize] = 0.0;
        bk7.l = 2;
    } else {
        let v8 = cr.v8x(cr.dax as usize);
        // Skewness range check mutates the station state in place
        // (cligen.f:1237-1238); sequential ifs are the source shape.
        #[allow(clippy::manual_clamp)]
        {
            if bk7.rst[m][2] > 4.5 {
                bk7.rst[m][2] = 4.5;
            }
            if bk7.rst[m][2] < -4.5 {
                bk7.rst[m][2] = -4.5;
            }
        }
        // `other` is only consumed when interp = 1, where lintrp
        // guarantees o_mo in 1..=12; rem_euclid keeps the eager read
        // in-bounds for the other modes (value unused there — the
        // Fortran never evaluates rst(o_mo,·) outside the interp-1
        // branch).
        let o = (ci.o_mo - 1).rem_euclid(12) as usize;
        let mut tmpvr3 = interp_val(ci, mo, cr.dax, ntd, ida, 3, bk7.rst[m][2], bk7.rst[o][2]);
        if tmpvr3 == 0.0 {
            tmpvr3 = 0.01;
        }
        let r6 = tmpvr3 / 6.0;
        // Band-aid draw (cligen.f:1253) — the reason ranset's replay
        // treats k5 as externally advanced.
        if bk7.v7 == 0.0 {
            bk7.v7 = randn(&mut bk7.k5);
        }
        let mut xlv = (dstn1(bk7.v7, v8) - r6) * r6 + 1.0;
        // x**3 expands to left-associated multiplies at -O0.
        xlv = (xlv * xlv * xlv - 1.0) * 2.0 / tmpvr3;
        bk7.v7 = v8;
        let tmpvr1 = interp_val(ci, mo, cr.dax, ntd, ida, 1, bk7.rst[m][0], bk7.rst[o][0]);
        let tmpvr2 = interp_val(ci, mo, cr.dax, ntd, ida, 2, bk7.rst[m][1], bk7.rst[o][1]);
        let rida = xlv * tmpvr2 + tmpvr1;
        bk5.r[(ida - 1) as usize] = if rida < 0.01 { 0.01 } else { rida };
        bk7.l = 1;
    }
}

/// The four temperature/dew-point monthly parameters (6, 8, 7, 9) and
/// the dew-point mean (13), interp-dispatched (`cligen.f:1286-1320`,
/// repeated verbatim at 1368-1399).
fn temp_params(
    mo: i32,
    dax: i32,
    ntd: i32,
    ida: i32,
    bk1: &Cbk1State,
    bk7: &Cbk7State,
    ci: &CinterpState,
) -> (f32, f32, f32, f32, f32) {
    let m = (mo - 1) as usize;
    let o = (ci.o_mo - 1).rem_euclid(12) as usize;
    let tmpvr6 = interp_val(ci, mo, dax, ntd, ida, 6, bk7.obmx[m], bk7.obmx[o]);
    let tmpvr8 = interp_val(ci, mo, dax, ntd, ida, 8, bk7.stdtx[m], bk7.stdtx[o]);
    let tmpvr7 = interp_val(ci, mo, dax, ntd, ida, 7, bk7.obmn[m], bk7.obmn[o]);
    let tmpvr9 = interp_val(ci, mo, dax, ntd, ida, 9, bk7.stdtm[m], bk7.stdtm[o]);
    let tmpv13 = interp_val(ci, mo, dax, ntd, ida, 13, bk1.rh[m], bk1.rh[o]);
    (tmpvr6, tmpvr8, tmpvr7, tmpvr9, tmpv13)
}

/// Observed-temperature branch (`cligen.f:1280-1345`, `msim = 0`):
/// dew point only, anchored to the observed `tmng`/`tmxg`.
fn temps_observed(
    ntd: i32,
    mo: i32,
    ida: i32,
    bk1: &mut Cbk1State,
    bk7: &mut Cbk7State,
    ci: &CinterpState,
    cr: &Crandom3State,
) {
    let xx = 1.0f32;
    let v12 = cr.v12x(cr.dax as usize);
    bk1.tdp = xx * dstn1(bk7.v11, v12);
    bk7.v11 = v12;
    let (tmpvr6, tmpvr8, tmpvr7, tmpvr9, tmpv13) = temp_params(mo, cr.dax, ntd, ida, bk1, bk7, ci);
    if tmpvr8 >= tmpvr9 {
        // The first twiddle/twiddld pair is computed and immediately
        // shadowed, exactly as the source's dead stores
        // (cligen.f:1324-1326).
        let _twiddle = (tmpvr8 * tmpvr8 - tmpvr9 * tmpvr9).sqrt();
        let _twiddld = tmpvr6 - tmpvr7;
        let twiddle = (((tmpvr8 + tmpvr9) / 2.0) * ((tmpvr8 + tmpvr9) / 2.0) - tmpvr9 * tmpvr9)
            .abs()
            .sqrt();
        let twiddld = tmpv13 - tmpvr7;
        bk1.tdp = bk7.tmng + twiddld + bk1.tdp * twiddle;
    } else {
        let _twiddle = (tmpvr9 * tmpvr9 - tmpvr8 * tmpvr8).sqrt();
        let _twiddld = tmpvr6 - tmpvr7;
        let twiddle = (((tmpvr8 + tmpvr9) / 2.0) * ((tmpvr8 + tmpvr9) / 2.0) - tmpvr8 * tmpvr8)
            .abs()
            .sqrt();
        let twiddld = tmpvr6 - tmpv13;
        bk1.tdp = bk7.tmxg - twiddld + bk1.tdp * twiddle;
    }
}

/// Generated-temperature branch (`cligen.f:1346-1446`, `msim ≠ 0`):
/// Tmax/Tmin/Tdew from the rolling pairs, anchored per the 2004
/// smaller-SD scheme, with the Tmin range check.
fn temps_generated(
    ntd: i32,
    mo: i32,
    ida: i32,
    bk1: &mut Cbk1State,
    bk7: &mut Cbk7State,
    ci: &CinterpState,
    cr: &Crandom3State,
) {
    let xx = 1.0f32;
    let v2 = cr.v2x(cr.dax as usize);
    bk7.tmxg = xx * dstn1(bk7.v1, v2);
    bk7.v1 = v2;
    let v4 = cr.v4x(cr.dax as usize);
    bk7.tmng = xx * dstn1(bk7.v3, v4);
    let v12 = cr.v12x(cr.dax as usize);
    bk1.tdp = xx * dstn1(bk7.v11, v12);
    bk7.v3 = v4;
    bk7.v11 = v12;
    let (tmpvr6, tmpvr8, tmpvr7, tmpvr9, tmpv13) = temp_params(mo, cr.dax, ntd, ida, bk1, bk7, ci);
    if tmpvr8 >= tmpvr9 {
        bk7.tmng = tmpvr7 + bk7.tmng * tmpvr9;
        let twiddle = (tmpvr8 * tmpvr8 - tmpvr9 * tmpvr9).sqrt();
        let twiddld = tmpvr6 - tmpvr7;
        bk7.tmxg = bk7.tmng + twiddld + bk7.tmxg * twiddle;
        let twiddle = (((tmpvr8 + tmpvr9) / 2.0) * ((tmpvr8 + tmpvr9) / 2.0) - tmpvr9 * tmpvr9)
            .abs()
            .sqrt();
        let twiddld = tmpv13 - tmpvr7;
        bk1.tdp = bk7.tmng + twiddld + bk1.tdp * twiddle;
    } else {
        bk7.tmxg = tmpvr6 + bk7.tmxg * tmpvr8;
        let twiddle = (tmpvr9 * tmpvr9 - tmpvr8 * tmpvr8).sqrt();
        let twiddld = tmpvr6 - tmpvr7;
        bk7.tmng = bk7.tmxg - twiddld - bk7.tmng * twiddle;
        let twiddle = (((tmpvr8 + tmpvr9) / 2.0) * ((tmpvr8 + tmpvr9) / 2.0) - tmpvr8 * tmpvr8)
            .abs()
            .sqrt();
        let twiddld = tmpvr6 - tmpv13;
        bk1.tdp = bk7.tmxg - twiddld + bk1.tdp * twiddle;
    }
    // Range check (cligen.f:1445).
    if bk7.tmng > bk7.tmxg {
        bk7.tmng = bk7.tmxg - 0.2 * bk7.tmxg.abs();
    }
}

/// Radiation block (`cligen.f:1469-1509`) plus the rolling shift.
fn gen_radiation(
    ntd: i32,
    mo: i32,
    ida: i32,
    bk7: &mut Cbk7State,
    ci: &CinterpState,
    cr: &Crandom3State,
) {
    let xx = 1.0f32;
    let m = (mo - 1) as usize;
    let o = (ci.o_mo - 1).rem_euclid(12) as usize;
    let v6 = cr.v6x(cr.dax as usize);
    bk7.ra = xx * dstn1(bk7.v5, v6);
    let tmpv10 = interp_val(ci, mo, cr.dax, ntd, ida, 10, bk7.obsl[m], bk7.obsl[o]);
    let tmpv11 = interp_val(ci, mo, cr.dax, ntd, ida, 11, bk7.stdsl[m], bk7.stdsl[o]);
    bk7.ra = tmpv10 + bk7.ra * tmpv11;
    if bk7.ra > bk7.rmx {
        bk7.ra = bk7.rmx;
    }
    if bk7.ra < bk7.rmx * 0.05 {
        bk7.ra = 0.05 * bk7.rmx;
    }
    bk7.v5 = v6;
}

/// Faithful `clgen` (`cligen.f:1094-1515`): the daily generator.
/// Consumes the batch columns at `dax`, calls the ported `ranset` at
/// month boundaries, and writes the generated surface
/// (`r(ida)`/`tmxg`/`tmng`/`tdp`/`ra`/`rmx`) plus the rolling-pair and
/// Markov state.
///
/// # Numerics
/// REAL*4 throughout; interp dispatch per parameter; `x**3`/`x**2`
/// expand to multiplies; ranges clamp exactly as the source. The
/// "Tdew -10" screen message becomes [`ClgenEvents`].
#[allow(clippy::too_many_arguments)]
pub fn clgen(
    ntd: i32,
    iyear: i32,
    bk1: &mut Cbk1State,
    bk3: &Cbk3State,
    bk4: &Cbk4State,
    bk5: &mut Cbk5State,
    bk7: &mut Cbk7State,
    ci: &CinterpState,
    cr: &mut Crandom3State,
    rs: &mut RansetState,
    acm: &mut AcmState,
) -> ClgenEvents {
    let mo = bk4.mo;
    let ida = bk3.ida;
    bk7.rmx = solar_rmx(ida, bk7);

    // Month boundary: regenerate the batch (cligen.f:1206-1212).
    if mo != cr.mox {
        cr.mox = mo;
        cr.dax = 1;
        ranset(ntd, iyear, bk4, bk7, rs, acm, cr);
    } else {
        cr.dax += 1;
    }

    if bk7.nsim != 0 {
        gen_precip(ntd, mo, ida, bk5, bk7, ci, cr);
    }

    if bk7.msim == 0 {
        temps_observed(ntd, mo, ida, bk1, bk7, ci, cr);
    } else {
        temps_generated(ntd, mo, ida, bk1, bk7, ci, cr);
    }

    // Dew-point range checks (cligen.f:1464-1467).
    if bk1.tdp > 0.99 * (bk7.tmxg + bk7.tmng) / 2.0 {
        bk1.tdp = ((bk7.tmxg + bk7.tmng) / 2.0) * 0.99;
    }
    let mut events = ClgenEvents::default();
    if bk1.tdp < -10.0 {
        events.tdew_low_rangecheck = true;
        bk1.tdp = 1.1 * bk7.tmng;
    }

    gen_radiation(ntd, mo, ida, bk7, ci, cr);
    events
}

/// Faithful daily wind generator (`cligen.f:2020-2119`).
/// Selects a direction from the monthly cumulative distribution, then
/// generates speed from the corresponding rolling normal pair. The
/// source's zero-skew guard mutates the station `wvl` value in place.
///
/// # Units
/// Writes `bk1.wv` in m/s and `bk1.th` in radians from north.
///
/// # Numerics
/// REAL*4 throughout. The Pearson-III cube is evaluated as three
/// left-associated f32 multiplies; `dstn1` supplies the only
/// transcendental work through its already-adjudicated pinned path.
pub fn windg(
    bk1: &mut Cbk1State,
    bk3: &mut Cbk3State,
    bk4: &Cbk4State,
    bk7: &mut Cbk7State,
    cr: &mut Crandom3State,
) {
    let m = (bk4.mo - 1) as usize;
    cr.fx = cr.fxx(cr.dax as usize);
    let mut ndflag = 0;
    bk3.j = 0;
    loop {
        bk3.j += 1;
        if bk1.dir[m][(bk3.j - 1) as usize] > cr.fx {
            ndflag = 2;
        }
        if ndflag != 0 || bk3.j >= 16 {
            break;
        }
    }

    if ndflag == 0 {
        bk1.wv = 0.0;
        bk1.th = 0.0;
        return;
    }

    let j = (bk3.j - 1) as usize;
    let j1 = bk3.j - 1;
    let g = if bk3.j == 1 {
        cr.fx / bk1.dir[m][j]
    } else {
        (cr.fx - bk1.dir[m][j - 1]) / (bk1.dir[m][j] - bk1.dir[m][j - 1])
    };
    let xj1 = j1 as f32;
    bk1.th = bk1.pi2 * (g + xj1 - 0.5) / 16.0;
    if bk1.th < 0.0 {
        // Preserve the source operand order (cligen.f:2101).
        #[allow(clippy::assign_op_pattern)]
        {
            bk1.th = bk1.pi2 + bk1.th;
        }
    }

    let v10 = cr.v10x(cr.dax as usize);
    if bk1.wvl[j][3][m] == 0.0 {
        bk1.wvl[j][3][m] = 0.01;
    }
    let r6 = bk1.wvl[j][3][m] / 6.0;
    let mut xlv = (dstn1(bk7.v9, v10) - r6) * r6 + 1.0;
    xlv = (xlv * xlv * xlv - 1.0) * 2.0 / bk1.wvl[j][3][m];
    bk7.v9 = v10;
    bk1.wv = xlv * bk1.wvl[j][2][m] + bk1.wvl[j][1][m];
    if bk1.wv < 0.0 {
        bk1.wv = 0.1;
    }
}

/// Faithful Bofu Yu alpha generator (`cligen.f:3817-3895`).
/// Consumes one `dstg` deviate from `k7` and writes the event's
/// maximum-30-minute / total-rain ratio to `bk9.r1`.
///
/// # Units
/// Reads daily precipitation and snowmelt in inches; writes a
/// dimensionless ratio.
///
/// # Numerics
/// REAL*4 outside `dstg`'s source-declared f64 island. The f32
/// exponential uses the adjudicated ARM transcription
/// [`expf_pinned`].
pub fn alphb(
    bk3: &Cbk3State,
    bk4: &Cbk4State,
    bk5: &Cbk5State,
    bk7: &mut Cbk7State,
    bk9: &mut Cbk9State,
    dg: &mut DstgState,
    cr: &mut Crandom3State,
) {
    let r = bk5.r[(bk3.ida - 1) as usize];
    assert!(r > 0.0, "alphb requires positive daily precipitation");
    let ei = r - bk5.sml;
    let ai = bk9.ab1 / (bk9.wi[(bk4.mo - 1) as usize] - bk9.ab);
    let ajp = if ei < 1.0 {
        1.0
    } else {
        let tmax = 125.0 / 25.4;
        1.0 - expf_pinned(-tmax / ei)
    };
    bk9.r1 = dstg(ai, &mut bk7.k7, dg, cr);
    bk9.r1 = (ei * (bk9.ab + bk9.r1 * (ajp - bk9.ab)) + bk5.sml * bk9.ab) / r;
}

/// Faithful once-per-run monthly maximum-30-minute-rain conversion
/// (`cligen.f:3898-3996`). Smooths the station values and overwrites
/// `bk9.wi` in place with the monthly `R30 / R` ratios.
///
/// # Units
/// Reads and writes precipitation depth in inches; the final `wi`
/// values are dimensionless ratios.
///
/// # Numerics
/// REAL*4 throughout. `alog(f)` routes through the adjudicated ARM
/// transcription [`logf_pinned`].
pub fn r5monb(bk4: &Cbk4State, bk7: &Cbk7State, bk9: &mut Cbk9State) {
    let mut sm = [0.0f32; 12];
    sm[0] = (bk9.wi[11] + bk9.wi[0] + bk9.wi[1]) / 3.0;
    for (i, value) in sm.iter_mut().enumerate().take(11).skip(1) {
        *value = (bk9.wi[i - 1] + bk9.wi[i] + bk9.wi[i + 1]) / 3.0;
    }
    sm[11] = (bk9.wi[10] + bk9.wi[11] + bk9.wi[0]) / 3.0;

    for (i, sm_i) in sm.iter().enumerate() {
        let smm = if bk7.prw[i][1] == 0.0 {
            0.0006944
        } else {
            let xm = (bk4.nc[i + 1] - bk4.nc[i]) as f32;
            xm * bk7.prw[i][1] / (1.0 - bk7.prw[i][0] + bk7.prw[i][1])
        };
        let r25 = if bk7.rst[i][0] == 0.0 {
            0.001
        } else {
            bk7.rst[i][0]
        };
        let mut f = 1.0 / (smm + 0.5);
        f = -1.0 / logf_pinned(f);
        if f > 1.0 || f <= 0.0 {
            bk9.wi[i] = *sm_i;
        } else {
            bk9.wi[i] = f * *sm_i;
        }
        bk9.wi[i] /= r25;
    }
}
