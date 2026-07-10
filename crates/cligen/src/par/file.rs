//! `ParFile`: the typed `.par` model (SPEC-PAR). Parse replicates the
//! Fortran fixed-column reads; `to_bytes` emits the retained records
//! verbatim (the corpus-supported round-trip invariant).

use std::fmt;
use std::io;
use std::path::PathBuf;

/// Typed parse failure — fail closed per SPEC-PAR/AGENTS (no inferred
/// defaults for malformed input).
#[derive(Debug)]
pub enum ParError {
    /// The selected parameter file could not be read.
    Io { path: PathBuf, source: io::Error },
    /// The intake banner or path could not be written to the caller's
    /// output stream.
    Output { source: io::Error },
    /// A non-interactive source path exists but is deliberately not
    /// implemented without a fixture-backed acceptance surface.
    Unsupported { surface: &'static str },
    /// The requested path requires prompt/read loops and is unavailable
    /// from the non-interactive library API.
    InteractiveOnly { surface: &'static str },
    /// The file is not ASCII text (the Fortran surface is fixed byte
    /// columns; the typed model fails closed instead of guessing an encoding).
    NotText,
    /// The typed/lexeme-preserving surface accepts LF records only;
    /// accepting CRLF would let `str::lines` silently break byte identity.
    InvalidLineEnding,
    /// Fewer records than the 83-record read surface.
    TooFewRecords { found: usize },
    /// A non-blank numeric field that does not parse after Fortran
    /// blank stripping. `record` is 1-based, `cols` are 1-based
    /// inclusive.
    Field {
        record: usize,
        cols: (usize, usize),
        text: String,
    },
}

impl fmt::Display for ParError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParError::Io { path, source } => {
                write!(f, "cannot read .par file {}: {source}", path.display())
            }
            ParError::Output { source } => {
                write!(f, "cannot write station intake output: {source}")
            }
            ParError::Unsupported { surface } => write!(f, "unsupported .par surface: {surface}"),
            ParError::InteractiveOnly { surface } => {
                write!(f, "interactive-only .par surface: {surface}")
            }
            ParError::NotText => write!(f, ".par file is not ASCII text"),
            ParError::InvalidLineEnding => write!(f, ".par file must use LF line endings"),
            ParError::TooFewRecords { found } => {
                write!(f, ".par has {found} records; CLIGEN reads 83")
            }
            ParError::Field { record, cols, text } => write!(
                f,
                ".par record {record} cols {}-{}: unparseable field {text:?}",
                cols.0, cols.1
            ),
        }
    }
}

impl std::error::Error for ParError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ParError::Io { source, .. } | ParError::Output { source } => Some(source),
            _ => None,
        }
    }
}

/// One `.par` file: the typed read surface plus every record's raw
/// bytes (SPEC-PAR §Serialization — presentation is retained as
/// lexemes, not reconstructed).
#[derive(Debug, Clone)]
pub struct ParFile {
    /// Every record, verbatim, without line terminators.
    records: Vec<String>,
    /// Whether the file ended with a final newline (all fixtures do).
    trailing_newline: bool,
    // --- record 1 (a41,i2,i4,i2), cligen.f:2324/2459 ---
    pub stidd: String,
    pub nst: i32,
    pub nstat: i32,
    pub igcode: i32,
    // --- record 2 (6x,f7.2,6x,f7.2,7x,i3,7x,i2), cligen.f:2753 ---
    pub ylt: f32,
    pub yll: f32,
    pub years: i32,
    pub itype: i32,
    // --- record 3 (12x,i5,17x,f5.2) — TP5 falls in the 17x skip ---
    pub elev_ft: i32,
    pub tp6: f32,
    // --- records 4-17 (8x,12f6.2 / 12f6.3) ---
    pub rst: [[f32; 3]; 12],
    pub prw: [[f32; 2]; 12],
    pub obmx: [f32; 12],
    pub obmn: [f32; 12],
    pub stdtx: [f32; 12],
    pub stdtm: [f32; 12],
    pub obsl: [f32; 12],
    pub stdsl: [f32; 12],
    pub wi_raw: [f32; 12],
    pub rh: [f32; 12],
    pub timpkd: [f32; 12],
    // --- records 18-81 (8x,12f6.2), (((wvl(i,j,k),k),j),i) ---
    pub wvl: [[[f32; 12]; 4]; 16],
    // --- record 82 ---
    pub calm: [f32; 12],
    // --- record 83 (a19,f6.3,2(2x,a19,f6.3)) ---
    pub site: [String; 3],
    pub wgt: [f32; 3],
}

