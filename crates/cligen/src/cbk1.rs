//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk1.inc (common /bk1/) — the slice
//!   `sta_parms` distributes (`wvl`, `dir`, `rh`, `calm`,
//!   cligen.f:2814, 2881-2925)
//! Precision-Map: REAL*4 throughout
//! Faithful-Acceptance: par-state snapshot identity
//!   (fixtures/taps/par/, tests/par_state_identity.rs V/D/M records)
//!
//! Remaining `/bk1/` members (`wv`, `th`, `pi2`, `ang`, `tdp`) are
//! generation-time scratch owned by the daily package when `windg`
//! ports (incremental-block pattern, SPEC-GENERATOR-CORE).
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `wvl` | `wvl(16,4,12)` | wind stats: direction, parameter (1 %-time, 2 mean speed, 3 std dev, 4 skew), month | % / m/s |
//! | `dir` | `dir(12,17)` | cumulative direction distribution by month (17th = total), scaled ×0.01 | fraction |
//! | `rh` | `rh(12)` | mean monthly dew point | °F |
//! | `calm` | `calm(12)` | % time calm by month | % |

/// Common `/bk1/` (`cbk1.inc:3-4`), the `sta_parms`-owned slice.
///
/// `wvl[i][j][k]` mirrors `wvl(i+1, j+1, k+1)`; `dir[m][d]` mirrors
/// `dir(m+1, d+1)`. No DATA initializer exists for any member: BSS
/// zeros until `sta_parms` distributes.
#[derive(Debug, Clone)]
pub struct Cbk1State {
    pub wvl: [[[f32; 12]; 4]; 16],
    pub dir: [[f32; 17]; 12],
    pub rh: [f32; 12],
    pub calm: [f32; 12],
    /// Generation members from the daily package: generated wind
    /// velocity/direction (windg), `pi2 = 6.283185` (main,
    /// `cligen.f:884`), generated dew point (clgen).
    pub wv: f32,
    pub th: f32,
    pub pi2: f32,
    pub tdp: f32,
}

impl Default for Cbk1State {
    fn default() -> Self {
        Cbk1State {
            wvl: [[[0.0; 12]; 4]; 16],
            dir: [[0.0; 17]; 12],
            rh: [0.0; 12],
            calm: [0.0; 12],
            wv: 0.0,
            th: 0.0,
            pi2: 0.0,
            tdp: 0.0,
        }
    }
}
