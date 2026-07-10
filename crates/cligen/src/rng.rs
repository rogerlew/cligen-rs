//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:1980-2019 (randn), 4002-4340
//!   (ranset)
//! Precision-Map: randn integer/REAL*4; ranset REAL*4 except common-block
//!   g_dsum/g_ssum f64 accumulation and explicit ACM f64 calls
//! Faithful-Acceptance: randn tap bit-identity; ranset sequential replay
//!   against fixtures/taps/*/rs-sample.tap (full streams under
//!   artifacts/tap-runs, `#[ignore]`-gated)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `k` | `k(4)` | 4-integer seed state for one stream | — |
//! | `randn` | `randn` | uniform deviate, open interval (0, 1) | — |
//! | `ell` | `ell` | 1 = preceding day wet, 2 = dry | state |
//! | `last_r` | `last_r(9)` | preceding uniform by parameter | — |
//! | `dimi`,`ldimp` | same | month days / wet days this attempt | day |
//! | `ransum`,`x2sum` | same | normal-deviate sum / squared sum | — |

use crate::acm::AcmState;
use crate::cbk4::Cbk4State;
use crate::cbk7::Cbk7State;
use crate::crandom3::Crandom3State;
use crate::deviates::dstn1;
use crate::qc::{conflm, confls, ks_tst};
use crate::quality::process::ProcessCounters;

/// One generator stream's seed state — the Fortran `k(4)` array.
///
/// `k[0]` is Fortran `k(1)`. The ten production streams (`k1`..`k10`)
/// live in [`crate::cbk7::Cbk7State`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SeedState(pub [i32; 4]);

/// Uniform (0, 1) deviate — faithful `randn` (`cligen.f:1980-2019`).
///
/// # Numerics
/// The seed update is pure integer arithmetic (multiply-by-3 with
/// base-1000/100 carry propagation, `cligen.f:1994-2009`). The uniform
/// is assembled from the four seed integers by f32 multiply-adds with
/// the source's literal constants (`cligen.f:2010-2011`); results
/// outside the open interval (0, 1) are rejected and the update re-run
/// (`cligen.f:2012-2013`).
// Faithful source shape (`k(2)=3*k(2)` etc.); clippy's assign-op
// rewrite is suppressed so the code reads line-for-line against
// cligen.f:1994-2009.
#[allow(clippy::assign_op_pattern)]
pub fn randn(k: &mut SeedState) -> f32 {
    let k = &mut k.0;
    loop {
        k[3] = 3 * k[3] + k[1];
        k[2] = 3 * k[2] + k[0];
        k[1] = 3 * k[1];
        k[0] = 3 * k[0];
        let mut i = k[0] / 1000;
        k[0] -= i * 1000;
        k[1] += i;
        i = k[1] / 100;
        k[1] -= 100 * i;
        k[2] += i;
        i = k[2] / 1000;
        k[2] -= i * 1000;
        k[3] += i;
        i = k[3] / 100;
        k[3] -= 100 * i;
        let v = ((((k[0] as f32) * 0.001 + k[1] as f32) * 0.01 + k[2] as f32) * 0.001
            + k[3] as f32)
            * 0.01;
        if v > 0.0 && v < 1.0 {
            return v;
        }
    }
}

/// Return one source uniform and record that returned deviate for group P.
/// The counter update occurs after the source draw and cannot feed RNG state.
pub(crate) fn randn_observed(
    k: &mut SeedState,
    stream: usize,
    process: &mut ProcessCounters,
) -> f32 {
    let value = randn(k);
    process.randn_draws[stream] += 1;
    value
}

/// `ranset` SAVE state (`cligen.f:4050-4057`).
#[derive(Debug, Clone)]
pub struct RansetState {
    pub ell: i32,
    pub last_r: [f32; 9],
}

impl Default for RansetState {
    fn default() -> Self {
        Self {
            ell: 2,
            last_r: [-1.0; 9],
        }
    }
}

#[derive(Debug, Clone)]
struct MonthAttempt {
    ransum: f32,
    x2sum: f32,
    chisum: [i32; 20],
    ldimp: i32,
}

fn is_normal_parameter(j: usize) -> bool {
    // 1-based exclusions at cligen.f:4193-4194.
    !matches!(j, 0 | 5 | 6 | 8)
}

