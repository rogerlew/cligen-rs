//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:4453-4700 (ks_tst, conflm,
//!   confls)
//! Precision-Map: REAL*4 except confls' explicit dble() x/df arguments
//! Faithful-Acceptance: ks_tst exercised through the dstg replay
//!   (fixtures/taps/*/dg.tap — a wrong verdict desynchronizes the
//!   iarrct/k7 assertions at the next record); confidence units use
//!   fixtures/taps/stage-c-vectors.tap and ranset replay
//!
//! `chitst` (`cligen.f:4342-4452`) is ratified dead (all call sites
//! commented) and is not ported.
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `n` | `n` | parameter number (1..10; 10 = dstg's channel) | — |
//! | `level1` | `level1` | verdict: 0 = pass, 1 = fail | flag |
//! | `chi_n` | `chi_n` | total observations across the 20 bins | count |
//! | `e_chi` | `e_chi` | expected cumulative count per bin | count |
//! | `ks_cnt` | `ks_cnt(20)` | cumulative observed counts | count |
//! | `ks_dif` | `ks_dif(20)` | abs(observed − expected) per bin | count |
//! | `maxdif` | `maxdif` | K-S statistic (max deviation) | count |
//! | `xbar` | `xbar` | sample mean | — |
//! | `x2sum` | `x2sum` | sum of squared standard-normal deviates | — |
//! | `level`,`level2` | same | confidence of population difference | percent |

use crate::acm::{cdfchi, AcmState};
use crate::crandom3::Crandom3State;

/// Kolmogorov–Smirnov uniformity test — faithful `ks_tst`
/// (`cligen.f:4453-4588`). Returns `level1` (0 = pass, 1 = fail) and
/// writes `chi_n` back to the common state, as the source does.
///
/// # Numerics
/// Only the 20-bin branch (`chi_n >= 100`, `cligen.f:4491-4502`) and
/// the skip branch (`else`, pass) are live; every intermediate binning
/// branch is commented out in the source. Expected counts are
/// `i*0.05*chi_n` evaluated left-to-right in f32; the acceptance
/// threshold is `maxdif/sqrt(float(chi_n)) > 0.8276`.
///
/// # Panics
/// Debug builds panic if `n` or the state's `mox` are outside their
/// 1-based Fortran ranges. The source performs no such check — `ranset`
/// may call with `mox = 0` in Fortran, which under-runs the common
/// block; that behavior is a named Stage C characterization item and is
/// deliberately not replicated here.
pub fn ks_tst(n: usize, cr: &mut Crandom3State) -> i32 {
    debug_assert!((1..=10).contains(&n), "ks_tst: parameter n out of range");
    debug_assert!(
        (1..=12).contains(&cr.mox),
        "ks_tst: mox out of 1-based month range (Fortran would under-run)"
    );
    let mox = cr.mox as usize;
    let mut level1 = 0;
    let mut chi_n: i32 = 0;
    let mut ks_cnt = [0i32; 20];
    let mut ks_dif = [0.0f32; 20];
    for i in 0..20 {
        chi_n += cr.chicnt[n - 1][mox - 1][i];
    }
    cr.chi_n = chi_n;

    if chi_n >= 100 {
        let mut e_chi = 0.05 * chi_n as f32;
        ks_cnt[0] = cr.chicnt[n - 1][mox - 1][0];
        ks_dif[0] = (ks_cnt[0] as f32 - e_chi).abs();
        let mut maxdif = ks_dif[0];
        for i in 2..=20usize {
            e_chi = (i as f32) * 0.05 * chi_n as f32;
            ks_cnt[i - 1] = ks_cnt[i - 2] + cr.chicnt[n - 1][mox - 1][i - 1];
            ks_dif[i - 1] = (ks_cnt[i - 1] as f32 - e_chi).abs();
            if maxdif < ks_dif[i - 1] {
                maxdif = ks_dif[i - 1];
            }
        }
        if maxdif / libm::sqrtf(chi_n as f32) > 0.8276 {
            level1 = 1;
        }
    }
    level1
}

/// Confidence level for a sample mean — faithful `conflm`
/// (`cligen.f:4589-4647`). All arithmetic remains f32.
pub fn conflm(xbar: f32, n: i32, mu: f32, sigma: f32) -> f32 {
    const Z: [f32; 15] = [
        2.807, 2.576, 1.96, 1.645, 1.282, 1.036, 0.8416, 0.6745, 0.5244, 0.3853, 0.2533, 0.1257,
        0.06271, 0.01253, 0.006267,
    ];
    const PROB: [f32; 15] = [
        99.5, 99.0, 95.0, 90.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0, 5.0, 1.0, 0.5,
    ];
    if n <= 0 {
        return 0.0;
    }
    for index in 0..Z.len() {
        let margin = Z[index] * sigma / libm::sqrtf(n as f32);
        let up_lim = xbar + margin;
        let lowlim = xbar - margin;
        if mu > up_lim || mu < lowlim {
            return PROB[index];
        }
    }
    0.0
}

/// Confidence level for a standard-normal sample variance — faithful
/// `confls` (`cligen.f:4650-4700`). The source widens `x2sum`/`n` at
/// lines 4662-4663, calls f64 `cdfchi`, then demotes P to f32 before the
/// final percentage arithmetic.
pub fn confls(x2sum: f32, n: i32, acm: &mut AcmState) -> f32 {
    if n <= 0 {
        return 0.0;
    }
    let result = cdfchi(1, 0.0, 0.0, x2sum as f64, n as f64, acm);
    assert_eq!(result.status, 0, "confls: cdfchi failed");
    let level = result.p as f32;
    (100.0 * 2.0) * (0.5 - level).abs()
}
