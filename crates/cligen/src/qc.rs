//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:4453-4588 (ks_tst)
//! Precision-Map: REAL*4 throughout (statistic and threshold)
//! Faithful-Acceptance: exercised through the dstg replay
//!   (fixtures/taps/*/dg.tap — a wrong verdict desynchronizes the
//!   iarrct/k7 assertions at the next record) + constructed-vector
//!   unit tests
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
