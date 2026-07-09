//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:1980-2019 (randn)
//! Precision-Map: pure integer arithmetic; uniform assembled in REAL*4
//! Faithful-Acceptance: tap bit-identity, fixtures/taps/*/rn-sample.tap
//!   (full streams: artifacts/tap-runs, `#[ignore]`-gated tests)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `k` | `k(4)` | 4-integer seed state for one stream | — |
//! | `randn` | `randn` | uniform deviate, open interval (0, 1) | — |

/// One generator stream's seed state — the Fortran `k(4)` array.
///
/// `k[0]` is Fortran `k(1)`. The ten production streams (`k1`..`k10`)
/// live in [`crate::cbk7::Cbk7Seeds`].
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