fn ranset_month_days(mox: i32, ntd: i32) -> usize {
    const DIM: [usize; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    // The source selects 29 days for February for every `ntd` except 365
    // (`cligen.f:4091-4095`). This includes single-storm ordinal values.
    if mox == 2 && ntd != 365 {
        29
    } else {
        DIM[(mox - 1) as usize]
    }
}

fn initialize_ranset_streams(
    seeds: &mut Cbk7State,
    state: &mut RansetState,
    cr: &mut Crandom3State,
    process: &mut ProcessCounters,
) {
    if state.last_r[0] != -1.0 {
        return;
    }
    cr.vv = randn_observed(&mut seeds.k1, 0, process);
    state.last_r[0] = cr.vv;
    seeds.v1 = randn_observed(&mut seeds.k2, 1, process);
    state.last_r[1] = seeds.v1;
    seeds.v3 = randn_observed(&mut seeds.k3, 2, process);
    state.last_r[2] = seeds.v3;
    seeds.v5 = randn_observed(&mut seeds.k4, 3, process);
    state.last_r[3] = seeds.v5;
    seeds.v7 = randn_observed(&mut seeds.k5, 4, process);
    state.last_r[4] = seeds.v7;
    cr.fx = randn_observed(&mut seeds.k6, 5, process);
    state.last_r[5] = cr.fx;
    seeds.v9 = randn_observed(&mut seeds.k8, 7, process);
    state.last_r[6] = seeds.v9;
    seeds.v11 = randn_observed(&mut seeds.k9, 8, process);
    state.last_r[7] = seeds.v11;
    cr.z = randn_observed(&mut seeds.k10, 9, process);
    state.last_r[8] = cr.z;
}

// Arguments are the explicit state/input surfaces read by the source's
// parameter dispatch at cligen.f:4140-4182.
#[allow(clippy::too_many_arguments)]
fn draw_ranset_value(
    j: usize,
    i: usize,
    month: usize,
    iopt: i32,
    seeds: &mut Cbk7State,
    state: &mut RansetState,
    cr: &Crandom3State,
    ldimp: &mut i32,
    process: &mut ProcessCounters,
) -> f32 {
    match j {
        0 => randn_observed(&mut seeds.k1, 0, process),
        1 => randn_observed(&mut seeds.k2, 1, process),
        2 => randn_observed(&mut seeds.k3, 2, process),
        3 => randn_observed(&mut seeds.k4, 3, process),
        4 => {
            if cr.ranary[0][i] <= seeds.prw[month][(state.ell - 1) as usize] {
                state.ell = 1;
                *ldimp += 1;
                randn_observed(&mut seeds.k5, 4, process)
            } else {
                state.ell = 2;
                0.0
            }
        }
        5 => randn_observed(&mut seeds.k6, 5, process),
        6 => randn_observed(&mut seeds.k8, 7, process),
        7 => randn_observed(&mut seeds.k9, 8, process),
        8 if iopt == 6 => 0.0,
        8 => {
            if cr.ranary[4][i] > 0.0 {
                state.ell = 1;
                randn_observed(&mut seeds.k10, 9, process)
            } else {
                state.ell = 2;
                0.0
            }
        }
        _ => unreachable!("ranset has exactly nine parameters"),
    }
}

#[allow(clippy::too_many_arguments)]
fn generate_ranset_parameter(
    j: usize,
    dimi: usize,
    month: usize,
    iopt: i32,
    seeds: &mut Cbk7State,
    state: &mut RansetState,
    cr: &mut Crandom3State,
    process: &mut ProcessCounters,
) -> MonthAttempt {
    let mut attempt = MonthAttempt {
        ransum: 0.0,
        x2sum: 0.0,
        chisum: [0; 20],
        ldimp: 0,
    };
    for i in 0..dimi {
        let value = draw_ranset_value(
            j,
            i,
            month,
            iopt,
            seeds,
            state,
            cr,
            &mut attempt.ldimp,
            process,
        );
        cr.ranary[j][i] = value;
        if value > 0.0 {
            let ichi = ((value * 20.0) as usize + 1).min(20);
            attempt.chisum[ichi - 1] += 1;
        }
        if is_normal_parameter(j) && (j != 4 || state.ell == 1) {
            // The source calls dstn1 twice (cligen.f:4196-4197), once for
            // each accumulation; retain that evaluation shape.
            attempt.ransum += dstn1(state.last_r[j], value);
            let deviate = dstn1(state.last_r[j], value);
            attempt.x2sum += deviate * deviate;
            state.last_r[j] = value;
        }
    }
    attempt
}

fn add_ranset_attempt(j: usize, month: usize, attempt: &MonthAttempt, cr: &mut Crandom3State) {
    for ichi in 0..20 {
        cr.chicnt[j][month][ichi] += attempt.chisum[ichi];
    }
    if is_normal_parameter(j) {
        cr.g_dsum[j][month] += attempt.ransum as f64;
        cr.g_ssum[j][month] += attempt.x2sum as f64;
    }
    if j == 4 {
        cr.g_dimp[month] += attempt.ldimp;
    }
}

fn ranset_quality_levels(
    j: usize,
    month: usize,
    acm: &mut AcmState,
    cr: &mut Crandom3State,
) -> (i32, f32, f32) {
    let level1 = ks_tst(j + 1, cr);
    if !is_normal_parameter(j) {
        return (level1, -1.0, -1.0);
    }
    if level1 != 0 {
        return (level1, -1.0, -1.0);
    }
    let n = if j == 4 {
        cr.g_dimp[month]
    } else {
        cr.g_dimi[month]
    };
    let g_davg = if n > 0 {
        (cr.g_dsum[j][month] / (n as f32) as f64) as f32
    } else {
        0.0
    };
    let level = conflm(g_davg, n, 0.0, 1.0);
    let level2 = confls(cr.g_ssum[j][month] as f32, n, acm);
    (level1, level, level2)
}

fn remove_ranset_attempt(
    j: usize,
    month: usize,
    attempt: &MonthAttempt,
    ellx: i32,
    state: &mut RansetState,
    cr: &mut Crandom3State,
) {
    if is_normal_parameter(j) {
        cr.g_dsum[j][month] -= attempt.ransum as f64;
        cr.g_ssum[j][month] -= attempt.x2sum as f64;
    }
    if j == 4 {
        cr.g_dimp[month] -= attempt.ldimp;
        state.ell = ellx;
    }
    for ichi in 0..20 {
        cr.chicnt[j][month][ichi] -= attempt.chisum[ichi];
    }
}

/// Generate and quality-control one month's nine random-number arrays —
/// faithful `ranset` (`cligen.f:4002-4340`).
///
/// The source deliberately never advances `k7` in this unit. Failed QC
/// attempts restore statistical state and `last_r`, but consumed seed draws
/// remain consumed; that coupling is preserved.
///
/// # Panics
/// Fails closed unless `mox` is 1..=12, `ntd` is positive, and `iopt` is a
/// production option. Single-storm mode passes its ordinal day as `ntd`
/// (captured value 166), while continuous modes pass 365/366. The sole
/// source call assigns `mox=mo` immediately
/// before `ranset` (`cligen.f:1207-1209`); a direct `mox=0` call would first
/// under-run `dim(mox)` at line 4092 and later common storage at 4211/4315.
#[allow(clippy::too_many_arguments)]
pub fn ranset(
    ntd: i32,
    iyear: i32,
    bk4: &Cbk4State,
    seeds: &mut Cbk7State,
    state: &mut RansetState,
    acm: &mut AcmState,
    cr: &mut Crandom3State,
    process: &mut ProcessCounters,
) {
    assert!(ntd > 0, "ranset: ntd must be positive");
    assert!((1..=7).contains(&bk4.iopt), "ranset: invalid iopt");
    assert!(
        (1..=12).contains(&cr.mox),
        "ranset: mox=0/out-of-range would under-run Fortran common storage"
    );
    let month = (cr.mox - 1) as usize;
    let dimi = ranset_month_days(cr.mox, ntd);
    cr.g_dimi[month] += dimi as i32;
    initialize_ranset_streams(seeds, state, cr, process);

    let mut iredo = 0i32;
    let ellx = state.ell;
    for j in 0..9 {
        let lst_rx = state.last_r[j];
        loop {
            let attempt =
                generate_ranset_parameter(j, dimi, month, bk4.iopt, seeds, state, cr, process);
            // Observed-mode time-to-peak skips all statistics, source
            // cligen.f:4204-4205 and 4334-4335.
            if bk4.iopt == 6 && j == 8 {
                process.record_acceptance(j, month, iyear, None);
                break;
            }
            add_ranset_attempt(j, month, &attempt, cr);
            let (level1, level, level2) = ranset_quality_levels(j, month, acm, cr);
            let failed = level1 > 0 || level > cr.thresh[j] || level2 > cr.thres2[j];
            if failed {
                process.record_rejection(j, month);
                iredo += 1;
                if iredo != 10_000 {
                    remove_ranset_attempt(j, month, &attempt, ellx, state, cr);
                    state.last_r[j] = lst_rx;
                } else {
                    println!(
                        "*** ERROR *** Could not produce desired level of quality in parameter {} random deviates (year {iyear}).",
                        j + 1
                    );
                }
            }
            if !failed || iredo >= 10_000 {
                if failed {
                    process.record_cap_give_up(j, month, iyear);
                }
                process.record_acceptance(j, month, iyear, Some((level1, level, level2)));
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::ranset_month_days;

    #[test]
    fn source_february_rule_includes_single_storm_ordinals() {
        assert_eq!(ranset_month_days(2, 365), 28);
        assert_eq!(ranset_month_days(2, 366), 29);
        assert_eq!(ranset_month_days(2, 45), 29);
        assert_eq!(ranset_month_days(6, 166), 30);
    }
}
