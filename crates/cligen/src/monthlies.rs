//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:7252-7657 (`lintrp`,
//!   `fouri1`, `fouri2`, `ryf1`, `ryf2`)
//! Precision-Map: REAL*4 throughout (no f64 site exists in these units)
//! Faithful-Acceptance: par-state snapshot identity — the -I2 snapshots
//!   pin fouri1's x_bar/c/t and the -I3 snapshots pin ryf1's
//!   emv/pmt/pmv/xes for all four stations
//!   — plus per-record fouri2/ryf2/lintrp tap identity
//!   (fixtures/taps/par/, tests/par_state_identity.rs)
//!
//! Transcendental adjudication (standard §1.3, Ran 2026-07-09):
//! f32 `sin`/`cos`/`atan` go through `libm_pinned::{sinf_pinned,
//! cosf_pinned, atanf_pinned}`. `libm::atanf` was tried first and
//! REJECTED — it carries the 5-term reduced float polynomial and
//! diverged from the reference runtime by 1 ULP on a captured `fouri1`
//! composition (input bits 0xBE794977); glibc 2.39 ships the 11-term
//! fdlibm `s_atanf.c`, transcribed as `atanf_pinned` and verified
//! against the reference libm on a 3.7M-input sweep plus all captured
//! snapshot compositions (evidence in the par package's
//! gate-results.md).
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `x` | `x(12)` | the 12 monthly values of one parameter (for parameter 14 the shifted `timpkd(0:11)` window — see SPEC-PAR) | param units |
//! | `indpar` | `indpar` | 1-based parameter index (1..14, cinterp glossary) | — |
//! | `s`,`x_bar` | same | sum / mean of the monthly values | param units |
//! | `suma`,`sumb` | same | cosine / sine Fourier accumulators | param units |
//! | `a`,`b`,`v` | same | scaled coefficients / harmonic phase argument | — / rad |
//! | `dim` | `dim(12)` | days per month, non-leap | day |
//! | `tte`,`tfs` | same | half-lengths of month i / i+1 | day |
//! | `emv` | `emv(14,·)` | end-of-month values (13/14 = leap Jan/Feb) | param units |
//! | `pmt`,`pmv` | same | pseudo-midpoint time / value | day / param units |
//! | `xes` | `xes(12,·)` | monthly value in max/min months, −9999.0 sentinel otherwise | param units |
//! | `ida` | `ida` | Julian day of year used by Fourier evaluation | day |
//! | `mo`,`jd`,`ntd` | same | month, day of month, and days in year | month / day / day |
//! | `mp`,`ni` | same | month midpoint / interval between adjacent midpoints | day |
//! | `lf`,`rf`,`o_mo` | same | linear interpolation weights and adjacent month | fraction / month |

use crate::cinterp::CinterpState;
use crate::libm_pinned::{atanf_pinned, cosf_pinned, sinf_pinned};

