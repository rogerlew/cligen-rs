//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:2153-2184 (`header`),
//!   2240-2483 (`sta_dat` characterized non-interactive paths), and
//!   2486-2652 (`sta_name` explicit interactive-only deferral)
//! Precision-Map: REAL*4 `version`; station values remain REAL*4 in
//!   `ParFile`/`sta_parms`
//! Faithful-Acceptance: exact header bytes + single-file fixture intake
//!   routed through the par-state snapshot gate
//!   (tests/par_state_identity.rs)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `version` | `version` | CLIGEN version rendered in the screen banner | — |
//! | `stidd` | `stidd` | fixed-width station identifier from record 1 | — |
//! | `nst`,`nstat` | same | state and station numeric codes | — |
//! | `igcode` | `igcode` | wind-information / ET-equation flag | flag |
//! | `infile` | `infile` | selected station-parameter path (`-i`) | path |
//! | `istate`,`index` | same | state/station selectors (`-S`/`-s`) | code |

use std::io::Write;
use std::path::Path;

use crate::cbk1::Cbk1State;
use crate::cbk7::Cbk7State;
use crate::cbk9::Cbk9State;
use crate::cinterp::CinterpState;

use super::{sta_parms, ParError, ParFile, StaParmsOut};

/// Explicit selection of one source `sta_dat` intake path.
#[derive(Debug, Clone, Copy)]
pub enum StaDatSelection<'a> {
    /// Characterized single-station `-i` path (`cligen.f:2392-2471`).
    SingleFile(&'a Path),
    /// Non-interactive `-S`+`-s` scan path. The path is recognized but
    /// deferred until a captured multi-station file supplies acceptance.
    StateStationFile {
        path: &'a Path,
        state_code: i32,
        station_code: i32,
    },
    /// Prompt-driven state/station selection through `sta_name`.
    Interactive,
}

/// Record-1 station identity plus `sta_parms`' output arguments.
#[derive(Debug, Clone)]
pub struct StaDatOut {
    pub stidd: String,
    pub nst: i32,
    pub nstat: i32,
    pub igcode: i32,
    pub parms: StaParmsOut,
}

/// Write the faithful CLIGEN screen banner (`cligen.f:2153-2184`).
///
/// `version` is rendered with the source's `f7.5` edit descriptor.
///
/// # Errors
/// Returns the writer's I/O error.
pub fn header(writer: &mut impl Write, version: f32) -> std::io::Result<()> {
    write!(
        writer,
        concat!(
            "\n\n",
            "  ********************************************************************\n",
            "  *                                                                  *\n",
            "  *              USDA - WATER EROSION PREDICTION PROJECT             *\n",
            "  *                 WEPP CLIMATE INPUT DATA GENERATOR                *\n",
            "  *                                                                  *\n",
            "  *                    CONTINUOUS SIMULATION AND                     *\n",
            "  *                       SINGLE STORM OPTIONS                       *\n",
            "  *                    with Command Line Options,                    *\n",
            "  *                        and Corrections to                        *\n",
            "  *                  Rainfall Intensity Calculations                 *\n",
            "  *                   and Random Number Generation.                  *\n",
            "  *                                                                  *\n",
            "  *                          VERSION {:7.5}                         *\n",
            "  *                     Revised from VERSION 4.2                     *\n",
            "  *                          September 2024                          *\n",
            "  *                                                                  *\n",
            "  *           (Use -h or /h to list command line options.)           *\n",
            "  *                                                                  *\n",
            "  ********************************************************************\n",
            "\n\n"
        ),
        version
    )
}

/// Load station parameters through the characterized `sta_dat` paths.
///
/// # Numerics
/// The selected [`ParFile`] and [`sta_parms`] retain the source REAL*4
/// precision map; this driver performs no numeric conversions.
///
/// # Errors
/// Returns [`ParError::Io`] or a parse error for the single-file path,
/// [`ParError::Unsupported`] for the uncaptured multi-station scan, and
/// [`ParError::InteractiveOnly`] for prompt-driven selection. Writer
/// failures return [`ParError::Output`].
pub fn sta_dat(
    selection: StaDatSelection<'_>,
    version: f32,
    writer: &mut impl Write,
    bk7: &mut Cbk7State,
    bk1: &mut Cbk1State,
    bk9: &mut Cbk9State,
    ci: &mut CinterpState,
) -> Result<StaDatOut, ParError> {
    // Live path calls header before station selection/open
    // (cligen.f:2337-2357).
    header(writer, version).map_err(|source| ParError::Output { source })?;

    let path = match selection {
        StaDatSelection::SingleFile(path) => path,
        StaDatSelection::StateStationFile { .. } => {
            return Err(ParError::Unsupported {
                surface: "sta_dat -S/-s multi-station scan",
            });
        }
        StaDatSelection::Interactive => {
            sta_name()?;
            unreachable!("sta_name always fails closed")
        }
    };

    let bytes = std::fs::read(path).map_err(|source| ParError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    // `write(*,*) infile`, cligen.f:2396 (list-directed leading blank).
    writeln!(writer, " {}", path.display()).map_err(|source| ParError::Output { source })?;
    let par = ParFile::parse(&bytes)?;
    let stidd = par.stidd.clone();
    let nst = par.nst;
    let nstat = par.nstat;
    let igcode = par.igcode;
    let parms = sta_parms(&par, bk7, bk1, bk9, ci);
    Ok(StaDatOut {
        stidd,
        nst,
        nstat,
        igcode,
        parms,
    })
}

/// Interactive station selection (`sta_name`, `cligen.f:2486-2652`).
///
/// The source unit consists entirely of prompt/read/catalog loops and
/// is unreachable on the fixture matrix's non-interactive paths.
///
/// # Errors
/// Always returns [`ParError::InteractiveOnly`].
pub fn sta_name() -> Result<(), ParError> {
    Err(ParError::InteractiveOnly {
        surface: "sta_name prompt/catalog loop",
    })
}
