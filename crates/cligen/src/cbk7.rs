//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk7.inc (common /bk7/: seed members,
//!   `prw`, ranset rolling-deviate members, and — from the par package —
//!   the station-parameter arrays `rst`/`obmx`/`obmn`/`obsl`/`cvs`/
//!   `cvtx`/`cvtm`/`stdtx`/`stdtm`/`stdsl`) + block-data seed
//!   initializers cligen.f:1054-1063 + the `-r` burn semantics
//!   cligen.f:702-737
//! Precision-Map: integer seeds; REAL*4 station/rolling values
//! Faithful-Acceptance: burn + warm-draw cross-check against
//!   fixtures/taps/*/dg.tap first records; ranset sequential replay;
//!   station fields via the par-state snapshot identity gate
//!   (fixtures/taps/par/, tests/par_state_identity.rs)
//!
//! The struct was `Cbk7Seeds` while it carried only the RNG package's
//! members; the par package renamed it to `Cbk7State` when the block's
//! station-parameter fields landed (the incremental-block pattern in
//! SPEC-GENERATOR-CORE — one struct per live common block, extended by
//! the package that ports each member's units). The daily package
//! added the generation scratch (`ra`, `tmxg`, `tmng`, `rmx`, `yls`,
//! `ylc`, `pit`, `nsim`, `msim`, `l`); the block is now complete for
//! every live member the decomposition names.
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `k1`..`k10` | `k1(4)`..`k10(4)` | per-parameter seed streams | — |
//! | `rst` | `rst(12,3)` | monthly daily-precip mean / std dev / skew | in / in / — |
//! | `prw` | `prw(12,2)` | wet-day transition probability by month/state | probability |
//! | `obmx`,`obmn` | same | observed monthly mean daily max/min temperature | °F |
//! | `stdtx`,`stdtm` | same | std dev of daily max/min temperature | °F |
//! | `obsl`,`stdsl` | same | mean / std dev of daily solar radiation | Langley/day |
//! | `cvs`,`cvtx`,`cvtm` | same | CV of radiation / max temp / min temp (temps via Rankine offset, cligen.f:2894-2898) | — |
//! | `v1`..`v11` | same odd symbols | preceding uniform for normal pairs | — |

use crate::rng::{randn, SeedState};

/// Common `/bk7/` (`cbk7.inc:10-15`): the ten generator seed streams
/// with block-data defaults (`cligen.f:1054-1063`), the wet-day
/// transition probabilities, the rolling normal-pair uniforms, and the
/// monthly station-parameter arrays distributed by `sta_parms`
/// (`cligen.f:2793-2904`).
///
/// Stream assignments (block-data order): `k1` precip probability,
/// `k2`/`k3` max/min temperature, `k4` radiation, `k5` precip amount,
/// `k6` wind direction, `k7` dstg/intensity, `k8` wind velocity,
/// `k9` dew point, `k10` time-to-peak.
#[derive(Debug, Clone)]
pub struct Cbk7State {
    /// `rst(month,stat)`, stored `[month-1][stat-1]`; stat 1 = mean,
    /// 2 = std dev, 3 = skew of daily precipitation (inches).
    pub rst: [[f32; 3]; 12],
    /// `prw(month,state)`, stored `[month-1][state-1]`.
    pub prw: [[f32; 2]; 12],
    pub obmx: [f32; 12],
    pub obmn: [f32; 12],
    pub obsl: [f32; 12],
    pub cvs: [f32; 12],
    pub cvtx: [f32; 12],
    pub cvtm: [f32; 12],
    pub stdtx: [f32; 12],
    pub stdtm: [f32; 12],
    pub stdsl: [f32; 12],
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
    /// Generation scratch distributed by the daily package: generated
    /// radiation / max temp / min temp, max possible radiation, the
    /// main program's latitude sin/cos and `pit = 58.13`
    /// (`cligen.f:882-887`), the observed-mode per-day flags, and the
    /// wet/dry Markov selector.
    pub ra: f32,
    pub tmxg: f32,
    pub tmng: f32,
    pub rmx: f32,
    pub yls: f32,
    pub ylc: f32,
    pub pit: f32,
    pub nsim: i32,
    pub msim: i32,
    pub l: i32,
}

impl Default for Cbk7State {
    fn default() -> Self {
        Cbk7State {
            // No DATA initializer: station loading / main warm-up writes
            // these BSS-zero values before production use.
            rst: [[0.0; 3]; 12],
            prw: [[0.0; 2]; 12],
            obmx: [0.0; 12],
            obmn: [0.0; 12],
            obsl: [0.0; 12],
            cvs: [0.0; 12],
            cvtx: [0.0; 12],
            cvtm: [0.0; 12],
            stdtx: [0.0; 12],
            stdtm: [0.0; 12],
            stdsl: [0.0; 12],
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
            ra: 0.0,
            tmxg: 0.0,
            tmng: 0.0,
            rmx: 0.0,
            yls: 0.0,
            ylc: 0.0,
            pit: 0.0,
            nsim: 0,
            msim: 0,
            l: 0,
        }
    }
}

impl Cbk7State {
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

    /// The `rst1`/`rst2`/`rst3` EQUIVALENCE views (`cligen.f:2783-2785`):
    /// column `stat` (1-based, mirroring `rst(1,stat)`) of `rst(12,3)`
    /// as the 12-month vector `sta_parms` hands to `fouri1`/`ryf1`.
    pub fn rst_col(&self, stat: usize) -> [f32; 12] {
        assert!((1..=3).contains(&stat), "rst column index 1..=3");
        std::array::from_fn(|m| self.rst[m][stat - 1])
    }

    /// The `prw1`/`prw2` EQUIVALENCE views (`cligen.f:2786-2787`):
    /// column `state` (1-based, mirroring `prw(1,state)`) of `prw(12,2)`.
    pub fn prw_col(&self, state: usize) -> [f32; 12] {
        assert!((1..=2).contains(&state), "prw column index 1..=2");
        std::array::from_fn(|m| self.prw[m][state - 1])
    }
}
