#![forbid(unsafe_code)]

//! Rust implementation of CLIGEN, the WEPP-family stochastic weather
//! generator — a source-code-authority port of CLIGEN 5.32.x (ADR-0001).
//!
//! The pinned Fortran source at `reference/cligen532/` is the faithful-mode
//! specification. No generator code has been ported yet; the module map is
//! planned in `docs/port/fortran-decomposition.md` and lands per the
//! roadmap, fixtures first.

pub mod cli_diff;

/// The CLIGEN version this port is faithful to.
pub const REFERENCE_VERSION: &str = "5.32.3";
