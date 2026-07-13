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

/// Owned typed projection of the legacy unit-7 header.
///
/// This is the pre-format authority for the immutable `.cli` header. In
/// particular, the monthly vectors are derived once with the faithful REAL*4
/// expression order and retained independently of the mutable generator state.
#[derive(Debug, Clone, PartialEq)]
pub(crate) struct LegacyCliHeader {
    pub(crate) version: f32,
    pub(crate) isim: i32,
    pub(crate) itemp: i32,
    pub(crate) igcode: i32,
    pub(crate) station_id: String,
    pub(crate) latitude_deg: f32,
    pub(crate) longitude_deg: f32,
    pub(crate) elevation_m: i32,
    pub(crate) observed_years: i32,
    pub(crate) begin_year: i32,
    pub(crate) simulated_years: i32,
    pub(crate) burn: i32,
    pub(crate) interpolation: i32,
    pub(crate) command_echo: String,
    pub(crate) monthly_tmax_c: [f32; 12],
    pub(crate) monthly_tmin_c: [f32; 12],
    pub(crate) monthly_solar_langley_per_day: [f32; 12],
    pub(crate) monthly_precip_mm: [f32; 12],
}

impl LegacyCliHeader {
    /// Capture the values used by `wxr_gen`'s header writes before daily
    /// generation mutates the common-block state.
    pub(crate) fn from_inputs(h: &HeaderInputs<'_>, bk7: &Cbk7State, nc: &[i32; 13]) -> Self {
        // Derived monthly values (cligen.f:3741-3750), REAL*4.
        let mut monthly_precip_mm = [0.0f32; 12];
        let mut monthly_tmax_c = [0.0f32; 12];
        let mut monthly_tmin_c = [0.0f32; 12];
        for month in 0..12 {
            let xm = (nc[month + 1] - nc[month]) as f32;
            monthly_precip_mm[month] =
                xm * bk7.prw[month][1] / (1.0 - bk7.prw[month][0] + bk7.prw[month][1]);
            monthly_precip_mm[month] = monthly_precip_mm[month] * bk7.rst[month][0] * 25.4;
            monthly_tmax_c[month] = (bk7.obmx[month] - 32.0) * (5.0 / 9.0);
            monthly_tmin_c[month] = (bk7.obmn[month] - 32.0) * (5.0 / 9.0);
        }
        Self {
            version: h.version,
            isim: if h.iopt == 4 || h.iopt == 7 { 2 } else { 1 },
            itemp: 0,
            igcode: h.igcode,
            station_id: h.stidd.to_owned(),
            latitude_deg: h.ylt,
            longitude_deg: h.yll,
            elevation_m: h.elev,
            observed_years: h.years,
            begin_year: h.iyear,
            simulated_years: h.numyr,
            burn: h.irand,
            interpolation: h.interp,
            command_echo: h.command_echo.to_owned(),
            monthly_tmax_c,
            monthly_tmin_c,
            monthly_solar_langley_per_day: bk7.obsl,
            monthly_precip_mm,
        }
    }
}

/// The wxr_gen unit-7 header block (`cligen.f:3717-3754`), emitted
/// only for `iopt ≥ 4` exactly as the source.
pub fn write_cli_header(out: &mut String, h: &HeaderInputs<'_>, bk7: &Cbk7State, nc: &[i32; 13]) {
    write_legacy_cli_header(out, &LegacyCliHeader::from_inputs(h, bk7, nc));
}

/// Render an owned pre-format header with the frozen Fortran formats.
pub(crate) fn write_legacy_cli_header(out: &mut String, h: &LegacyCliHeader) {
    // format 642: (f7.5)
    out.push_str(&f_edit(h.version, 7, 5));
    out.push('\n');
    // format 778: (3i4)
    out.push_str(&i_edit(h.isim as i64, 4));
    out.push_str(&i_edit(h.itemp as i64, 4));
    out.push_str(&i_edit(h.igcode as i64, 4));
    out.push('\n');
    // format 644 line 1
    out.push_str("  Station: ");
    out.push_str(&h.station_id);
    out.push_str("      ");
    out.push_str(" CLIGEN VER.");
    out.push_str(&f_edit(h.version, 8, 5));
    out.push_str(" -r:");
    out.push_str(&i_edit(h.burn as i64, 5));
    out.push_str(" -I:");
    out.push_str(&i_edit(h.interpolation as i64, 2));
    out.push('\n');
    // format 644 line 2
    out.push_str(
        " Latitude Longitude Elevation (m) Obs. Years   Beginning year  Years simulated Command Line:\n",
    );
    // format 644 line 3: 2f9.2,i12,2i12,i16,'          ',a
    out.push_str(&f_edit(h.latitude_deg, 9, 2));
    out.push_str(&f_edit(h.longitude_deg, 9, 2));
    out.push_str(&i_edit(h.elevation_m as i64, 12));
    out.push_str(&i_edit(h.observed_years as i64, 12));
    out.push_str(&i_edit(h.begin_year as i64, 12));
    out.push_str(&i_edit(h.simulated_years as i64, 16));
    out.push_str("          ");
    out.push_str(&h.command_echo);
    // arg_v(:av_len) carries ONE trailing blank: the main program's
    // length scan sets av_len one past the last non-blank
    // (cligen.f:670-674, 678-682).
    out.push(' ');
    out.push('\n');
    // format 500: two labeled lines of (1x,12(f5.1,1x)). The group's
    // trailing 1x only advances the position — a Fortran X descriptor
    // writes nothing unless later output lands past it, so the record
    // ends after the last value (no trailing blank).
    out.push_str(" Observed monthly ave max temperature (C)\n ");
    for (i, v) in h.monthly_tmax_c.iter().enumerate() {
        if i > 0 {
            out.push(' ');
        }
        out.push_str(&f_edit(*v, 5, 1));
    }
    out.push_str("\n Observed monthly ave min temperature (C)\n ");
    for (i, v) in h.monthly_tmin_c.iter().enumerate() {
        if i > 0 {
            out.push(' ');
        }
        out.push_str(&f_edit(*v, 5, 1));
    }
    out.push('\n');
    // format 520: (12(1x,f5.1)) — space BEFORE each value
    out.push_str(" Observed monthly ave solar radiation (Langleys/day)\n");
    for v in h.monthly_solar_langley_per_day {
        out.push(' ');
        out.push_str(&f_edit(v, 5, 1));
    }
    out.push('\n');
    // format 555: same shape as 520
    out.push_str(" Observed monthly ave precipitation (mm)\n");
    for v in h.monthly_precip_mm {
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
