//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:2188-2236 (`timepk`), the
//!   day_gen storm block 3114-3176 (wet-day duration + the
//!   duration/Ipeak chain with the iopt-4/7 overrides), and the typed
//!   non-interactive surface of `sing_stm` 3325-3493.
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
//! | `r5p` | `r5p` | source-described peak rainfall rate (`−2·xr·alog(1−r1)`, clamp `tymax(itype)`; expression retained exactly) | mm/h |
//! | `xmav` | `xmav` | normalized peak intensity (`r5p/(xr/dur)`; floors 1.01) | — |
//! | `tymax` | `tymax(4)` | per-`itype` r5p ceiling (main DATA, `cligen.f:602`) | mm/h |
//! | `usdur`,`ustpr`,`uxmav`,`damt` | same | single-storm user parameters (`sing_stm` reads) | h / fraction / in/h / in |
//! | `mo`,`jd`,`ibyear` | same | typed storm date and beginning simulation year | month / day / year |
//! | `numyr`,`ioyr` | same | simulation-year count and observed-input beginning year | year |

use std::fmt;

use crate::cbk3::Cbk3State;
use crate::cbk4::Cbk4State;
use crate::cbk5::Cbk5State;
use crate::cbk7::Cbk7State;
use crate::cbk9::Cbk9State;
use crate::crandom3::Crandom3State;
use crate::daily::alphb;
use crate::deviates::DstgState;
use crate::libm_pinned::logf_pinned;
use crate::quality::process::ProcessCounters;
use crate::rng::{randn_observed, SeedState};

/// `tymax(4)` — upper limit of `r5p` by single-storm `itype`
/// (main-program DATA, `cligen.f:602`).
pub const TYMAX: [f32; 4] = [180.34, 154.94, 307.34, 330.2];

/// The single-storm parameters `sing_stm` reads (`cligen.f:3384-3399`).
/// Option 7 reads the date and amount but leaves the three option-4
/// shape fields unused.
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct SingleStormParams {
    /// Storm month (`mo`); written into [`Cbk4State::mo`].
    pub mo: i32,
    /// Day of the storm (`jd`).
    pub jd: i32,
    /// Beginning simulation year read with the storm date (`ibyear`).
    pub ibyear: i32,
    /// Design storm amount, inches (`damt`).
    pub damt: f32,
    /// Storm duration, hours (`usdur`, `iopt = 4` only).
    pub usdur: f32,
    /// Time to peak as fraction of duration (`ustpr`, `iopt = 4` only).
    pub ustpr: f32,
    /// Maximum intensity, inches/hour (`uxmav`, `iopt = 4` only).
    pub uxmav: f32,
}

/// Values written by the characterized, non-interactive `sing_stm`
/// intake surface. `None` means the source mode does not assign that
/// output (`iopt = 1` assigns neither; continuous modes assign no `jd`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SingStmOut {
    pub jd: Option<i32>,
    pub iyear: Option<i32>,
    pub numyr: i32,
}

/// Typed deferrals for `sing_stm` surfaces that remain outside the
/// non-interactive library API.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StormError {
    /// The source would enter a prompt/read loop for missing input.
    InteractiveOnly { surface: &'static str },
    /// File/unit plumbing or an unrecognized mode has no library surface.
    Unsupported { surface: &'static str },
}

impl fmt::Display for StormError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StormError::InteractiveOnly { surface } => {
                write!(f, "interactive-only storm surface: {surface}")
            }
            StormError::Unsupported { surface } => {
                write!(f, "unsupported storm surface: {surface}")
            }
        }
    }
}

impl std::error::Error for StormError {}

/// Typed, non-interactive `sing_stm` intake (`cligen.f:3325-3421`).
/// Prompt reads are supplied through [`SingleStormParams`] or scalar
/// arguments; file opening and overwrite policy are separate deferrals.
///
/// # Units
/// `SingleStormParams` retains the source units: `damt` in inches,
/// `usdur` in hours, `ustpr` as a fraction, and `uxmav` in inches/hour.
///
/// # Numerics
/// No floating-point computation occurs. Option 6 applies only the
/// source's exact `-1` defaults (`ibyear = ioyr`, `numyr = 100`).
///
/// # Errors
/// Returns [`StormError::InteractiveOnly`] when required typed values
/// are absent and the source would prompt, or [`StormError::Unsupported`]
/// for an option outside 1 through 7.
pub fn sing_stm(
    ioyr: i32,
    ibyear: i32,
    numyr: i32,
    single_storm: Option<&SingleStormParams>,
    bk4: &mut Cbk4State,
) -> Result<SingStmOut, StormError> {
    match bk4.iopt {
        1 => Ok(SingStmOut {
            jd: None,
            iyear: None,
            numyr,
        }),
        4 | 7 => {
            let params = single_storm.ok_or(StormError::InteractiveOnly {
                surface: "sing_stm option-4/7 storm parameter prompts",
            })?;
            bk4.mo = params.mo;
            Ok(SingStmOut {
                jd: Some(params.jd),
                iyear: Some(params.ibyear),
                numyr,
            })
        }
        6 => Ok(SingStmOut {
            jd: None,
            iyear: Some(if ibyear == -1 { ioyr } else { ibyear }),
            numyr: if numyr == -1 { 100 } else { numyr },
        }),
        2 | 3 | 5 => {
            if ibyear <= 0 {
                return Err(StormError::InteractiveOnly {
                    surface: "sing_stm beginning simulation year prompt",
                });
            }
            if numyr <= 0 {
                return Err(StormError::InteractiveOnly {
                    surface: "sing_stm simulation-year count prompt",
                });
            }
            Ok(SingStmOut {
                jd: None,
                iyear: Some(ibyear),
                numyr,
            })
        }
        _ => Err(StormError::Unsupported {
            surface: "sing_stm iopt outside 1..=7",
        }),
    }
}

/// Explicit deferral for the source's output-name prompt loop
/// (`cligen.f:3425-3430`).
///
/// # Errors
/// Always returns [`StormError::InteractiveOnly`].
pub fn sing_stm_interactive_output_name() -> Result<(), StormError> {
    Err(StormError::InteractiveOnly {
        surface: "sing_stm output filename prompt",
    })
}

/// Explicit deferral for unit-7/8 open, rewind, and overwrite handling
/// (`cligen.f:3432-3488`); filesystem policy belongs to the CLI/output
/// layer.
///
/// # Errors
/// Always returns [`StormError::Unsupported`].
pub fn sing_stm_output_file_management() -> Result<(), StormError> {
    Err(StormError::Unsupported {
        surface: "sing_stm Fortran unit-7/8 file management",
    })
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
    process: &mut ProcessCounters,
) -> f32 {
    if bk4.iopt == 6 {
        cr.z = randn_observed(k10, 9, process);
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
    process: &mut ProcessCounters,
) -> f32 {
    let ida = (bk3.ida - 1) as usize;
    if bk5.r[ida] <= 0.0 {
        bk5.r[ida] = 0.0;
        0.0
    } else {
        alphb(bk3, bk4, bk5, bk7, bk9, dg, cr, process);
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
    process: &mut ProcessCounters,
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
        alphb(bk3, bk4, bk5, bk7, bk9, dg, cr, process);
        xr = r * 25.4;
        tpr = timepk(timpkd, &mut bk7.k10, bk4, cr, process);
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