/// Days per month, non-leap (`cligen.f:7471` and `7583`).
const DIM: [i32; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

/// Linear monthly interpolation weights — faithful `lintrp`
/// (`cligen.f:7252-7337`). Writes `ci.o_mo`, `ci.lf`, and `ci.rf`.
///
/// # Numerics
/// All REAL*4. `ni(2)` is selected afresh for every call, exactly as
/// the source reassigns its DATA-initialized local for leap/non-leap
/// years (`cligen.f:7310-7315`); no implicit-SAVE state is needed.
pub fn lintrp(mo: i32, jd: i32, ntd: i32, ci: &mut CinterpState) {
    assert!((1..=12).contains(&mo), "lintrp: month must be 1..=12");
    assert!(ntd == 365 || ntd == 366, "lintrp: ntd must be 365 or 366");

    // DATA statements, cligen.f:7303-7306.
    const MP: [f32; 12] = [
        15.5, 14.0, 15.5, 15.0, 15.5, 15.0, 15.5, 15.5, 15.0, 15.5, 15.0, 15.5,
    ];
    let mut ni = [
        31.0f32, 29.5, 30.0, 30.5, 30.5, 30.5, 30.5, 31.0, 30.5, 30.5, 30.5, 30.5,
    ];
    ni[1] = if ntd == 366 { 30.0 } else { 29.5 };

    let m = (mo - 1) as usize;
    // cligen.f:7320-7332.
    if (jd as f32) > MP[m] {
        ci.o_mo = (mo + 1) % 12;
        if ci.o_mo == 0 {
            ci.o_mo = 12;
        }
        ci.rf = ((jd as f32) - MP[m]) / ni[(ci.o_mo - 1) as usize];
    } else {
        ci.o_mo = (mo - 1) % 12;
        if ci.o_mo == 0 {
            ci.o_mo = 12;
        }
        ci.rf = (MP[m] - (jd as f32)) / ni[m];
    }
    ci.lf = 1.0 - ci.rf;
}

/// Fourier-coefficient setup — faithful `fouri1` (`cligen.f:7338-7386`).
/// Called by `sta_parms` for each of the 14 parameters when
/// `interp = 2`; writes `x_bar(indpar)`, `c(1..6,indpar)`,
/// `t(1..6,indpar)`.
///
/// # Numerics
/// All REAL*4. The harmonic argument is the source's literal shape
/// `6.2832*float(i)*float(j)/12.` (left-to-right, `cligen.f:7372`);
/// `2./12.` is the compile-time f32 constant (`cligen.f:7377-7378`).
/// A constant monthly series yields `a = b = 0` and the source's
/// `atan(-b/a)`/`a/cos(t)` produce NaN through IEEE 0/0 — replicated,
/// not guarded (no fixture parameter is constant).
// Faithful source shape (`s=s+x(i)` accumulation, cligen.f:7359-7362;
// the source literal `6.2832` at cligen.f:7372 resembles TAU but is the
// specification's constant); clippy's iterator/assign-op/constant
// rewrites are suppressed so the code reads line-for-line against the
// source.
#[allow(
    clippy::assign_op_pattern,
    clippy::needless_range_loop,
    clippy::approx_constant
)]
pub fn fouri1(x: &[f32; 12], indpar: usize, ci: &mut CinterpState) {
    let p = indpar - 1;
    // cligen.f:7359-7365
    let mut s = 0.0f32;
    for i in 0..12 {
        s = s + x[i];
    }
    ci.x_bar[p] = s / 12.0;
    // cligen.f:7366-7381
    for j in 1..=6usize {
        let mut suma = 0.0f32;
        let mut sumb = 0.0f32;
        for i in 1..=12usize {
            let d = x[i - 1] - ci.x_bar[p];
            let v = 6.2832f32 * (i as f32) * (j as f32) / 12.0;
            suma = suma + (d * cosf_pinned(v));
            sumb = sumb + (d * sinf_pinned(v));
        }
        let a = suma * (2.0f32 / 12.0f32);
        let b = sumb * (2.0f32 / 12.0f32);
        ci.t[j - 1][p] = atanf_pinned(-b / a);
        ci.c[j - 1][p] = a / cosf_pinned(ci.t[j - 1][p]);
    }
}

/// Fourier-series daily evaluation — faithful `fouri2`
/// (`cligen.f:7387-7423`).
///
/// # Numerics
/// All REAL*4. The source's six additions are evaluated in statement
/// order, and every cosine routes through [`cosf_pinned`].
// Faithful source shape: six explicit harmonic additions and the
// source literal `6.2832` (cligen.f:7411-7418). Iterator/assign-op/
// approximate-constant rewrites would obscure that transcription.
#[allow(clippy::assign_op_pattern, clippy::approx_constant)]
pub fn fouri2(indpar: usize, ida: i32, ci: &CinterpState) -> f32 {
    assert!(
        (1..=14).contains(&indpar),
        "fouri2: parameter must be 1..=14"
    );
    let p = indpar - 1;
    let dd = ((ida as f32) + 15.5) / 366.0;
    let mut value = ci.x_bar[p];
    value = value + ci.c[0][p] * cosf_pinned(6.2832 * 1.0 * dd + ci.t[0][p]);
    value = value + ci.c[1][p] * cosf_pinned(6.2832 * 2.0 * dd + ci.t[1][p]);
    value = value + ci.c[2][p] * cosf_pinned(6.2832 * 3.0 * dd + ci.t[2][p]);
    value = value + ci.c[3][p] * cosf_pinned(6.2832 * 4.0 * dd + ci.t[3][p]);
    value = value + ci.c[4][p] * cosf_pinned(6.2832 * 5.0 * dd + ci.t[4][p]);
    value = value + ci.c[5][p] * cosf_pinned(6.2832 * 6.0 * dd + ci.t[5][p]);
    value
}

