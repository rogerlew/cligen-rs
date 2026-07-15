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
use crate::profile::QcFilter;
use crate::qc::{conflm, confls, ks_tst, ks_verdict};
use crate::quality::process::{DiagnosticQc, ProcessCounters};

/// One generator stream's seed state — the Fortran `k(4)` array.
///
/// `k[0]` is Fortran `k(1)`. The ten production streams (`k1`..`k10`)
/// live in [`crate::cbk7::Cbk7State`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SeedState(pub [i32; 4]);

const SEED_MODULUS: u64 = 10_000_000_000;

/// Advance one source RNG state by an exact number of raw recurrence updates.
///
/// The mixed-radix Fortran state is one integer modulo 10^10. The source's
/// cross-word additions make each complete raw update multiplication by
/// 100003, not merely by the visible per-word factor three. This research
/// support seam is used only to allocate A5e0's declared, nonoverlapping
/// faithful substreams; it does not alter the source `randn` path.
pub(crate) fn advance_seed_raw(seed: &mut SeedState, updates: u64) {
    if updates == 0 {
        return;
    }
    let encoded = encode_seed(*seed);
    let multiplier = modular_power(100_003, updates, SEED_MODULUS);
    *seed = decode_seed(modular_product(encoded, multiplier, SEED_MODULUS));
}

/// Period of a canonical state under the raw source recurrence.
pub(crate) fn seed_period(seed: SeedState) -> u64 {
    let reduced_modulus = SEED_MODULUS / greatest_common_divisor(encode_seed(seed), SEED_MODULUS);
    let mut value = reduced_modulus;
    let mut power_two = 0u32;
    let mut power_five = 0u32;
    while value.is_multiple_of(2) {
        value /= 2;
        power_two += 1;
    }
    while value.is_multiple_of(5) {
        value /= 5;
        power_five += 1;
    }
    debug_assert_eq!(value, 1);
    least_common_multiple(
        order_mod_power_two(power_two),
        order_mod_power_five(power_five),
    )
}

fn encode_seed(seed: SeedState) -> u64 {
    let [first, second, third, fourth] = seed.0;
    debug_assert!((0..1000).contains(&first));
    // k10's source DATA state has second = 103. The first recurrence
    // normalizes it through the base-100 carry; its encoded residue is valid.
    debug_assert!(second >= 0);
    debug_assert!((0..1000).contains(&third));
    debug_assert!((0..100).contains(&fourth));
    (first as u64 + 1_000 * second as u64 + 100_000 * third as u64 + 100_000_000 * fourth as u64)
        % SEED_MODULUS
}

fn decode_seed(mut encoded: u64) -> SeedState {
    let first = (encoded % 1_000) as i32;
    encoded /= 1_000;
    let second = (encoded % 100) as i32;
    encoded /= 100;
    let third = (encoded % 1_000) as i32;
    encoded /= 1_000;
    let fourth = (encoded % 100) as i32;
    SeedState([first, second, third, fourth])
}

fn modular_power(mut base: u64, mut exponent: u64, modulus: u64) -> u64 {
    let mut result = 1u64;
    while exponent != 0 {
        if exponent & 1 == 1 {
            result = modular_product(result, base, modulus);
        }
        base = modular_product(base, base, modulus);
        exponent >>= 1;
    }
    result
}

fn modular_product(left: u64, right: u64, modulus: u64) -> u64 {
    ((left as u128 * right as u128) % modulus as u128) as u64
}

fn greatest_common_divisor(mut left: u64, mut right: u64) -> u64 {
    while right != 0 {
        (left, right) = (right, left % right);
    }
    left
}

fn least_common_multiple(left: u64, right: u64) -> u64 {
    left / greatest_common_divisor(left, right) * right
}

fn order_mod_power_two(power: u32) -> u64 {
    match power {
        0 | 1 => 1,
        2 | 3 => 2,
        _ => 1u64 << (power - 2),
    }
}

fn order_mod_power_five(power: u32) -> u64 {
    if power == 0 {
        1
    } else {
        4 * 5u64.pow(power - 1)
    }
}

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
    loop {
        let v = raw_step_value(k);
        if v > 0.0 && v < 1.0 {
            return v;
        }
    }
}

#[allow(clippy::assign_op_pattern)]
fn raw_step_value(state: &mut SeedState) -> f32 {
    let k = &mut state.0;
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
    ((((k[0] as f32) * 0.001 + k[1] as f32) * 0.01 + k[2] as f32) * 0.001 + k[3] as f32) * 0.01
}

