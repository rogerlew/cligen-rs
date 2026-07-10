//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/ccl1.inc (common /cl1/)
//! Precision-Map: REAL*4 throughout
//! Faithful-Acceptance: cold-start day-loop replay
//!   (tests/modes_identity.rs) — `dur` feeds the storm chain, the
//!   grids feed opt_calc/clmout (modes/output packages)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `prcip` | `prcip(12,31)` | daily precipitation grid | in |
//! | `tgmx`,`tgmn` | same | daily max/min temperature grids (Fahrenheit — stored before day_gen's F→C conversion) | °F |
//! | `radg` | `radg(12,31)` | daily solar radiation grid | Langley/day |
//! | `dur` | `dur(12,31)` | storm duration grid | h |

/// Common `/cl1/` (`ccl1.inc:3-4`), indexed `[mo-1][jd-1]`.
/// `wxr_gen` zeroes every cell at each year start
/// (`cligen.f:3768-3775`).
#[derive(Debug, Clone)]
pub struct Ccl1State {
    pub prcip: [[f32; 31]; 12],
    pub tgmx: [[f32; 31]; 12],
    pub tgmn: [[f32; 31]; 12],
    pub radg: [[f32; 31]; 12],
    pub dur: [[f32; 31]; 12],
}

impl Default for Ccl1State {
    fn default() -> Self {
        Ccl1State {
            prcip: [[0.0; 31]; 12],
            tgmx: [[0.0; 31]; 12],
            tgmn: [[0.0; 31]; 12],
            radg: [[0.0; 31]; 12],
            dur: [[0.0; 31]; 12],
        }
    }
}

impl Ccl1State {
    /// The per-year zeroing loop (`cligen.f:3768-3775`).
    pub fn zero_year(&mut self) {
        *self = Ccl1State::default();
    }
}
