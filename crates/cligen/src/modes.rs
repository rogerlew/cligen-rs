//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:2971-3195 (`day_gen`, the
//!   production day-loop driver) and the main-program generation setup
//!   865-902 (the cold-start surface). `wxr_gen`/`opt_calc`/`usr_opt`
//!   and the unit-7 FORMAT emission are item 8.
//! Precision-Map: REAL*4 throughout (integer `.prn` fields scale by
//!   the source's `·0.01`; the only new arithmetic is `th·clt` and
//!   the F→C conversions)
//! Faithful-Acceptance: cold-start replay — zero injected state; the
//!   complete `DailyRow` stream reproduced from block-data seeds +
//!   burn + this setup + the real `.par`/`.prn` inputs, against rows
//!   reconstructed from cg/wg/sd taps (tests/modes_identity.rs).
//!   Earlier unit replays retain the finer internal/tp assertions.
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `nbt` | `nbt` | first Julian day of the loop (1, or the storm day for iopt 4/7) | day |
//! | `ntd`,`ntd1` | same | days in the year / storm Julian day (iopt 4/7 overwrite `ntd = ntd1`) | day |
//! | `clt` | `clt` | 57.296 degrees-per-radian converter | °/rad |
//! | `q_gen_started` | same | SAVE'd flag: a 9999 sentinel was seen this run — forces the stop signal at year end (5.323 fix) | — |
//! | `moveto` | `moveto` | 225 = stop (observed EOF, or generation-started year end) | — |

use crate::calendar::jlt;
use crate::cbk1::Cbk1State;
use crate::cbk3::Cbk3State;
use crate::cbk4::Cbk4State;
use crate::cbk5::Cbk5State;
use crate::cbk7::Cbk7State;
use crate::cbk9::Cbk9State;
use crate::ccl1::Ccl1State;
use crate::cinterp::CinterpState;
use crate::crandom3::Crandom3State;
use crate::daily::{clgen, r5monb, windg, ClgenEvents};
use crate::deviates::DstgState;
use crate::libm_pinned::{cosf_pinned, sinf_pinned};
use crate::monthlies::lintrp;
use crate::observed::{PrnError, PrnReader};
use crate::rng::{randn, RansetState};
use crate::storm::{storm_block, wet_day_duration, SingleStormParams};

use crate::acm::AcmState;

/// `day_gen`'s SAVE state (`cligen.f:3040-3042`), caller-owned and
/// persistent across years.
#[derive(Debug, Clone, Copy, Default)]
pub struct DayGenState {
    pub q_gen_started: bool,
}

/// One unit-7 daily row's numeric values (`cligen.f:3175-3176` operand
/// order) — item 8's writer input. Temps and dew point are Celsius,
/// `th` is degrees (both converted in place by day_gen before the
/// write).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DailyRow {
    pub jd: i32,
    pub mo: i32,
    pub iyear: i32,
    pub xr: f32,
    pub dur: f32,
    pub tpr: f32,
    pub xmav: f32,
    pub tmxg: f32,
    pub tmng: f32,
    pub radg: f32,
    pub wv: f32,
    pub th: f32,
    pub tdp: f32,
}

/// day_gen's exit signal: `Stop` is the source's `moveto = 225`
/// (observed EOF mid-year, or `q_gen_started` at the year's end —
/// the 5.323 stop protocol consumed by wxr_gen).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DayGenExit {
    YearComplete,
    Stop,
}

/// The generation-time state bundle `day_gen` threads (one per run).
#[derive(Debug)]
pub struct GenState {
    pub bk1: Cbk1State,
    pub bk3: Cbk3State,
    pub bk4: Cbk4State,
    pub bk5: Cbk5State,
    pub bk7: Cbk7State,
    pub bk9: Cbk9State,
    pub ccl1: Ccl1State,
    pub ci: CinterpState,
    pub cr: Crandom3State,
    pub rs: RansetState,
    pub acm: AcmState,
    pub dg: DstgState,
    pub daygen: DayGenState,
    /// Cumulative Tdew-rangecheck events (screen-only in the source).
    pub tdew_events: u32,
}