/// Yoder–Foster monthly-mean-preserving setup — faithful `ryf1`
/// (`cligen.f:7424-7544`). Called by `sta_parms` for each parameter
/// when `interp = 3`; writes `emv(1..14,indpar)`, `pmt(1..13,indpar)`,
/// `pmv(1..13,indpar)`, `xes(1..12,indpar)`.
///
/// # Numerics
/// All REAL*4, pure arithmetic (no transcendentals). Float literals
/// (`0.516667`, `0.483333`, `15.5`, `14.5`, `29.0`, `31.0`) are the
/// source's (`cligen.f:7486-7488, 7518-7538`). The max/min-month
/// classification compares f32 values for exact equality exactly as
/// the source does.
// Faithful source shape: exact `.eq.` comparisons on REAL*4
// (cligen.f:7493, 7512, 7528) — clippy's float_cmp rewrite would
// change the classification semantics.
#[allow(clippy::float_cmp)]
pub fn ryf1(x: &[f32; 12], indpar: usize, ci: &mut CinterpState) {
    let p = indpar - 1;
    // End-of-month values, cligen.f:7476-7488.
    for i in 1..=11usize {
        let tte = (DIM[i - 1] as f32) / 2.0;
        let tfs = (DIM[i] as f32) / 2.0;
        let ratio = tte / (tte + tfs);
        ci.emv[i - 1][p] = x[i - 1] + (x[i] - x[i - 1]) * ratio;
    }
    ci.emv[11][p] = (x[11] + x[0]) * 0.5;
    ci.emv[12][p] = x[0] + (x[1] - x[0]) * 0.516667;
    ci.emv[13][p] = x[1] + (x[2] - x[1]) * 0.483333;

    // Pseudo-midpoint times & values, months 2..12 (cligen.f:7491-7510).
    for i in 2..=12usize {
        let m = i - 1;
        if ci.emv[i - 2][p] == x[m] && ci.emv[i - 1][p] == x[m] {
            // 3 consecutive identical monthly values
            ci.pmt[m][p] = (DIM[m] as f32) / 2.0;
            ci.pmv[m][p] = x[m];
            ci.xes[m][p] = -9999.0;
        } else if (ci.emv[i - 2][p] < x[m] && ci.emv[i - 1][p] > x[m])
            || (ci.emv[i - 2][p] > x[m] && ci.emv[i - 1][p] < x[m])
        {
            // not a max or min
            ci.pmt[m][p] =
                (DIM[m] as f32) * (ci.emv[i - 1][p] - x[m]) / (ci.emv[i - 1][p] - ci.emv[i - 2][p]);
            ci.pmv[m][p] = x[m];
            ci.xes[m][p] = -9999.0;
        } else {
            // max, min, or one EOM value identical to x(i)
            ci.pmv[m][p] = 2.0 * x[m] - (ci.emv[i - 1][p] + ci.emv[i - 2][p]) / 2.0;
            ci.pmt[m][p] = (DIM[m] as f32) / 2.0;
            ci.xes[m][p] = x[m];
        }
    }
    // January, wrapping through December's EOM value (cligen.f:7512-7526).
    if ci.emv[11][p] == x[0] && ci.emv[0][p] == x[0] {
        ci.pmt[0][p] = (DIM[0] as f32) / 2.0;
        ci.pmv[0][p] = x[0];
        ci.xes[0][p] = -9999.0;
    } else if (ci.emv[11][p] < x[0] && ci.emv[0][p] > x[0])
        || (ci.emv[11][p] > x[0] && ci.emv[0][p] < x[0])
    {
        ci.pmt[0][p] = 31.0 * (ci.emv[0][p] - x[0]) / (ci.emv[0][p] - ci.emv[11][p]);
        ci.pmv[0][p] = x[0];
        ci.xes[0][p] = -9999.0;
    } else {
        ci.pmv[0][p] = 2.0 * x[0] - (ci.emv[0][p] + ci.emv[11][p]) / 2.0;
        ci.pmt[0][p] = 15.5;
        ci.xes[0][p] = x[0];
    }
    // February in leap years — slot 13, no xes slot (cligen.f:7528-7539).
    if ci.emv[0][p] == x[1] && ci.emv[1][p] == x[1] {
        ci.pmt[12][p] = 14.5;
        ci.pmv[12][p] = x[1];
    } else if (ci.emv[0][p] < x[1] && ci.emv[1][p] > x[1])
        || (ci.emv[0][p] > x[1] && ci.emv[1][p] < x[1])
    {
        ci.pmt[12][p] = 29.0 * (ci.emv[1][p] - x[1]) / (ci.emv[1][p] - ci.emv[0][p]);
        ci.pmv[12][p] = x[1];
    } else {
        ci.pmv[12][p] = 2.0 * x[1] - (ci.emv[1][p] + ci.emv[0][p]) / 2.0;
        ci.pmt[12][p] = 14.5;
    }
}

