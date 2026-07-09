//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk7.inc (common /bk7/, seed members
//!   only) + block-data seed initializers cligen.f:1054-1063 + the `-r`
//!   burn semantics cligen.f:702-737
//! Precision-Map: integer
//! Faithful-Acceptance: burn + warm-draw cross-check against
//!   fixtures/taps/*/dg.tap first records
//!
//! The `/bk7/` block also carries station-parameter arrays (`rst`,
//! `prw`, `obmx`, …) owned by the `par` module when it ports (ROADMAP
//! item 4). Per the coding standard §5 the block keeps a single home;
//! this struct is that home, extended field-by-field as later packages
//! port their units — a deliberate incremental reading of the standard,
//! recorded in the Stage S handoff.
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `k1`..`k10` | `k1(4)`..`k10(4)` | per-parameter seed streams | — |

use crate::rng::{randn, SeedState};

/// The ten generator seed streams of common `/bk7/`
/// (`cbk7.inc:10-12`), with block-data defaults (`cligen.f:1054-1063`).
///
/// Stream assignments (block-data order): `k1` precip probability,
/// `k2`/`k3` max/min temperature, `k4` radiation, `k5` precip amount,
/// `k6` wind direction, `k7` dstg/intensity, `k8` wind velocity,
/// `k9` dew point, `k10` time-to-peak.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Cbk7Seeds {
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
}

impl Default for Cbk7Seeds {
    fn default() -> Self {
        Cbk7Seeds {
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
