//! Faithful `sta_parms` (`cligen.f:2656-2967`): distribute the parsed
//! `.par` values into the common-block state, derive the load-time
//! quantities, and run the par-time interpolation setup.
//!
//! The Fortran unit reads records 2-83 from open unit 10; the port consumes
//! serialization-independent [`FixedMonthly5323`] state (record 1 is
//! `sta_dat`'s read — Stage C).
//! The interactive display block (`cligen.f:2939-2965`) is dead on
//! every non-interactive path (`numarg > 0` forces `yc = 'N'`) and is
//! not ported (intake-path-characterization.md).

use crate::cbk1::Cbk1State;
use crate::cbk7::Cbk7State;
use crate::cbk9::Cbk9State;
use crate::cinterp::CinterpState;
use crate::monthlies::{fouri1, ryf1};
use crate::par::ParFile;
use crate::station::FixedMonthly5323;

/// `sta_parms`' output arguments (`cligen.f:2656-2659`).
#[derive(Debug, Clone)]
pub struct StaParmsOut {
    /// Station latitude, °N (`ylt`).
    pub ylt: f32,
    /// Station longitude, °E (`yll`).
    pub yll: f32,
    /// Years of record (`years`).
    pub years: i32,
    /// Single-storm parameter type (`itype`).
    pub itype: i32,
    /// Elevation in whole meters — the file's feet value converted in
    /// place by `elev = elev*.3048` (f32 multiply, truncation toward
    /// zero on integer assignment; `cligen.f:2886`).
    pub elev: i32,
    /// Max 6-h precipitation depth, inches (`tp6`).
    pub tp6: f32,
    /// `timpkd(0:12)`: index 0 is the caller-set 0.0 sentinel
    /// (`cligen.f:846, 2338`), 1..12 the record-17 values.
    pub timpkd: [f32; 13],
    /// Record-83 station weights (0.0 across the corpus — the record
    /// read is blank; SPEC-PAR).
    pub wgt: [f32; 3],
    /// Record-83 station names (blank across the corpus).
    pub site: [String; 3],
}

/// Faithful `sta_parms` state distribution. Reads nothing from the
/// filesystem: `par` is the validated legacy typed surface, `ci.interp` plays
/// the role of the `/interp/` common's mode field (set from the `-I`
/// flag by the caller).
///
/// # Numerics
/// REAL*4 throughout. Derivations in source order: `wi` halving
/// (`cligen.f:2810-2812`), interpolation setup (2830-2868, on the
/// halved `wi` and the shifted parameter-14 `timpkd` window — see
/// SPEC-PAR), elevation feet→meters (2886), temperature CVs via the
/// Rankine offset and the guarded radiation CV (2889-2904), and the
/// cumulative wind-direction distribution (2910-2925).
pub fn sta_parms(
    par: &ParFile,
    bk7: &mut Cbk7State,
    bk1: &mut Cbk1State,
    bk9: &mut Cbk9State,
    ci: &mut CinterpState,
) -> StaParmsOut {
    sta_parms_fixed(par.fixed_monthly(), bk7, bk1, bk9, ci)
}

