//! Group A targets derived from the parsed `.par` (SPEC-QUALITY-REPORT
//! group A; adjudication in
//! `docs/work-packages/20260710-q1-quality-report/artifacts/estimator-adjudication.md`).
//!
//! The target is what the generator was **asked** to reproduce, on
//! the `.cli` consumer surface's units (mm, °C, Langleys/day, m/s):
//!
//! - values the source distributes verbatim (`sta_parms`,
//!   cligen.f:2793-2815) are the as-parsed `.par` values, unit-mapped;
//! - values the source corrects before use carry the correction:
//!   precipitation skew is clamped to ±4.5 in place
//!   (cligen.f:1237-1238) and a zero skew is replaced by 0.01
//!   (cligen.f:1244-1246);
//! - derived targets use the source's own expectation formulas: the
//!   wet-day fraction is the stationary Markov probability
//!   P(W|D) / (1 − P(W|W) + P(W|D)) (the header `smy` formula,
//!   cligen.f:3741-3745), and the wind-speed mean is the
//!   direction-probability-weighted mean with calm days as zero
//!   (`windg`, cligen.f:2020-2119).
//!
//! Parsed f32 `.par` fields widen to f64 before any arithmetic. With
//! interpolation active (`-I1..3`) the generator's effective daily
//! parameters differ from these monthly values; the report keeps the
//! monthly `.par`-derived targets and group A then includes the
//! interpolation-method bias.

use crate::par::ParFile;
use crate::station::FixedMonthly5323;

const IN_TO_MM: f64 = 25.4;
const F_TO_C_SCALE: f64 = 5.0 / 9.0;

/// Per-month group A targets, f64, `.cli`-surface units.
#[derive(Debug, Clone)]
pub struct ParTargets {
    pub precip_wet_mean_mm: [Option<f64>; 12],
    pub precip_wet_sd_mm: [Option<f64>; 12],
    pub precip_wet_skew: [Option<f64>; 12],
    pub wet_day_fraction: [Option<f64>; 12],
    pub p_ww: [Option<f64>; 12],
    pub p_wd: [Option<f64>; 12],
    pub tmax_mean_c: [Option<f64>; 12],
    pub tmax_sd_c: [Option<f64>; 12],
    pub tmin_mean_c: [Option<f64>; 12],
    pub tmin_sd_c: [Option<f64>; 12],
    pub radiation_mean_ly: [Option<f64>; 12],
    pub dewpoint_mean_c: [Option<f64>; 12],
    pub wind_speed_mean_ms: [Option<f64>; 12],
}

impl ParTargets {
    /// Derive every group A target from a parsed `.par`.
    #[must_use]
    pub fn from_par(par: &ParFile) -> Self {
        Self::from_station(par.fixed_monthly())
    }

    /// Derive every group A target from syntax-independent fixed-monthly
    /// station state (SPEC-STATION-DOCUMENT).
    #[must_use]
    pub fn from_station(station: &FixedMonthly5323) -> Self {
        let mut targets = ParTargets {
            precip_wet_mean_mm: [None; 12],
            precip_wet_sd_mm: [None; 12],
            precip_wet_skew: [None; 12],
            wet_day_fraction: [None; 12],
            p_ww: [None; 12],
            p_wd: [None; 12],
            tmax_mean_c: [None; 12],
            tmax_sd_c: [None; 12],
            tmin_mean_c: [None; 12],
            tmin_sd_c: [None; 12],
            radiation_mean_ly: [None; 12],
            dewpoint_mean_c: [None; 12],
            wind_speed_mean_ms: [None; 12],
        };
        for m in 0..12 {
            targets.precip_wet_mean_mm[m] = Some(f64::from(station.rst[m][0]) * IN_TO_MM);
            targets.precip_wet_sd_mm[m] = Some(f64::from(station.rst[m][1]) * IN_TO_MM);
            targets.precip_wet_skew[m] = Some(effective_skew(f64::from(station.rst[m][2])));
            let p_ww = f64::from(station.prw[m][0]);
            let p_wd = f64::from(station.prw[m][1]);
            targets.p_ww[m] = Some(p_ww);
            targets.p_wd[m] = Some(p_wd);
            targets.wet_day_fraction[m] = stationary_wet_fraction(p_ww, p_wd);
            targets.tmax_mean_c[m] = Some(f_to_c(f64::from(station.obmx[m])));
            targets.tmax_sd_c[m] = Some(f64::from(station.stdtx[m]) * F_TO_C_SCALE);
            targets.tmin_mean_c[m] = Some(f_to_c(f64::from(station.obmn[m])));
            targets.tmin_sd_c[m] = Some(f64::from(station.stdtm[m]) * F_TO_C_SCALE);
            targets.radiation_mean_ly[m] = Some(f64::from(station.obsl[m]));
            targets.dewpoint_mean_c[m] = Some(f_to_c(f64::from(station.rh[m])));
            targets.wind_speed_mean_ms[m] = Some(wind_mean(station, m));
        }
        targets
    }
}

/// The skew the generator is asked to reproduce: clamped to ±4.5
/// (cligen.f:1237-1238), then a zero replaced by 0.01
/// (cligen.f:1244-1246).
fn effective_skew(skew: f64) -> f64 {
    let clamped = skew.clamp(-4.5, 4.5);
    if clamped == 0.0 {
        0.01
    } else {
        clamped
    }
}

/// Stationary two-state Markov wet probability
/// P(W|D) / (1 − P(W|W) + P(W|D)); `None` on a zero denominator.
fn stationary_wet_fraction(p_ww: f64, p_wd: f64) -> Option<f64> {
    let denominator = 1.0 - p_ww + p_wd;
    if denominator == 0.0 {
        return None;
    }
    Some(p_wd / denominator)
}

/// Direction-probability-weighted monthly mean wind speed, m/s.
/// `wvl[direction][0]` is percent-of-time, `wvl[direction][1]` the
/// direction's mean speed; calm days (the percentage shortfall from
/// 100) contribute zero, exactly as `windg`'s `ndflag = 0` path.
fn wind_mean(station: &FixedMonthly5323, month: usize) -> f64 {
    let mut mean = 0.0f64;
    for direction in 0..16 {
        let probability = f64::from(station.wvl[direction][0][month]) * 0.01;
        mean += probability * f64::from(station.wvl[direction][1][month]);
    }
    mean
}

/// Fahrenheit → Celsius on a widened f64 value.
fn f_to_c(fahrenheit: f64) -> f64 {
    (fahrenheit - 32.0) * F_TO_C_SCALE
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn effective_skew_applies_source_corrections() {
        assert_eq!(effective_skew(4.82), 4.5);
        assert_eq!(effective_skew(-5.0), -4.5);
        assert_eq!(effective_skew(0.0), 0.01);
        assert_eq!(effective_skew(2.01), 2.01);
    }

    #[test]
    fn stationary_wet_fraction_matches_source_formula() {
        // New Meadows January: P(W|W) = .51, P(W|D) = .18.
        let pi = stationary_wet_fraction(0.51, 0.18).unwrap();
        assert!((pi - 0.18 / 0.67).abs() < 1e-15);
        assert_eq!(stationary_wet_fraction(1.0, 0.0), None);
    }
}
