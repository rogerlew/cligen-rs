//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cbk4.inc (common /bk4/: `iopt` slice
//!   from the RNG package; `nc`/`nt`/`mo` from the daily package;
//!   `dtp`/`dmxi` from the storm package) + block-data initializers
//!   cligen.f:1064-1066 (`nc`, `dtp`, `dmxi`), 1083 (`iopt`)
//! Precision-Map: integer control fields; REAL*4 `dtp`/`dmxi`
//! Faithful-Acceptance: ranset sequential replay; daily/storm tap
//!   identity (`mo` threads every per-day record; `dtp` is covered by
//!   the constructed iopt-7 override vector)
//!
//! Remaining `/bk4/` members (`iyr`, `px`) arrive with the modes package
//! (incremental-block pattern, SPEC-GENERATOR-CORE).
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `nc` | `nc(13)` | cumulative days preceding each month, non-leap (block data) | day |
//! | `nt` | `nt` | 1 if the beginning year is not a leap year — set only for options 4/7 | flag |
//! | `mo` | `mo` | current month (`day_gen`'s `jlt` decomposition, or the typed `sing_stm` intake for options 4/7) | month |
//! | `iopt` | `iopt` | generator option (1..7 in production) | flag |
//! | `dtp` | `dtp(4)` | design-storm time-to-peak fraction by storm type | fraction |
//! | `dmxi` | `dmxi(4)` | initialized design-storm values retained for block completeness; live source never reads them | — |

/// Incremental owning struct for common `/bk4/`.
#[derive(Debug, Clone, PartialEq)]
pub struct Cbk4State {
    pub nc: [i32; 13],
    pub nt: i32,
    pub mo: i32,
    pub iopt: i32,
    /// `dtp(4)` — design-storm time-to-peak by `itype` (block data
    /// `cligen.f:1065`; consumed only by the `iopt = 7` override).
    pub dtp: [f32; 4],
    /// `dmxi(4)` — set by block data (`cligen.f:1066`), never read
    /// (source's own comment); carried for block completeness.
    pub dmxi: [f32; 4],
}

impl Default for Cbk4State {
    fn default() -> Self {
        Self {
            // Block data, cligen.f:1064.
            nc: [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365],
            // BSS zero until the option-4/7 paths write it.
            nt: 0,
            // BSS zero until jlt/day_gen writes it.
            mo: 0,
            // Block data, cligen.f:1083.
            iopt: -1,
            // Block data, cligen.f:1065-1066.
            dtp: [0.4, 0.32, 0.5, 0.5],
            dmxi: [18.24, 5.76, 32.88, 20.16],
        }
    }
}