/// `clt = 57.296` (`cligen.f:882`).
pub const CLT: f32 = 57.296;

/// The main program's generation setup (`cligen.f:865-902`): `sml`,
/// `r5monb`, the `ab` pair, the angle constants, the latitude
/// sin/cos, the wet/dry selector seed draw, the `rn1` warm, and the
/// six rolling-pair warms. The `r5max` scan (866-869) computes a
/// local the program never reads — not ported. Returns the state
/// bundle ready for year loops.
///
/// # Units
/// `ylt` is station latitude in degrees; initialized state fields retain
/// the units documented by their owning common-block modules.
///
/// # Numerics
/// Source REAL*4 throughout. Latitude sine/cosine use the pinned f32
/// implementations after division by the source's `CLT = 57.296`.
pub fn generation_setup(
    mut bk1: Cbk1State,
    mut bk4: Cbk4State,
    mut bk7: Cbk7State,
    mut bk9: Cbk9State,
    ci: CinterpState,
    ylt: f32,
) -> GenState {
    let bk5 = Cbk5State {
        sml: 0.0, // cligen.f:865
        ..Cbk5State::default()
    };
    r5monb(&bk4, &bk7, &mut bk9); // cligen.f:878
    bk9.ab = 0.02083; // cligen.f:879
    bk9.ab1 = 1.0 - bk9.ab; // cligen.f:880
    bk4.nt = 0; // cligen.f:881
    bk7.pit = 58.13; // cligen.f:883
                     // Source literal pi2 = 6.283185 (cligen.f:884) resembles TAU but
                     // is the specification's constant.
    #[allow(clippy::approx_constant)]
    {
        bk1.pi2 = 6.283185;
    }
    let xx = ylt / CLT; // cligen.f:885
    bk7.yls = sinf_pinned(xx);
    bk7.ylc = cosf_pinned(xx);
    let mut cr = Crandom3State::default();
    // Faithful main-program sequence (cligen.f:888): the draw follows
    // the block-data state construction.
    #[allow(clippy::field_reassign_with_default)]
    {
        cr.vv = randn(&mut bk7.k1);
    }
    bk7.l = 2;
    if cr.vv > bk7.prw[0][0] {
        bk7.l = 1; // cligen.f:890 — inverted sense, transcribed
    }
    bk9.rn1 = randn(&mut bk7.k7); // cligen.f:891
    bk7.v1 = randn(&mut bk7.k2); // cligen.f:894-899
    bk7.v3 = randn(&mut bk7.k3);
    bk7.v5 = randn(&mut bk7.k4);
    bk7.v7 = randn(&mut bk7.k5);
    bk7.v9 = randn(&mut bk7.k8);
    bk7.v11 = randn(&mut bk7.k9);
    bk7.msim = 1; // cligen.f:901-902
    bk7.nsim = 1;
    GenState {
        bk1,
        bk3: Cbk3State::default(),
        bk4,
        bk5,
        bk7,
        bk9,
        ccl1: Ccl1State::default(),
        ci,
        cr,
        rs: RansetState::default(),
        acm: AcmState::default(),
        dg: DstgState::default(),
        daygen: DayGenState::default(),
        tdew_events: 0,
    }
}

