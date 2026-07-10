//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:2188-2236 (`timepk`) and the
//!   day_gen storm block 3114-3176 (wet-day duration + the
//!   duration/Ipeak chain with the iopt-4/7 overrides). Stage C adds
//!   the `sing_stm` typed intake (3325-3493).
//! Precision-Map: REAL*4 throughout (the only transcendental is the
//!   already-pinned `logf_pinned`)
//! Faithful-Acceptance: sd/tp tap identity through the storm day-loop
//!   replay (fixtures/taps/storm/, tests/storm_identity.rs)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `timpkd` | `timpkd(0:12)` | cumulative time-to-peak distribution; index 0 is the caller-set 0.0 sentinel, live when the search lands at i = 1 | fraction |
//! | `z` | `z` | time-to-peak uniform (fresh `randn(k10)` when `iopt = 6`, batch `zx(dax)` otherwise) | — |
//! | `dur` | `dur(mo,jd)` | storm duration (`3.99/(−2·alog(1−r1))`, the live B. Yu 6/99 coefficient; clamp 24) | h |
//! | `xr` | `xr` | daily precipitation converted to mm (`r·25.4`) | mm |
//! | `tpr` | `tpr` | time to peak as fraction of duration (clamp 0.99) | fraction |
//! | `r5p` | `r5p` | max 30-min depth surrogate (`−2·xr·alog(1−r1)`, clamp `tymax(itype)`) | mm |
//! | `xmav` | `xmav` | normalized peak intensity (`r5p/(xr/dur)`; floors 1.01) | — |
//! | `tymax` | `tymax(4)` | per-`itype` r5p ceiling (main DATA, `cligen.f:602`) | mm |
//! | `usdur`,`ustpr`,`uxmav`,`damt` | same | single-storm user parameters (`sing_stm` reads) | h / fraction / in/h / in |

use crate::cbk3::Cbk3State;
use crate::cbk4::Cbk4State;
use crate::cbk5::Cbk5State;
use crate::cbk7::Cbk7State;
use crate::cbk9::Cbk9State;
use crate::crandom3::Crandom3State;
use crate::daily::alphb;
use crate::deviates::DstgState;
use crate::libm_pinned::logf_pinned;
use crate::rng::{randn, SeedState};

/// `tymax(4)` — upper limit of `r5p` by single-storm `itype`
/// (main-program DATA, `cligen.f:602`).
pub const TYMAX: [f32; 4] = [180.34, 154.94, 307.34, 330.2];

/// The single-storm parameters `sing_stm` reads (`cligen.f:3384-3399`);
/// unread garbage in the Fortran for other modes — the port passes
/// zeros there (only the `iopt = 4`/`7` overrides consume them).
#[derive(Debug, Clone, Copy, Default)]
pub struct SingleStormParams {
    /// Design storm amount, inches (`damt`).
    pub damt: f32,
    /// Storm duration, hours (`usdur`, `iopt = 4` only).
    pub usdur: f32,
    /// Time to peak as fraction of duration (`ustpr`, `iopt = 4` only).
    pub ustpr: f32,
    /// Maximum intensity, inches/hour (`uxmav`, `iopt = 4` only).
    pub uxmav: f32,
}

/// The chain's per-day output — the numeric inputs of the unit-7
/// daily row (`cligen.f:3175`), which item 8's `.cli` writer consumes.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct StormQuantities {
    pub xr: f32,
    pub dur: f32,
    pub tpr: f32,
    pub xmav: f32,
}

/// Faithful `timepk` (`cligen.f:2188-2236`): draw the time-to-peak
/// uniform (mode-split on `iopt`), walk the cumulative distribution,
/// interpolate within the landed 1/12 interval.
///
/// # Numerics
/// REAL*4; `0.08333` is the source literal. Writes the drawn uniform
/// to `cr.z` exactly as the source stores it in common.
pub fn timepk(
    timpkd: &[f32; 13],
    k10: &mut SeedState,
    bk4: &Cbk4State,
    cr: &mut Crandom3State,
) -> f32 {
    if bk4.iopt == 6 {
        cr.z = randn(k10);
    } else {
        cr.z = cr.zx(cr.dax as usize);
    }
    let mut i = 0usize;
    loop {
        i += 1;
        if !(timpkd[i] < cr.z && i < 12) {
            break;
        }
    }
    let diff1 = timpkd[i] - cr.z;
    let diff2 = timpkd[i] - timpkd[i - 1];
    let ratio = diff1 / diff2;
    0.08333 * (i as f32) - ratio * 0.08333
}

