//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:7338-7386 (fouri1), 7424-7544
//!   (ryf1). Stage C adds the generation-time evaluators fouri2
//!   (7387-7423), ryf2 (7545-7657), lintrp (7252-7337).
//! Precision-Map: REAL*4 throughout (no f64 site exists in these units)
//! Faithful-Acceptance: par-state snapshot identity — the -I2 snapshots
//!   pin fouri1's x_bar/c/t and the -I3 snapshots pin ryf1's
//!   emv/pmt/pmv/xes for all four stations
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

use crate::cinterp::CinterpState;
use crate::libm_pinned::{atanf_pinned, cosf_pinned, sinf_pinned};

/// Days per month, non-leap (`cligen.f:7471` and `7583`).
const DIM: [i32; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

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
