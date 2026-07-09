//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk7.inc (common /bk7/, seed members,
//!   `prw`, and ranset rolling-deviate members) + block-data seed
//!   initializers cligen.f:1054-1063 + the `-r` burn semantics
//!   cligen.f:702-737
//! Precision-Map: integer seeds; REAL*4 station/rolling values
//! Faithful-Acceptance: burn + warm-draw cross-check against
//!   fixtures/taps/*/dg.tap first records; ranset sequential replay
//!
//! The `/bk7/` block also carries station-parameter arrays (`rst`,
//! `obmx`, …) owned by the `par` module when it ports (ROADMAP
//! item 4). Per the coding standard §5 the block keeps a single home;
//! this struct is that home, extended field-by-field as later packages
//! port their units — a deliberate incremental reading of the standard,
//! recorded in the Stage S handoff.
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `k1`..`k10` | `k1(4)`..`k10(4)` | per-parameter seed streams | — |
//! | `prw` | `prw(12,2)` | wet-day transition probability by month/state | probability |
//! | `v1`..`v11` | same odd symbols | preceding uniform for normal pairs | — |

use crate::rng::{randn, SeedState};

/// The ten generator seed streams of common `/bk7/`
/// (`cbk7.inc:10-12`), with block-data defaults (`cligen.f:1054-1063`).
///
/// Stream assignments (block-data order): `k1` precip probability,
/// `k2`/`k3` max/min temperature, `k4` radiation, `k5` precip amount,
/// `k6` wind direction, `k7` dstg/intensity, `k8` wind velocity,
/// `k9` dew point, `k10` time-to-peak.
#[derive(Debug, Clone)]
pub struct Cbk7Seeds {
    /// `prw(month,state)`, stored `[month-1][state-1]`.
    pub prw: [[f32; 2]; 12],
    pub k1: SeedState,
    pub k2: SeedState,
    pub k3: SeedState,
    pub k4: SeedState,
    pub k5: SeedState,
    pub k6: SeedState,
    pub k7: SeedState,
    pub k8: SeedState,
    pub k9: SeedState,
    pub k10: SeedState,
    pub v1: f32,
    pub v3: f32,
    pub v5: f32,
    pub v7: f32,
    pub v9: f32,
    pub v11: f32,
}

impl Default for Cbk7Seeds {
    fn default() -> Self {
        Cbk7Seeds {
            // No DATA initializer: station loading / main warm-up writes
            // these BSS-zero values before production use.
            prw: [[0.0; 2]; 12],
            k1: SeedState([9, 98, 915, 92]),
            k2: SeedState([135, 28, 203, 85]),
            k3: SeedState([43, 54, 619, 33]),
            k4: SeedState([645, 9, 948, 65]),
            k5: SeedState([885, 41, 696, 62]),
            k6: SeedState([51, 78, 648, 0]),
            k7: SeedState([227, 57, 929, 37]),
            k8: SeedState([205, 90, 215, 31]),
            k9: SeedState([320, 73, 631, 49]),
            k10: SeedState([22, 103, 82, 4]),
            v1: 0.0,
            v3: 0.0,
            v5: 0.0,
            v7: 0.0,
            v9: 0.0,
            v11: 0.0,
        }
    }
}

impl Cbk7Seeds {
    /// The `-rN` option (`cligen.f:723-737`): discard `n` draws from
    /// each of `k1`..`k9`. `k10` is deliberately not advanced by the
    /// source's burn loop.
    pub fn burn(&mut self, n: u32) {
        for _ in 0..n {
            let _ = randn(&mut self.k1);
            let _ = randn(&mut self.k2);
            let _ = randn(&mut self.k3);
            let _ = randn(&mut self.k4);
            let _ = randn(&mut self.k5);
            let _ = randn(&mut self.k6);
            let _ = randn(&mut self.k7);
            let _ = randn(&mut self.k8);
            let _ = randn(&mut self.k9);
        }
    }
}