/// Faithful `day_gen` (`cligen.f:2971-3195`): one year's daily loop.
/// The unit-7 rows land in `rows` (iopt ≥ 4 days only, as the
/// source); the observed `.prn` stream is consumed per day under
/// `iopt = 6`.
///
/// # Units
/// Inputs and state retain source units. Emitted [`DailyRow`] temperatures
/// and dew point are Celsius, wind direction is degrees, and storm values
/// use the units documented by `crate::storm`.
///
/// # Numerics
/// Source REAL*4 expression order is preserved, including `.prn`
/// precipitation scaling, `th * CLT`, and the Fahrenheit-to-Celsius seam.
/// Transcendentals occur only in the already pinned downstream units.
///
/// # Errors
/// Propagates `.prn` input failures, including a missing observed-mode
/// stream (fail closed).
#[allow(clippy::too_many_arguments)]
pub fn day_gen(
    nbt: i32,
    iyear: i32,
    timpkd: &[f32; 13],
    ss: &SingleStormParams,
    itype: i32,
    ntd1: i32,
    ntd_in: i32,
    prn: Option<&mut PrnReader>,
    st: &mut GenState,
    rows: &mut Vec<DailyRow>,
) -> Result<DayGenExit, PrnError> {
    let mut ntd = ntd_in;
    // cligen.f:3064
    if st.bk4.iopt == 4 || st.bk4.iopt == 7 {
        ntd = ntd1;
    }
    let mut prn = prn;
    st.bk3.ida = nbt; // cligen.f:3065
    loop {
        if st.bk4.iopt == 6 {
            st.bk7.msim = 0;
            st.bk7.nsim = 0;
            // moveto = 225 armed before the read; EOF keeps it
            // (cligen.f:3070-3074, the 5.323 fix).
            let reader = prn.as_deref_mut().ok_or(PrnError::MissingStream)?;
            match reader.next()? {
                None => {
                    return Ok(DayGenExit::Stop);
                }
                Some(day) => {
                    if day.irida == 9999 || day.itmxg == 9999 {
                        st.daygen.q_gen_started = true;
                    }
                    if day.irida == 9999 {
                        st.bk7.nsim = 1;
                    }
                    if day.itmxg == 9999 || day.itmng == 9999 {
                        st.bk7.msim = 1;
                    }
                    st.bk5.r[(st.bk3.ida - 1) as usize] = (day.irida as f32) * 0.01;
                    st.bk7.tmxg = day.itmxg as f32;
                    st.bk7.tmng = day.itmng as f32;
                }
            }
        }
        // L1 IF (cligen.f:3086) — the EOF path returned above, so
        // moveto is always 0 here.
        {
            let idr = st.bk3.ida;
            let (mo, jd) = jlt(ntd, idr);
            st.bk4.mo = mo;
            if st.ci.interp == 1 {
                lintrp(mo, jd, ntd, &mut st.ci);
            }
            let events = clgen(
                ntd,
                iyear,
                &mut st.bk1,
                &st.bk3,
                &st.bk4,
                &mut st.bk5,
                &mut st.bk7,
                &st.ci,
                &mut st.cr,
                &mut st.rs,
                &mut st.acm,
            );
            if events != ClgenEvents::default() {
                st.tdew_events += 1;
            }
            windg(&mut st.bk1, &mut st.bk3, &st.bk4, &mut st.bk7, &mut st.cr);
            // cligen.f:3104: wind direction radians -> degrees in
            // place, keeping the source's assignment form.
            #[allow(clippy::assign_op_pattern)]
            {
                st.bk1.th = st.bk1.th * CLT;
            }
            let m = (mo - 1) as usize;
            let d = (jd - 1) as usize;
            let ida = (st.bk3.ida - 1) as usize;
            st.ccl1.prcip[m][d] = st.bk5.r[ida];
            st.ccl1.tgmx[m][d] = st.bk7.tmxg;
            st.ccl1.tgmn[m][d] = st.bk7.tmng;
            // cligen.f:3110-3112: F -> C in place.
            st.bk7.tmxg = (st.bk7.tmxg - 32.0) * (5.0 / 9.0);
            st.bk7.tmng = (st.bk7.tmng - 32.0) * (5.0 / 9.0);
            st.bk1.tdp = (st.bk1.tdp - 32.0) * (5.0 / 9.0);
            st.ccl1.radg[m][d] = st.bk7.ra;
            // The wet-day duration block + storm chain (item 6).
            let dur = wet_day_duration(
                &st.bk3,
                &st.bk4,
                &mut st.bk5,
                &mut st.bk7,
                &mut st.bk9,
                &mut st.dg,
                &mut st.cr,
            );
            st.ccl1.dur[m][d] = dur;
            if st.bk4.iopt >= 4 {
                let q = storm_block(
                    dur,
                    timpkd,
                    itype,
                    ss,
                    &st.bk3,
                    &st.bk4,
                    &mut st.bk5,
                    &mut st.bk7,
                    &mut st.bk9,
                    &mut st.dg,
                    &mut st.cr,
                );
                st.ccl1.dur[m][d] = q.dur;
                rows.push(DailyRow {
                    jd,
                    mo,
                    iyear,
                    xr: q.xr,
                    dur: q.dur,
                    tpr: q.tpr,
                    xmav: q.xmav,
                    tmxg: st.bk7.tmxg,
                    tmng: st.bk7.tmng,
                    radg: st.ccl1.radg[m][d],
                    wv: st.bk1.wv,
                    th: st.bk1.th,
                    tdp: st.bk1.tdp,
                });
            }
        }
        // cligen.f:3182-3183
        st.bk3.ida += 1;
        if st.bk3.ida > ntd {
            break;
        }
    }
    // cligen.f:3189: stop signal if generation started this year.
    if st.daygen.q_gen_started {
        Ok(DayGenExit::Stop)
    } else {
        Ok(DayGenExit::YearComplete)
    }
}

