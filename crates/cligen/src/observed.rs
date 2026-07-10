//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: the observed-mode unit-9 read surface —
//!   reference/cligen532/cligen.f:3052 (format `(15x,3i5)`) and
//!   3067-3083 (the per-day read/EOF protocol consumed by `day_gen`)
//! Precision-Map: integer fields (the f32 scaling happens in day_gen)
//! Faithful-Acceptance: cold-start observed replay over the real
//!   fixture `ws.prn`/`ws-truncated.prn` files
//!   (tests/modes_identity.rs)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `irida` | `irida` | observed daily precipitation | hundredths of an inch (9999 = generate) |
//! | `itmxg`,`itmng` | same | observed daily max/min temperature | °F (9999 = generate) |

use std::fmt;

/// Typed `.prn` input failure — fail closed, no inferred defaults.
#[derive(Debug, PartialEq, Eq)]
pub enum PrnError {
    /// `day_gen` was invoked in observed mode without a reader.
    MissingStream,
    NotText,
    /// 1-based record and columns of an unparseable integer field.
    Field {
        record: usize,
        cols: (usize, usize),
        text: String,
    },
}

impl fmt::Display for PrnError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PrnError::MissingStream => write!(f, "observed mode requires a .prn stream"),
            PrnError::NotText => write!(f, ".prn file is not ASCII text"),
            PrnError::Field { record, cols, text } => write!(
                f,
                ".prn record {record} cols {}-{}: unparseable field {text:?}",
                cols.0, cols.1
            ),
        }
    }
}

impl std::error::Error for PrnError {}

/// One observed day as `day_gen` reads it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PrnDay {
    pub irida: i32,
    pub itmxg: i32,
    pub itmng: i32,
}

/// Sequential reader over an observed `.prn` byte stream, replicating
/// the Fortran `(15x,3i5)` record read: columns 16-20, 21-25, 26-30,
/// blanks stripped (`BLANK='NULL'`), short records blank-padded
/// (`PAD='YES'`). The fixture files are CRLF with left-justified
/// integers — the CR sits beyond column 30, so neither the Fortran
/// format nor this reader ever sees it.
#[derive(Debug)]
pub struct PrnReader {
    records: Vec<String>,
    pos: usize,
}

fn i_field(
    record_1based: usize,
    record: &str,
    start: usize,
    width: usize,
) -> Result<i32, PrnError> {
    let bytes = record.as_bytes();
    let mut raw = String::with_capacity(width);
    for i in start..start + width {
        raw.push(if i < bytes.len() {
            bytes[i] as char
        } else {
            ' '
        });
    }
    let stripped: String = raw.chars().filter(|c| *c != ' ').collect();
    if stripped.is_empty() {
        return Ok(0);
    }
    stripped.parse::<i32>().map_err(|_| PrnError::Field {
        record: record_1based,
        cols: (start + 1, start + width),
        text: raw,
    })
}

impl PrnReader {
    /// Load a `.prn` byte stream (fails closed on non-ASCII).
    ///
    /// # Errors
    /// Returns [`PrnError::NotText`] unless `bytes` is ASCII text.
    pub fn new(bytes: &[u8]) -> Result<Self, PrnError> {
        let text = std::str::from_utf8(bytes).map_err(|_| PrnError::NotText)?;
        if !text.is_ascii() {
            return Err(PrnError::NotText);
        }
        Ok(PrnReader {
            records: text.lines().map(str::to_owned).collect(),
            pos: 0,
        })
    }

    /// The `read(9,1000,end=199)` step: `Ok(None)` is end-of-file
    /// (the 5.323 `moveto = 225` path).
    ///
    /// # Errors
    /// Returns [`PrnError::Field`] for a nonblank field that is not a
    /// valid `i32`; the reader never substitutes a value.
    #[allow(clippy::should_implement_trait)]
    pub fn next(&mut self) -> Result<Option<PrnDay>, PrnError> {
        if self.pos >= self.records.len() {
            return Ok(None);
        }
        let record = &self.records[self.pos];
        self.pos += 1;
        let n = self.pos;
        Ok(Some(PrnDay {
            irida: i_field(n, record, 15, 5)?,
            itmxg: i_field(n, record, 20, 5)?,
            itmng: i_field(n, record, 25, 5)?,
        }))
    }
}
