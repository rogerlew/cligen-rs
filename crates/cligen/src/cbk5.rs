//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk5.inc (common /bk5/, live slice)
//! Precision-Map: REAL*4 throughout
//! Faithful-Acceptance: daily tap identity (fixtures/taps/daily/,
//!   tests/daily_identity.rs `r(ida)` assertions)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `r` | `r(366)` | daily precipitation by Julian day | in |
//! | `sml` | `sml` | snowmelt placeholder — written exactly once, `cligen.f:865` (`sml = 0.0`); constant 0 in every reachable run | in |

/// Common `/bk5/` (`cbk5.inc:6`), the live slice. `r` is BSS-zero
/// until generation/observed intake writes it; `sml` is the main
/// program's constant 0.0.
#[derive(Debug, Clone)]
pub struct Cbk5State {
    pub r: [f32; 366],
    pub sml: f32,
}

impl Default for Cbk5State {
    fn default() -> Self {
        Cbk5State {
            r: [0.0; 366],
            sml: 0.0,
        }
    }
}
