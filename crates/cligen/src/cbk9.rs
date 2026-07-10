//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk9.inc (common /bk9/) — the slice
//!   `sta_parms` distributes (`wi`, cligen.f:2802-2812) plus daily
//!   intensity state (`ab`, `ab1`, `rn1`, `r1`, cligen.f:879-891,
//!   3817-3895)
//! Precision-Map: REAL*4 throughout
//! Faithful-Acceptance: par-state snapshot identity
//!   (fixtures/taps/par/, tests/par_state_identity.rs M records) and
//!   daily alphb/r5monb tap identity (fixtures/taps/daily/,
//!   tests/daily_identity.rs)
//!
//! Remaining `/bk9/` member `xi` arrives with the storm package
//! (incremental-block pattern, SPEC-GENERATOR-CORE).
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `wi` | `wi(12)` | monthly average max .5-h precip — file carries intensity (in/h), halved to depth at load (cligen.f:2804-2812, B. Yu 7/7/1999) | in |
//! | `ab` | `ab` | lower bound for the alpha ratio (`0.02083`) | — |
//! | `ab1` | `ab1` | complement `1.0 - ab` | — |
//! | `rn1` | `rn1` | main-program warm draw from `k7`; retained although the live `dstg` call no longer consumes it | — |
//! | `r1` | `r1` | generated maximum-30-minute / total-rain ratio | — |

/// Incremental owning struct for common `/bk9/` (`cbk9.inc:4`).
/// `wi` is BSS-zero until `sta_parms` distributes; `ab`/`ab1` mirror
/// the once-per-run main-program assignments at `cligen.f:879-880`.
#[derive(Debug, Clone)]
pub struct Cbk9State {
    pub wi: [f32; 12],
    pub ab: f32,
    pub ab1: f32,
    pub rn1: f32,
    pub r1: f32,
}

impl Default for Cbk9State {
    fn default() -> Self {
        let ab = 0.02083f32;
        Self {
            wi: [0.0; 12],
            ab,
            ab1: 1.0 - ab,
            // `rn1 = randn(k7)` is an orchestrator warm draw
            // (cligen.f:891); the modes package owns that seed-advancing
            // setup. Both fields otherwise begin in Fortran BSS storage.
            rn1: 0.0,
            r1: 0.0,
        }
    }
}