/// Exact raw recurrence updates needed to return `draws` source uniforms.
///
/// This includes updates rejected by the source's rounded open-interval check
/// and is used only in A5e0 substream evidence.
pub(crate) fn raw_updates_for_returned(mut seed: SeedState, draws: u64) -> u64 {
    let mut returned = 0;
    let mut updates = 0;
    while returned < draws {
        let value = raw_step_value(&mut seed);
        updates += 1;
        if value > 0.0 && value < 1.0 {
            returned += 1;
        }
    }
    updates
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
    qc: QcFilter,
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
    initialize_ranset_streams(seeds, state, cr, process);

    if qc == QcFilter::Off {
        // SPEC-GENERATION-PROFILES §qc_filter `off`: every produced
        // batch is accepted; RANDN, the streams, the column-5/9 masks,
        // and the `ell` chain stay source-shaped — only the
        // accept/retry loop and its QC accumulation (`g_dimi`,
        // `add_ranset_attempt`) are skipped. The faithful verdicts are
        // evaluated diagnostically over a parallel accumulator owned
        // by group P; generation state is never touched by them.
        process.diagnostic.g_dimi[month] += dimi as i32;
        for j in 0..9 {
            let attempt =
                generate_ranset_parameter(j, dimi, month, bk4.iopt, seeds, state, cr, process);
            if bk4.iopt == 6 && j == 8 {
                continue; // the observed-mode statistics bypass
            }
            let reject = counterfactual_would_reject(
                j,
                month,
                &attempt,
                cr.thresh[j],
                cr.thres2[j],
                process,
            );
            process.record_counterfactual(j, month, reject);
        }
        return;
    }

    cr.g_dimi[month] += dimi as i32;
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

/// The `qc_filter: off` counterfactual: accumulate the attempt into
/// the diagnostic copy of the QC state and evaluate the faithful
/// verdict expressions over it — the same math as
/// [`add_ranset_attempt`] + [`ranset_quality_levels`], operating on
/// [`DiagnosticQc`] storage only.
fn counterfactual_would_reject(
    j: usize,
    month: usize,
    attempt: &MonthAttempt,
    thresh: f32,
    thres2: f32,
    process: &mut ProcessCounters,
) -> bool {
    let diag: &mut DiagnosticQc = &mut process.diagnostic;
    for ichi in 0..20 {
        diag.chicnt[j][month][ichi] += attempt.chisum[ichi];
    }
    if is_normal_parameter(j) {
        diag.g_dsum[j][month] += attempt.ransum as f64;
        diag.g_ssum[j][month] += attempt.x2sum as f64;
    }
    if j == 4 {
        diag.g_dimp[month] += attempt.ldimp;
    }
    let level1 = ks_verdict(&diag.chicnt[j][month]);
    if !is_normal_parameter(j) || level1 != 0 {
        return level1 > 0;
    }
    let n = if j == 4 {
        diag.g_dimp[month]
    } else {
        diag.g_dimi[month]
    };
    let g_davg = if n > 0 {
        (diag.g_dsum[j][month] / (n as f32) as f64) as f32
    } else {
        0.0
    };
    let level = conflm(g_davg, n, 0.0, 1.0);
    let level2 = confls(diag.g_ssum[j][month] as f32, n, &mut diag.acm);
    level > thresh || level2 > thres2
}

#[cfg(test)]
mod tests {
    use super::{
        advance_seed_raw, randn, ranset_month_days, raw_step_value, raw_updates_for_returned,
        seed_period, SeedState,
    };
    use crate::cbk7::Cbk7State;

    #[test]
    fn source_february_rule_includes_single_storm_ordinals() {
        assert_eq!(ranset_month_days(2, 365), 28);
        assert_eq!(ranset_month_days(2, 366), 29);
        assert_eq!(ranset_month_days(2, 45), 29);
        assert_eq!(ranset_month_days(6, 166), 30);
    }

    #[test]
    fn exact_skip_matches_raw_recurrence_and_known_vector() {
        let initial = Cbk7State::default().k1;
        let mut iterated = initial;
        for _ in 0..17 {
            let _ = raw_step_value(&mut iterated);
        }
        let mut skipped = initial;
        advance_seed_raw(&mut skipped, 17);
        assert_eq!(skipped, iterated);
        assert_eq!(skipped, SeedState([467, 35, 440, 48]));
    }

    #[test]
    fn zero_skip_preserves_source_k10_representation() {
        let mut seed = Cbk7State::default().k10;
        let original = seed;
        advance_seed_raw(&mut seed, 0);
        assert_eq!(seed, original);
        assert_eq!(seed, SeedState([22, 103, 82, 4]));
    }

    #[test]
    fn canonical_periods_match_the_partition_proof() {
        let state = Cbk7State::default();
        let periods = [
            state.k1, state.k2, state.k3, state.k4, state.k5, state.k6, state.k7, state.k8,
            state.k9, state.k10,
        ]
        .map(seed_period);
        assert_eq!(
            periods,
            [
                500_000_000,
                100_000_000,
                500_000_000,
                100_000_000,
                100_000_000,
                500_000_000,
                500_000_000,
                100_000_000,
                12_500_000,
                250_000_000,
            ]
        );
        assert!(periods.into_iter().all(|period| period >= 24 * 500_000));
    }

    #[test]
    fn raw_update_evidence_counts_source_endpoint_rejections() {
        let initial = Cbk7State::default().k1;
        let updates = raw_updates_for_returned(initial, 10_000);
        let mut replay = initial;
        for _ in 0..10_000 {
            let _ = randn(&mut replay);
        }
        let mut skipped = initial;
        advance_seed_raw(&mut skipped, updates);
        assert_eq!(skipped, replay);
    }
}
