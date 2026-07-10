//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk9.inc (common /bk9/) — the slice
//!   `sta_parms` distributes (`wi`, cligen.f:2802-2812)
//! Precision-Map: REAL*4 throughout
//! Faithful-Acceptance: par-state snapshot identity
//!   (fixtures/taps/par/, tests/par_state_identity.rs M records)
//!
//! Remaining `/bk9/` members (`xi`, `ab`, `ab1`, `rn1`, `r1`) are
//! storm/main-program state owned by later packages
//! (incremental-block pattern, SPEC-GENERATOR-CORE).
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `wi` | `wi(12)` | monthly average max .5-h precip — file carries intensity (in/h), halved to depth at load (cligen.f:2804-2812, B. Yu 7/7/1999) | in |

/// Common `/bk9/` (`cbk9.inc:4`), the `sta_parms`-owned slice.
/// No DATA initializer: BSS zeros until `sta_parms` distributes.
#[derive(Debug, Clone, Default)]
pub struct Cbk9State {
    pub wi: [f32; 12],
}