/// Fixed-column slice with `PAD='YES'` semantics: columns beyond the
/// record end read as blanks. `start` is 0-based, `width` in chars.
fn field(record: &str, start: usize, width: usize) -> String {
    let mut s = String::with_capacity(width);
    let bytes = record.as_bytes();
    for i in start..start + width {
        s.push(if i < bytes.len() {
            bytes[i] as char
        } else {
            ' '
        });
    }
    s
}

/// Fortran `Fw.d` read under `BLANK='NULL'`: blanks stripped, empty
/// field = 0.0, explicit decimal point overrides `d`, a point-free
/// field is scaled by 10^-d (no corpus instance; implemented for
/// fidelity by synthesizing the decimal point).
fn f_edit(
    record_1based: usize,
    record: &str,
    start: usize,
    width: usize,
    d: usize,
) -> Result<f32, ParError> {
    let raw = field(record, start, width);
    let stripped: String = raw.chars().filter(|&c| c != ' ').collect();
    if stripped.is_empty() {
        return Ok(0.0);
    }
    let text = if stripped.contains('.') {
        stripped.clone()
    } else {
        // insert the implied decimal point d digits from the right
        let (sign, digits) = match stripped.strip_prefix('-') {
            Some(rest) => ("-", rest),
            None => ("", stripped.as_str()),
        };
        let padded = format!("{digits:0>width$}", width = d.max(digits.len()));
        let split = padded.len() - d;
        format!("{sign}{}.{}", &padded[..split], &padded[split..])
    };
    text.parse::<f32>().map_err(|_| ParError::Field {
        record: record_1based,
        cols: (start + 1, start + width),
        text: raw,
    })
}

/// Fortran `Iw` read under `BLANK='NULL'`: blanks stripped, empty = 0.
fn i_edit(record_1based: usize, record: &str, start: usize, width: usize) -> Result<i32, ParError> {
    let raw = field(record, start, width);
    let stripped: String = raw.chars().filter(|&c| c != ' ').collect();
    if stripped.is_empty() {
        return Ok(0);
    }
    stripped.parse::<i32>().map_err(|_| ParError::Field {
        record: record_1based,
        cols: (start + 1, start + width),
        text: raw,
    })
}

/// `(8x,12f6.d)` — one monthly row (records 4-17, 18-82).
fn monthly_row(record_1based: usize, record: &str, d: usize) -> Result<[f32; 12], ParError> {
    let mut out = [0.0f32; 12];
    for (k, slot) in out.iter_mut().enumerate() {
        *slot = f_edit(record_1based, record, 8 + 6 * k, 6, d)?;
    }
    Ok(out)
}

/// Records 1-3, the scalar header surface (`sta_dat` record-1 read at
/// `cligen.f:2459`; `sta_parms` format 1000 at `cligen.f:2753/2793`).
struct ScalarRecords {
    stidd: String,
    nst: i32,
    nstat: i32,
    igcode: i32,
    ylt: f32,
    yll: f32,
    years: i32,
    itype: i32,
    elev_ft: i32,
    tp6: f32,
}

fn parse_scalars(records: &[String]) -> Result<ScalarRecords, ParError> {
    let r = |n: usize| records[n - 1].as_str();
    Ok(ScalarRecords {
        // record 1: (a41,i2,i4,i2)
        stidd: field(r(1), 0, 41),
        nst: i_edit(1, r(1), 41, 2)?,
        nstat: i_edit(1, r(1), 43, 4)?,
        igcode: i_edit(1, r(1), 47, 2)?,
        // record 2: (6x,f7.2,6x,f7.2,7x,i3,7x,i2)
        ylt: f_edit(2, r(2), 6, 7, 2)?,
        yll: f_edit(2, r(2), 19, 7, 2)?,
        years: i_edit(2, r(2), 33, 3)?,
        itype: i_edit(2, r(2), 43, 2)?,
        // record 3: (12x,i5,17x,f5.2)
        elev_ft: i_edit(3, r(3), 12, 5)?,
        tp6: f_edit(3, r(3), 34, 5, 2)?,
    })
}

