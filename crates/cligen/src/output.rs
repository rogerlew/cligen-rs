//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: the `.cli` unit-7 text surface — wxr_gen header writes
//!   (`cligen.f:3722-3754`, formats 642/778/644/500/520/555/648),
//!   the day_gen daily row (format 2000, `cligen.f:3055-3056,
//!   3175-3176`), and the main-program run-end blank line
//!   (`cligen.f:965-966`, list-directed `write(7,*) ' '`).
//! Precision-Map: formatting only — every REAL field routes through
//!   the adjudicated [`crate::fortran_format`] (exact integer decimal
//!   rounding, ties-to-even); the two header F→C/smy computations are
//!   REAL*4 transcriptions (`cligen.f:3741-3750`)
//! Faithful-Acceptance: the 12-golden byte-parity gate
//!   (tests/cli_parity.rs)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `isim` | `isim` | 1 continuous (iopt 5/6), 2 single storm (iopt 4/7) | flag |
//! | `itemp` | `itemp` | breakpoint flag, always 0 on this surface | flag |
//! | `smy` | `smy(12)` | derived observed monthly precipitation | mm |
//! | `arg_v` | `arg_v(:av_len)` | the command echo (SPEC-RUNSPEC §Header echo) | — |

use crate::cbk7::Cbk7State;
use crate::fortran_format::{f_edit, i_edit};
use crate::modes::DailyRow;

/// Everything the wxr_gen header emission needs beyond station state.
pub struct HeaderInputs<'a> {
    pub version: f32,
    pub igcode: i32,
    pub stidd: &'a str,
    pub ylt: f32,
    pub yll: f32,
    pub years: i32,
    pub elev: i32,
    pub iopt: i32,
    pub irand: i32,
    pub interp: i32,
    /// Legacy-visible header values (SPEC-RUNSPEC §Header echo):
    /// `iyear` as resolved, `numyr` as the *command-block* value
    /// (−1 for storm modes, 100-defaulted for observed).
    pub iyear: i32,
    pub numyr: i32,
    pub command_echo: &'a str,
}