// ---- wxr_gen orchestration + main-program run assembly (item 8) ----

/// Typed run failure for the library orchestration.
#[derive(Debug)]
pub enum RunError {
    Par(crate::par::ParError),
    Prn(PrnError),
    Storm(crate::storm::StormError),
}

impl std::fmt::Display for RunError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RunError::Par(e) => write!(f, "{e}"),
            RunError::Prn(e) => write!(f, "{e}"),
            RunError::Storm(e) => write!(f, "{e}"),
        }
    }
}

impl std::error::Error for RunError {}

/// The typed run inputs the SPEC-RUNSPEC surface resolves to
/// (Stage C's serde layer produces this; the parity gate constructs
/// it directly from the golden equivalence table).
pub struct RunInputs<'a> {
    /// Legacy `iopt` (4 | 5 | 6 | 7 on this surface).
    pub iopt: i32,
    /// Interpolation mode 0..3.
    pub interp: i32,
    /// The `-r` burn count.
    pub burn: u32,
    /// `simulation.begin_year` (None = legacy -1 sentinel).
    pub begin_year: Option<i32>,
    /// `simulation.years` (None = legacy -1 sentinel).
    pub years: Option<i32>,
    pub par_bytes: &'a [u8],
    pub prn_bytes: Option<&'a [u8]>,
    pub storm: Option<crate::storm::SingleStormParams>,
    /// The version constant (`cligen.f:618`: 5.3230).
    pub version: f32,
    /// SPEC-RUNSPEC §Header echo — emitted verbatim.
    pub command_echo: &'a str,
}

