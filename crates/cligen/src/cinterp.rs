//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cinterp.inc (common /interp/) +
//!   block-data `interp` initializer cligen.f:1089
//! Precision-Map: REAL*4 values, INTEGER mode/month fields
//! Faithful-Acceptance: par-state snapshot identity
//!   (fixtures/taps/par/, tests/par_state_identity.rs I/F/E/Q/U/Z
//!   records); generation-time `lf`/`rf`/`o_mo` via the lintrp taps
//!   (Stage C)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `interp` | `interp` | interpolation mode: 0 none, 1 linear, 2 Fourier, 3 Yoder–Foster (`-I` flag, cligen.f:812-826) | mode |
//! | `o_mo` | `o_mo` | "other" month of the linear interval (lintrp output) | month |
//! | `lf`,`rf` | same | linear weights, this-month / other-month ends | fraction |
//! | `x_bar` | `x_bar(14)` | per-parameter mean of the 12 monthly values | param units |
//! | `c`,`t` | `c(6,14)`,`t(6,14)` | Fourier magnitude / phase per harmonic and parameter | param units / rad |
//! | `emv` | `emv(14,14)` | end-of-month values (13/14 = leap Jan/Feb ends) | param units |
//! | `pmt` | `pmt(13,14)` | pseudo-midpoint time (13 = leap Feb) | day |
//! | `pmv` | `pmv(13,14)` | pseudo-midpoint value | param units |
//! | `xes` | `xes(12,14)` | max/min-month monthly value, −9999.0 sentinel otherwise | param units |
//!
//! Parameter index (1-based, `cinterp.inc` comment block): 1 mean P,
//! 2 SD P, 3 skew P, 4 P(W|W), 5 P(W|D), 6 mean Tmax, 7 mean Tmin,
//! 8 SD Tmax, 9 SD Tmin, 10 mean Rad, 11 SD Rad, 12 max .5-h P,
//! 13 dew point, 14 time-to-peak.

/// Common `/interp/` (`cinterp.inc:4-7`).
///
/// Array fields mirror the Fortran subscripts with 0-based offsets:
/// `c[j][p]` is `c(j+1, p+1)` (harmonic-major, matching the
/// column-major first subscript), `emv[i][p]` is `emv(i+1, p+1)`, etc.
#[derive(Debug, Clone)]
pub struct CinterpState {
    pub interp: i32,
    pub o_mo: i32,
    pub lf: f32,
    pub rf: f32,
    pub x_bar: [f32; 14],
    pub c: [[f32; 14]; 6],
    pub t: [[f32; 14]; 6],
    pub emv: [[f32; 14]; 14],
    pub pmt: [[f32; 14]; 13],
    pub pmv: [[f32; 14]; 13],
    pub xes: [[f32; 14]; 12],
}

impl Default for CinterpState {
    fn default() -> Self {
        CinterpState {
            // block data: `data interp /0/` (cligen.f:1089); every other
            // member is BSS-zero until lintrp/fouri1/ryf1 write it.
            interp: 0,
            o_mo: 0,
            lf: 0.0,
            rf: 0.0,
            x_bar: [0.0; 14],
            c: [[0.0; 14]; 6],
            t: [[0.0; 14]; 6],
            emv: [[0.0; 14]; 14],
            pmt: [[0.0; 14]; 13],
            pmv: [[0.0; 14]; 13],
            xes: [[0.0; 14]; 12],
        }
    }
}
