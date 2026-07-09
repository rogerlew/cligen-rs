//! Constructed-vector tests for `ks_tst` branch coverage
//! (cligen.f:4453-4588). Trajectory-level verification of `ks_tst` runs
//! through the dstg replay in tap_identity.rs.

use cligen::acm::AcmState;
use cligen::crandom3::Crandom3State;
use cligen::qc::{conflm, confls, ks_tst};
use std::path::Path;

fn state_with_bins(n: usize, mox: i32, bins: [i32; 20]) -> Crandom3State {
    let mut cr = Crandom3State {
        mox,
        ..Default::default()
    };
    cr.chicnt[n - 1][(mox - 1) as usize] = bins;
    cr
}

#[test]
fn ks_tst_passes_perfectly_uniform_bins() {
    // 100 observations, exactly 5 per bin: cumulative == expected,
    // maxdif == 0 -> pass.
    let mut cr = state_with_bins(10, 1, [5; 20]);
    assert_eq!(ks_tst(10, &mut cr), 0);
    assert_eq!(cr.chi_n, 100, "chi_n is written back to the common state");
}

#[test]
fn ks_tst_fails_degenerate_distribution() {
    // All 100 observations in bin 1: maxdif = |100 - 5| = 95;
    // 95/sqrt(100) = 9.5 > 0.8276 -> fail.
    let mut bins = [0i32; 20];
    bins[0] = 100;
    let mut cr = state_with_bins(10, 6, bins);
    assert_eq!(ks_tst(10, &mut cr), 1);
}

#[test]
fn ks_tst_skips_below_100_observations() {
    // chi_n < 100: every live binning branch is commented out in the
    // source; the test is skipped and passes (cligen.f:4574-4577).
    let mut bins = [0i32; 20];
    bins[0] = 99; // maximally skewed, but below the threshold
    let mut cr = state_with_bins(3, 12, bins);
    assert_eq!(ks_tst(3, &mut cr), 0);
    assert_eq!(cr.chi_n, 99);
}

#[test]
fn ks_tst_threshold_edge_uses_f32_statistic() {
    // A mildly skewed 100-obs distribution near the 0.8276 threshold:
    // shifting one observation from bin 20 to bin 1 moves every
    // cumulative count by 1, i.e. maxdif by 1 and the statistic by 0.1.
    // 8 shifted: maxdif = 8, 8/10 = 0.8 < 0.8276 -> pass.
    // 9 shifted: maxdif = 9, 9/10 = 0.9 > 0.8276 -> fail.
    let mut bins = [5i32; 20];
    bins[0] += 8;
    bins[19] -= 5;
    bins[18] -= 3;
    let mut cr = state_with_bins(10, 1, bins);
    assert_eq!(ks_tst(10, &mut cr), 0);

    let mut bins = [5i32; 20];
    bins[0] += 9;
    bins[19] -= 5;
    bins[18] -= 4;
    let mut cr = state_with_bins(10, 1, bins);
    assert_eq!(ks_tst(10, &mut cr), 1);
}

#[test]
fn confidence_units_match_fortran_bits() {
    let path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/taps/stage-c-vectors.tap");
    let data = std::fs::read_to_string(path).unwrap();
    let mut acm = AcmState::default();
    let mut count = 0;
    for line in data.lines() {
        let f: Vec<_> = line.split_whitespace().collect();
        if f.first() == Some(&"CONFLM") {
            let n = f[1].parse().unwrap();
            let xbar = f32::from_bits(u32::from_str_radix(f[2], 16).unwrap());
            let expected = u32::from_str_radix(f[3], 16).unwrap();
            assert_eq!(conflm(xbar, n, 0.0, 1.0).to_bits(), expected, "{line}");
            count += 1;
        } else if f.first() == Some(&"CONFLS") {
            let n = f[1].parse().unwrap();
            let x2sum = f32::from_bits(u32::from_str_radix(f[2], 16).unwrap());
            let expected = u32::from_str_radix(f[3], 16).unwrap();
            assert_eq!(confls(x2sum, n, &mut acm).to_bits(), expected, "{line}");
            count += 1;
        }
    }
    assert_eq!(count, 6);
}