/// Wet-day duration (`day_gen:3114-3127`): normalize non-positive
/// rain to zero (duration 0), else run the first `alphb` call and
/// derive the storm duration.
#[allow(clippy::too_many_arguments)]
pub fn wet_day_duration(
    bk3: &Cbk3State,
    bk4: &Cbk4State,
    bk5: &mut Cbk5State,
    bk7: &mut Cbk7State,
    bk9: &mut Cbk9State,
    dg: &mut DstgState,
    cr: &mut Crandom3State,
) -> f32 {
    let ida = (bk3.ida - 1) as usize;
    if bk5.r[ida] <= 0.0 {
        bk5.r[ida] = 0.0;
        0.0
    } else {
        alphb(bk3, bk4, bk5, bk7, bk9, dg, cr);
        // The live 3.99 coefficient (B. Yu 6/99; 9.210 and 4.607 are
        // retained history, cligen.f:3121-3124).
        let mut dur = 3.99 / (-2.0 * logf_pinned(1.0 - bk9.r1));
        if dur > 24.0 {
            dur = 24.0;
        }
        dur
    }
}

/// The duration/Ipeak chain (`day_gen:3136-3171`): the `iopt ≥ 4`
/// storm-quantities block, including the second `alphb` call, the
/// `timepk` draw, every clamp, and the iopt-4/7 overrides.
///
/// # Numerics
/// REAL*4 as written — including the **transient infinity** for
/// `iopt ∈ {4,7}` (the just-zeroed `dur` makes `xr/dur = +∞`,
/// `xmav = 0`, floored to 1.01, then the override recomputes; IEEE
/// f32 reproduces the source exactly — deliberately unguarded).
///
/// # Panics
/// For `iopt < 4` (the CREAMS/screen modes have no unit-7 row and
/// leave these quantities undefined in the source; fail closed —
/// the modes package owns those surfaces).
#[allow(clippy::too_many_arguments)]
pub fn storm_block(
    dur_in: f32,
    timpkd: &[f32; 13],
    itype: i32,
    ss: &SingleStormParams,
    bk3: &Cbk3State,
    bk4: &Cbk4State,
    bk5: &mut Cbk5State,
    bk7: &mut Cbk7State,
    bk9: &mut Cbk9State,
    dg: &mut DstgState,
    cr: &mut Crandom3State,
) -> StormQuantities {
    assert!(
        bk4.iopt >= 4,
        "storm_block: iopt < 4 has no storm-quantity surface"
    );
    let mut dur = dur_in;
    if bk4.iopt == 4 || bk4.iopt == 7 {
        dur = 0.0;
    }
    let r = bk5.r[(bk3.ida - 1) as usize];
    let (mut xr, mut tpr, mut xmav);
    if r > 0.0 {
        alphb(bk3, bk4, bk5, bk7, bk9, dg, cr);
        xr = r * 25.4;
        tpr = timepk(timpkd, &mut bk7.k10, bk4, cr);
        if tpr > 0.99 {
            tpr = 0.99;
        }
        let mut r5p = -2.0 * xr * logf_pinned(1.0 - bk9.r1);
        if r5p > TYMAX[(itype - 1) as usize] {
            r5p = TYMAX[(itype - 1) as usize];
        }
        xmav = r5p / (xr / dur);
        if (bk7.tmxg + bk7.tmng) / 2.0 <= 0.0 {
            xmav = 1.01;
        }
        if xmav < 1.01 {
            xmav = 1.01;
        }
    } else {
        // The source's dead `tap4 = 0.0` store (3153) is not carried.
        xr = r * 25.4;
        xmav = 0.0;
        tpr = 0.0;
    }
    if bk4.iopt == 4 {
        dur = ss.usdur;
        xr = ss.damt * 25.4;
        tpr = ss.ustpr;
        xmav = (ss.uxmav * 25.4) / (xr / dur);
        if xmav < 1.01 {
            xmav = 1.01;
        }
    } else if bk4.iopt == 7 {
        dur = 24.0;
        xr = ss.damt * 25.4;
        xmav = TYMAX[(itype - 1) as usize] / (xr / dur);
        if xmav < 1.01 {
            xmav = 1.01;
        }
        tpr = bk4.dtp[(itype - 1) as usize];
    }
    StormQuantities { xr, dur, tpr, xmav }
}