/// Records 4-8, the column-viewed monthly stats (`rst(12,3)` /
/// `prw(12,2)`, read column-by-column at `cligen.f:2794-2796`).
#[allow(clippy::type_complexity)]
fn parse_rst_prw(records: &[String]) -> Result<([[f32; 3]; 12], [[f32; 2]; 12]), ParError> {
    let r = |n: usize| records[n - 1].as_str();
    let mut rst = [[0.0f32; 3]; 12];
    for (stat, rec) in (4..=6).enumerate() {
        let row = monthly_row(rec, r(rec), 2)?;
        for m in 0..12 {
            rst[m][stat] = row[m];
        }
    }
    let mut prw = [[0.0f32; 2]; 12];
    for (state, rec) in (7..=8).enumerate() {
        let row = monthly_row(rec, r(rec), 2)?;
        for m in 0..12 {
            prw[m][state] = row[m];
        }
    }
    Ok((rst, prw))
}

/// Records 18-83: the wind block and the site/weight record
/// (`cligen.f:2881-2883`).
#[allow(clippy::type_complexity)]
fn parse_wind(
    records: &[String],
) -> Result<([[[f32; 12]; 4]; 16], [f32; 12], [String; 3], [f32; 3]), ParError> {
    let r = |n: usize| records[n - 1].as_str();
    // records 18-81: (((wvl(i,j,k),k=1,12),j=1,4),i=1,16)
    let mut wvl = [[[0.0f32; 12]; 4]; 16];
    for (i, by_dir) in wvl.iter_mut().enumerate() {
        for (j, row) in by_dir.iter_mut().enumerate() {
            let rec = 18 + i * 4 + j;
            *row = monthly_row(rec, r(rec), 2)?;
        }
    }
    let calm = monthly_row(82, r(82), 2)?;
    // record 83: (a19,f6.3,2(2x,a19,f6.3))
    let site = [
        field(r(83), 0, 19),
        field(r(83), 27, 19),
        field(r(83), 54, 19),
    ];
    let wgt = [
        f_edit(83, r(83), 19, 6, 3)?,
        f_edit(83, r(83), 46, 6, 3)?,
        f_edit(83, r(83), 73, 6, 3)?,
    ];
    Ok((wvl, calm, site, wgt))
}

impl ParFile {
    /// Parse `.par` bytes per SPEC-PAR §Record grammar. Fails closed on
    /// non-text input, fewer than 83 records, or unparseable numeric
    /// fields; the tail (records 84+) is retained unparsed.
    pub fn parse(bytes: &[u8]) -> Result<ParFile, ParError> {
        let text = std::str::from_utf8(bytes).map_err(|_| ParError::NotText)?;
        if !text.is_ascii() {
            return Err(ParError::NotText);
        }
        if text.contains('\r') {
            return Err(ParError::InvalidLineEnding);
        }
        let trailing_newline = text.ends_with('\n');
        let records: Vec<String> = text.lines().map(str::to_owned).collect();
        if records.len() < 83 {
            return Err(ParError::TooFewRecords {
                found: records.len(),
            });
        }
        let r = |n: usize| records[n - 1].as_str(); // 1-based, as in the source

        let scalars = parse_scalars(&records)?;
        let (rst, prw) = parse_rst_prw(&records)?;
        let obmx = monthly_row(9, r(9), 2)?;
        let obmn = monthly_row(10, r(10), 2)?;
        let stdtx = monthly_row(11, r(11), 2)?;
        let stdtm = monthly_row(12, r(12), 2)?;
        let obsl = monthly_row(13, r(13), 2)?;
        let stdsl = monthly_row(14, r(14), 2)?;
        let wi_raw = monthly_row(15, r(15), 2)?;
        let rh = monthly_row(16, r(16), 2)?;
        let timpkd = monthly_row(17, r(17), 3)?;
        let (wvl, calm, site, wgt) = parse_wind(&records)?;

        Ok(ParFile {
            records,
            trailing_newline,
            stidd: scalars.stidd,
            nst: scalars.nst,
            nstat: scalars.nstat,
            igcode: scalars.igcode,
            ylt: scalars.ylt,
            yll: scalars.yll,
            years: scalars.years,
            itype: scalars.itype,
            elev_ft: scalars.elev_ft,
            tp6: scalars.tp6,
            rst,
            prw,
            obmx,
            obmn,
            stdtx,
            stdtm,
            obsl,
            stdsl,
            wi_raw,
            rh,
            timpkd,
            wvl,
            calm,
            site,
            wgt,
        })
    }

    /// Byte-preserving emission (SPEC-PAR invariant 1):
    /// `to_bytes(parse(b)) == b` for any accepted input.
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut out = self.records.join("\n");
        if self.trailing_newline {
            out.push('\n');
        }
        out.into_bytes()
    }
}