// Source uses assignment forms that must remain visible; keep the load-time
// derivations line-for-line against the source.
#[allow(clippy::assign_op_pattern)]
pub(crate) fn sta_parms_fixed(
    par: &FixedMonthly5323,
    bk7: &mut Cbk7State,
    bk1: &mut Cbk1State,
    bk9: &mut Cbk9State,
    ci: &mut CinterpState,
) -> StaParmsOut {
    // Distribution of the raw reads (cligen.f:2793-2815).
    bk7.rst = par.rst;
    bk7.prw = par.prw;
    bk7.obmx = par.obmx;
    bk7.obmn = par.obmn;
    bk7.stdtx = par.stdtx;
    bk7.stdtm = par.stdtm;
    bk7.obsl = par.obsl;
    bk7.stdsl = par.stdsl;
    bk9.wi = par.wi_raw;
    bk1.rh = par.rh;
    let mut timpkd = [0.0f32; 13];
    timpkd[1..].copy_from_slice(&par.timpkd);

    // wi is input as max 30-min intensity; converted to depth
    // (cligen.f:2804-2812, B. Yu 7/7/1999).
    for i in 0..12 {
        bk9.wi[i] = 0.5 * bk9.wi[i];
    }

    // Par-time interpolation setup (cligen.f:2829-2868). Parameter 14
    // receives the shifted window [timpkd(0), timpkd(1..11)] — the
    // array-name argument passes the 0-based array's first element
    // (SPEC-PAR §timpkd window quirk).
    let timpk_window: [f32; 12] = std::array::from_fn(|i| timpkd[i]);
    if ci.interp == 2 {
        fouri1(&bk7.rst_col(1), 1, ci);
        fouri1(&bk7.rst_col(2), 2, ci);
        fouri1(&bk7.rst_col(3), 3, ci);
        fouri1(&bk7.prw_col(1), 4, ci);
        fouri1(&bk7.prw_col(2), 5, ci);
        fouri1(&bk7.obmx, 6, ci);
        fouri1(&bk7.obmn, 7, ci);
        fouri1(&bk7.stdtx, 8, ci);
        fouri1(&bk7.stdtm, 9, ci);
        fouri1(&bk7.obsl, 10, ci);
        fouri1(&bk7.stdsl, 11, ci);
        fouri1(&bk9.wi, 12, ci);
        fouri1(&bk1.rh, 13, ci);
        fouri1(&timpk_window, 14, ci);
    } else if ci.interp == 3 {
        ryf1(&bk7.rst_col(1), 1, ci);
        ryf1(&bk7.rst_col(2), 2, ci);
        ryf1(&bk7.rst_col(3), 3, ci);
        ryf1(&bk7.prw_col(1), 4, ci);
        ryf1(&bk7.prw_col(2), 5, ci);
        ryf1(&bk7.obmx, 6, ci);
        ryf1(&bk7.obmn, 7, ci);
        ryf1(&bk7.stdtx, 8, ci);
        ryf1(&bk7.stdtm, 9, ci);
        ryf1(&bk7.obsl, 10, ci);
        ryf1(&bk7.stdsl, 11, ci);
        ryf1(&bk9.wi, 12, ci);
        ryf1(&bk1.rh, 13, ci);
        ryf1(&timpk_window, 14, ci);
    }

    // Wind reads (cligen.f:2881-2883).
    bk1.wvl = par.wvl;
    bk1.calm = par.calm;
    let site = par.site.clone();
    let wgt = par.wgt;

    // elev is integer, the file value floating-point feet; in-place
    // feet→meters with truncation (cligen.f:2884-2886).
    let elev = ((par.elev_ft as f32) * 0.3048) as i32;

    // CV derivation; observed temperatures are Fahrenheit, converted to
    // Rankine for the CV denominators (cligen.f:2889-2904).
    for i in 0..12 {
        bk7.cvtm[i] = bk7.stdtm[i] / (bk7.obmn[i] + 459.67);
        bk7.cvtx[i] = bk7.stdtx[i] / (bk7.obmx[i] + 459.67);
        if bk7.obsl[i] <= 0.0 {
            bk7.cvs[i] = 0.0;
        } else {
            bk7.cvs[i] = bk7.stdsl[i] / bk7.obsl[i];
        }
    }

    // Cumulative wind-direction distribution (cligen.f:2910-2925).
    for i in 0..12 {
        bk1.dir[i][0] = bk1.wvl[0][0][i];
    }
    for i in 0..12 {
        for j in 1..16 {
            bk1.dir[i][j] = bk1.dir[i][j - 1] + bk1.wvl[j][0][i];
        }
        bk1.dir[i][16] = 100.0;
    }
    for i in 0..12 {
        for j in 0..17 {
            bk1.dir[i][j] = bk1.dir[i][j] * 0.01;
        }
    }

    StaParmsOut {
        ylt: par.ylt,
        yll: par.yll,
        years: par.years,
        itype: par.itype,
        elev,
        tp6: par.tp6,
        timpkd,
        wgt,
        site,
    }
}
