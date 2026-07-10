//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk3.inc (common /bk3/, live slice)
//! Precision-Map: INTEGER throughout
//! Faithful-Acceptance: daily tap identity (fixtures/taps/daily/,
//!   tests/daily_identity.rs — `ida` drives the solar geometry pinned
//!   by every `rmx` assertion)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `j` | `j` | windg's direction-search loop index — a loop counter in COMMON (source's own comment: "WHY is it in a COMMON BLOCK?!?") | — |
//! | `ida` | `ida` | Julian day of year, subscript into `r` | day |

/// Common `/bk3/` (`cbk3.inc:5`), the live slice. No DATA initializer:
/// BSS zeros until the day loop writes.
#[derive(Debug, Clone, Default)]
pub struct Cbk3State {
    pub j: i32,
    pub ida: i32,
}
