#![forbid(unsafe_code)]

//! Rust implementation of CLIGEN, the WEPP-family stochastic weather
//! generator — a source-code-authority port of CLIGEN 5.32.x (ADR-0001).
//!
//! The pinned Fortran source at `reference/cligen532/` is the faithful-mode
//! specification. Module boundaries follow the ratified decomposition in
//! `docs/port/fortran-decomposition.md`; every port module carries its
//! attribution header, symbol glossary, and precision map.

pub mod a5e0;
pub mod acm;
pub mod calendar;
pub mod cbk1;
pub mod cbk3;
pub mod cbk4;
pub mod cbk5;
pub mod cbk7;
pub mod cbk9;
pub mod ccl1;
pub mod cinterp;
pub mod cli_diff;
pub mod crandom3;
pub mod daily;
pub mod deviates;
pub mod fast_batch;
pub mod fortran_format;
pub mod libm_pinned;
pub mod modes;
pub mod monthlies;
pub mod observed;
pub mod output;
pub mod par;
pub mod parquet_output;
pub mod profile;
pub mod provenance;
pub mod qc;
pub mod quality;
pub mod rng;
pub mod runspec;
pub mod station;
pub mod stations;
pub mod storm;
pub mod typed_output;

/// The CLIGEN version this port is faithful to.
pub const REFERENCE_VERSION: &str = "5.32.3";
