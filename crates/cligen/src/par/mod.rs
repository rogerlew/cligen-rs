//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: the unit-10 `.par` read surface — reference/cligen532/
//!   cligen.f:2459 (record 1, sta_dat) and 2793-2815, 2881-2883
//!   (records 2-83, sta_parms), formats cligen.f:2324-2325 and
//!   2753-2756. Stage C adds the intake drivers sta_dat (2240-2483) /
//!   sta_name (2486-2652) / header (2153-2184) on the characterized
//!   live paths.
//! Precision-Map: REAL*4 field values (correctly-rounded decimal→f32)
//! Faithful-Acceptance: par-state snapshot identity across all four
//!   fixture stations (tests/par_state_identity.rs) + byte round-trip
//!   `to_bytes(parse(b)) == b` on all four fixture .par files
//!
//! Format semantics, units, EQUIVALENCE views, serialization, and the
//! round-trip adjudication live in SPEC-PAR (docs/specifications/).
//! `ParFile` is the typed read surface **plus retained raw records**:
//! byte-preserving emission is the round-trip invariant the corpus
//! supports (two zero-rendering conventions exist, section-mixed within
//! one fixture — a canonical value→text formatter cannot reproduce the
//! bytes; see par-roundtrip-adjudication.md).
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `stidd` | `stidd` | 41-char station name (record 1) | — |
//! | `nst`,`nstat` | same | numeric state / station codes (record 1) | — |
//! | `igcode` | `igcode` | 0 = wind data (Penman ET), 1 = none (Priestley–Taylor) | flag |
//! | `ylt`,`yll` | same | station latitude / longitude | °N / °E |
//! | `years` | `years` | years of record | yr |
//! | `itype` | `itype` | single-storm parameter type | 1..4 |
//! | `elev_ft` | `elev` (file) | station elevation as stored in the file | ft |
//! | `tp6` | `tp6` | max 6-h precipitation depth | in |
//! | `rst` | `rst(12,3)` | monthly precip mean/std dev/skew, file values | in/in/— |
//! | `prw` | `prw(12,2)` | P(wet\|wet), P(wet\|dry) by month | probability |
//! | `obmx`..`stdsl` | same | monthly temperature / radiation stats | °F / Langley·day⁻¹ |
//! | `wi_raw` | `wi` (file) | max .5-h precip **intensity** as stored (pre-halving) | in/h |
//! | `rh` | `rh(12)` | monthly dew point | °F |
//! | `timpkd` | `timpkd(1:12)` | cumulative time-to-peak distribution | fraction |
//! | `wvl` | `wvl(16,4,12)` | wind stats by direction/parameter/month | % , m/s |
//! | `calm` | `calm(12)` | % time calm | % |
//! | `site`,`wgt` | same | record-83 wind-station names/weights (blank/0.0 in the corpus) | — |

mod file;
mod intake;
mod sta_parms;

pub use file::{ParError, ParFile};
pub use intake::{header, sta_dat, sta_name, StaDatOut, StaDatSelection};
pub use sta_parms::{sta_parms, StaParmsOut};