/// The full faithful run: main-program assembly (burn → station →
/// option resolution → generation setup, `cligen.f:702-902`) +
/// `wxr_gen` (`cligen.f:3589-3816`: header, year plan, day loops) +
/// the run-end marker (`cligen.f:965-966`). Returns the `.cli` bytes.
pub fn run_to_cli(inp: &RunInputs<'_>) -> Result<String, RunError> {
    use crate::output::{write_cli_header, write_daily_row, write_run_end, HeaderInputs};

    // Seeds + burn (cligen.f:723-737).
    let mut bk7 = Cbk7State::default();
    bk7.burn(inp.burn);
    // Station intake (sta_dat single-file path).
    let par = crate::par::ParFile::parse(inp.par_bytes).map_err(RunError::Par)?;
    let mut bk1 = Cbk1State::default();
    let mut bk9 = Cbk9State::default();
    let mut ci = CinterpState {
        interp: inp.interp,
        ..CinterpState::default()
    };
    let out = crate::par::sta_parms(&par, &mut bk7, &mut bk1, &mut bk9, &mut ci);
    let mut bk4 = Cbk4State {
        iopt: inp.iopt,
        ..Cbk4State::default()
    };
    // usr_opt's observed pieces: open the stream, read ioyr
    // (cligen.f:3557-3574).
    let mut prn = match inp.prn_bytes {
        Some(bytes) => Some(PrnReader::new(bytes).map_err(RunError::Prn)?),
        None => None,
    };
    let ioyr = match &prn {
        Some(reader) => reader.initial_year().map_err(RunError::Prn)?,
        None => 0,
    };
    // sing_stm option resolution (typed intake; legacy -1 sentinels).
    let ss_out = crate::storm::sing_stm(
        ioyr,
        inp.begin_year.unwrap_or(-1),
        inp.years.unwrap_or(-1),
        inp.storm.as_ref(),
        &mut bk4,
    )
    .map_err(RunError::Storm)?;
    let mut iyear = ss_out.iyear.unwrap_or(0);
    // The header echoes the COMMAND-BLOCK numyr: -1 for storm modes
    // (never defaulted there), the resolved value otherwise
    // (SPEC-RUNSPEC §Header echo; wxr_gen:3728 reads command6 numyr).
    let numyr_header = if inp.iopt == 4 || inp.iopt == 7 {
        inp.years.unwrap_or(-1)
    } else {
        ss_out.numyr
    };
    let mut st = generation_setup(bk1, bk4, bk7, bk9, ci, out.ylt);

    // ---- wxr_gen ----
    let mut cli = String::new();
    let mut nbt = 1;
    if st.bk4.iopt >= 4 {
        write_cli_header(
            &mut cli,
            &HeaderInputs {
                version: inp.version,
                igcode: par.igcode,
                stidd: &par.stidd,
                ylt: out.ylt,
                yll: out.yll,
                years: out.years,
                elev: out.elev,
                iopt: st.bk4.iopt,
                irand: inp.burn as i32,
                interp: st.ci.interp,
                iyear,
                numyr: numyr_header,
                command_echo: inp.command_echo,
            },
            &st.bk7,
            &st.bk4.nc,
        );
    }
    // Year plan (wxr_gen:3758-3800).
    let mut loop_years = ss_out.numyr;
    let mut ntd1 = 0;
    if st.bk4.iopt == 4 || st.bk4.iopt == 7 {
        // The distinct iopt-4/7 nt test (note `.and.`, not
        // `.and..not.` — transcribed, cligen.f:3759-3763).
        st.bk4.nt = 0;
        if iyear - iyear / 400 * 400 == 0
            || (iyear - iyear / 4 * 4 == 0 && iyear - iyear / 100 * 100 == 0)
        {
            st.bk4.nt = 1;
        }
        let storm = inp.storm.as_ref().expect("sing_stm validated storm params");
        ntd1 = crate::calendar::jdt(&st.bk4.nc, storm.jd, storm.mo, st.bk4.nt);
        nbt = ntd1;
        loop_years = 1;
    }
    let mut ii = 1;
    let mut stopped = false;
    loop {
        let mut ntd = 365;
        // Gregorian test on iyear (wxr_gen:3766-3770); `!= 0` renders
        // the source's `.not.(mod-100 == 0)`.
        if (st.bk4.iopt <= 3 || st.bk4.iopt == 5 || st.bk4.iopt == 6)
            && (iyear - iyear / 400 * 400 == 0
                || (iyear - iyear / 4 * 4 == 0 && iyear - iyear / 100 * 100 != 0))
        {
            ntd = 366;
        }
        st.ccl1.zero_year();
        let mut rows = Vec::new();
        let exit = day_gen(
            nbt,
            iyear,
            &out.timpkd,
            inp.storm.as_ref().unwrap_or(&Default::default()),
            out.itype,
            ntd1,
            ntd,
            prn.as_mut(),
            &mut st,
            &mut rows,
        )
        .map_err(RunError::Prn)?;
        for row in &rows {
            write_daily_row(&mut cli, row);
        }
        if exit == DayGenExit::Stop {
            stopped = true;
            break;
        }
        // opt_calc is a no-op for iopt >= 4 (characterized:
        // cligen.f:3196-3324 has no branch past iopt = 3); moveto
        // stays 0, so the year advances (wxr_gen:3784-3789).
        iyear += 1;
        ii += 1;
        if ii > loop_years {
            break;
        }
    }
    // The run-end blank line is written only on normal termination
    // (main:941-973: the moveto = 225 stop path closes unit 7 without
    // it, cligen.f:978).
    if !stopped {
        write_run_end(&mut cli);
    }
    Ok(cli)
}