/// Yoder–Foster daily evaluation — faithful `ryf2`
/// (`cligen.f:7545-7657`).
///
/// # Numerics
/// All REAL*4. The day is represented at noon by
/// `mjd = float(jd) - 0.5`. In leap-year February, endpoint and
/// pseudo-midpoint slots change to 13/14, while the max/min sentinel
/// deliberately remains `xes(mo,indpar)` (`cligen.f:7610-7615,
/// 7623,7640`).
// Faithful source shape: exact sentinel comparison and explicit
// quarter-month branches (`cligen.f:7621-7653`).
#[allow(clippy::float_cmp)]
pub fn ryf2(mo: i32, jd: i32, ntd: i32, indpar: usize, ci: &CinterpState) -> f32 {
    assert!((1..=12).contains(&mo), "ryf2: month must be 1..=12");
    assert!((1..=14).contains(&indpar), "ryf2: parameter must be 1..=14");
    assert!(ntd == 365 || ntd == 366, "ryf2: ntd must be 365 or 366");
    let m = (mo - 1) as usize;
    let p = indpar - 1;

    // Choose current-month values (cligen.f:7598-7616).
    let (idim, ipmt, ipmv, emv0, emv1) = if mo != 2 || ntd != 366 {
        let emv0 = if mo > 1 {
            ci.emv[m - 1][p]
        } else {
            ci.emv[11][p]
        };
        (
            DIM[m] as f32,
            ci.pmt[m][p],
            ci.pmv[m][p],
            emv0,
            ci.emv[m][p],
        )
    } else {
        (
            29.0,
            ci.pmt[12][p],
            ci.pmv[12][p],
            ci.emv[12][p],
            ci.emv[13][p],
        )
    };

    let mjd = (jd as f32) - 0.5;
    if mjd > ipmt {
        if ci.xes[m][p] == -9999.0 {
            let ratio = (idim - mjd) / (idim - ipmt);
            ratio * ipmv + (1.0 - ratio) * emv1
        } else if mjd > 0.75 * idim {
            let ratio = (idim - mjd) / (0.25 * idim);
            ratio * ci.xes[m][p] + (1.0 - ratio) * emv1
        } else {
            let ratio = (mjd - 0.5 * idim) / (0.25 * idim);
            ratio * ci.xes[m][p] + (1.0 - ratio) * ipmv
        }
    } else if ci.xes[m][p] == -9999.0 {
        let ratio = mjd / ipmt;
        ratio * ipmv + (1.0 - ratio) * emv0
    } else if mjd < 0.25 * idim {
        let ratio = mjd / (0.25 * idim);
        ratio * ci.xes[m][p] + (1.0 - ratio) * emv0
    } else {
        let ratio = (0.5 * idim - mjd) / (0.25 * idim);
        ratio * ci.xes[m][p] + (1.0 - ratio) * ipmv
    }
}
