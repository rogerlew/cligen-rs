//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk4.inc (common /bk4/, iopt slice) +
//!   reference/cligen532/cligen.f:1083 (block-data initializer)
//! Precision-Map: integer
//! Faithful-Acceptance: ranset sequential replay
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `iopt` | `iopt` | generator option (1..7 in production) | flag |

/// Incremental owning struct for common `/bk4/`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cbk4State {
    pub iopt: i32,
}

impl Default for Cbk4State {
    fn default() -> Self {
        // Block data, cligen.f:1083.
        Self { iopt: -1 }
    }
}