/// The wxr_gen unit-7 header block (`cligen.f:3717-3754`), emitted
/// only for `iopt ≥ 4` exactly as the source.
pub fn write_cli_header(out: &mut String, h: &HeaderInputs<'_>, bk7: &Cbk7State, nc: &[i32; 13]) {
    // format 642: (f7.5)
    out.push_str(&f_edit(h.version, 7, 5));
    out.push('\n');
    // format 778: (3i4)
    let isim = if h.iopt == 4 || h.iopt == 7 { 2 } else { 1 };
    let itemp = 0;
    out.push_str(&i_edit(isim as i64, 4));
    out.push_str(&i_edit(itemp as i64, 4));
    out.push_str(&i_edit(h.igcode as i64, 4));
    out.push('\n');
    // format 644 line 1
    out.push_str("  Station: ");
    out.push_str(h.stidd);
    out.push_str("      ");
    out.push_str(" CLIGEN VER.");
    out.push_str(&f_edit(h.version, 8, 5));
    out.push_str(" -r:");
    out.push_str(&i_edit(h.irand as i64, 5));
    out.push_str(" -I:");
    out.push_str(&i_edit(h.interp as i64, 2));
    out.push('\n');
    // format 644 line 2
    out.push_str(
        " Latitude Longitude Elevation (m) Obs. Years   Beginning year  Years simulated Command Line:\n",
    );
    // format 644 line 3: 2f9.2,i12,2i12,i16,'          ',a
    out.push_str(&f_edit(h.ylt, 9, 2));
    out.push_str(&f_edit(h.yll, 9, 2));
    out.push_str(&i_edit(h.elev as i64, 12));
    out.push_str(&i_edit(h.years as i64, 12));
    out.push_str(&i_edit(h.iyear as i64, 12));
    out.push_str(&i_edit(h.numyr as i64, 16));
    out.push_str("          ");
    out.push_str(h.command_echo);
    // arg_v(:av_len) carries ONE trailing blank: the main program's
    // length scan sets av_len one past the last non-blank
    // (cligen.f:670-674, 678-682).
    out.push(' ');
    out.push('\n');
    // Derived monthly values (cligen.f:3741-3750), REAL*4.
    let mut smy = [0.0f32; 12];
    let mut tmpcmx = [0.0f32; 12];
    let mut tmpcmn = [0.0f32; 12];
    for kkk in 0..12 {
        let xm = (nc[kkk + 1] - nc[kkk]) as f32;
        smy[kkk] = xm * bk7.prw[kkk][1] / (1.0 - bk7.prw[kkk][0] + bk7.prw[kkk][1]);
        smy[kkk] = smy[kkk] * bk7.rst[kkk][0] * 25.4;
        tmpcmx[kkk] = (bk7.obmx[kkk] - 32.0) * (5.0 / 9.0);
        tmpcmn[kkk] = (bk7.obmn[kkk] - 32.0) * (5.0 / 9.0);
    }
    // format 500: two labeled lines of (1x,12(f5.1,1x)). The group's
    // trailing 1x only advances the position — a Fortran X descriptor
    // writes nothing unless later output lands past it, so the record
    // ends after the last value (no trailing blank).
    out.push_str(" Observed monthly ave max temperature (C)\n ");
    for (i, v) in tmpcmx.iter().enumerate() {
        if i > 0 {
            out.push(' ');
        }
        out.push_str(&f_edit(*v, 5, 1));
    }
    out.push_str("\n Observed monthly ave min temperature (C)\n ");
    for (i, v) in tmpcmn.iter().enumerate() {
        if i > 0 {
            out.push(' ');
        }
        out.push_str(&f_edit(*v, 5, 1));
    }
    out.push('\n');
    // format 520: (12(1x,f5.1)) — space BEFORE each value
    out.push_str(" Observed monthly ave solar radiation (Langleys/day)\n");
    for v in bk7.obsl {
        out.push(' ');
        out.push_str(&f_edit(v, 5, 1));
    }
    out.push('\n');
    // format 555: same shape as 520
    out.push_str(" Observed monthly ave precipitation (mm)\n");
    for v in smy {
        out.push(' ');
        out.push_str(&f_edit(v, 5, 1));
    }
    out.push('\n');
    // format 648: the daily column header
    out.push_str(" da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n");
    out.push_str("             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n");
}

/// One daily unit-7 row (format 2000, `cligen.f:3055-3056`):
/// `2i3,1x,i5,1x,f5.1,1x,f5.2,1x,f4.2,1x,f6.2,2(1x,f5.1),1x,f4.0,
/// 1x,f4.1,2x,f4.0,1x,f5.1`.
pub fn write_daily_row(out: &mut String, r: &DailyRow) {
    out.push_str(&i_edit(r.jd as i64, 3));
    out.push_str(&i_edit(r.mo as i64, 3));
    out.push(' ');
    out.push_str(&i_edit(r.iyear as i64, 5));
    out.push(' ');
    out.push_str(&f_edit(r.xr, 5, 1));
    out.push(' ');
    out.push_str(&f_edit(r.dur, 5, 2));
    out.push(' ');
    out.push_str(&f_edit(r.tpr, 4, 2));
    out.push(' ');
    out.push_str(&f_edit(r.xmav, 6, 2));
    out.push(' ');
    out.push_str(&f_edit(r.tmxg, 5, 1));
    out.push(' ');
    out.push_str(&f_edit(r.tmng, 5, 1));
    out.push(' ');
    out.push_str(&f_edit(r.radg, 4, 0));
    out.push(' ');
    out.push_str(&f_edit(r.wv, 4, 1));
    out.push_str("  ");
    out.push_str(&f_edit(r.th, 4, 0));
    out.push(' ');
    out.push_str(&f_edit(r.tdp, 5, 1));
    out.push('\n');
}

/// The main-program run-end marker (`cligen.f:965-966`):
/// list-directed `write(7,*) ' '` = one leading blank + the blank.
pub fn write_run_end(out: &mut String) {
    out.push_str("  \n");
}
