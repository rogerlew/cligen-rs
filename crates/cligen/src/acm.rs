//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:4705-7165 (ACM cluster)
//! Precision-Map: DOUBLE PRECISION (f64) throughout; machine constants
//!   retain the embedded IEEE configuration from ipmpar
//! Faithful-Acceptance: fixtures/taps/stage-c-vectors.tap plus ranset
//!   sequential replay; f64 log/sin/exp vectors adjudicate libm use
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `p`,`q` | `p,q` | lower and upper cumulative probabilities | — |
//! | `x` | `x` | distribution argument / inverse-search point | — |
//! | `df` | `df` | chi-square degrees of freedom | — |
//! | `ans`,`qans` | `ans,qans` | incomplete-gamma P and Q ratios | — |
//! | `status` | `status` | reverse-communication / CDF status | flag |
//! | `qleft`,`qhi` | `qleft,qhi` | failed-bound direction/sign flags | flag |
//! | `a`,`b`,`c`,`d` | same | Bus–Dekker zero-finder points | — |
//! | `fa`,`fb`,`fc`,`fd` | same | function values at those points | — |
//!
//! The reverse-communication `ASSIGN`/assigned-GOTO continuations in
//! `dinvr` and `dzror` are explicit enums stored in their SAVE-state
//! structs. Their ENTRY points `dstinv` and `dstzr` are separate functions
//! over those same structs (`cligen.f:5316,5623`).

use crate::libm_pinned::exp_pinned;

/// Result surface of `cdfchi` (`cligen.f:4705-4951`).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CdfChiResult {
    pub p: f64,
    pub q: f64,
    pub x: f64,
    pub df: f64,
    pub status: i32,
    pub bound: f64,
}

/// Result of one `dinvr` reverse-communication step.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DinvrResult {
    pub status: i32,
    pub x: f64,
    pub qleft: bool,
    pub qhi: bool,
}

/// Result of one `dzror` reverse-communication step.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DzrorResult {
    pub status: i32,
    pub x: f64,
    pub xlo: f64,
    pub xhi: f64,
    pub qleft: bool,
    pub qhi: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum InvrStage {
    #[default]
    Unset,
    AwaitSmall,
    AwaitBig,
    AwaitInitial,
    AwaitUpper,
    AwaitLower,
    InZero,
}

/// SAVE storage shared by `dstinv` and `dinvr` (`cligen.f:5129-5154`).
#[derive(Debug, Clone)]
pub struct DinvrState {
    small: f64,
    big: f64,
    absstp: f64,
    relstp: f64,
    stpmul: f64,
    abstol: f64,
    reltol: f64,
    stage: InvrStage,
    xsave: f64,
    fsmall: f64,
    fbig: f64,
    qincr: bool,
    step: f64,
    xlb: f64,
    xub: f64,
    qleft: bool,
    qhi: bool,
}

impl Default for DinvrState {
    fn default() -> Self {
        Self {
            small: 0.0,
            big: 0.0,
            absstp: 0.0,
            relstp: 0.0,
            stpmul: 0.0,
            abstol: 0.0,
            reltol: 0.0,
            stage: InvrStage::Unset,
            xsave: 0.0,
            fsmall: 0.0,
            fbig: 0.0,
            qincr: false,
            step: 0.0,
            xlb: 0.0,
            xub: 0.0,
            qleft: false,
            qhi: false,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum ZrorStage {
    #[default]
    Unset,
    AwaitFb,
    AwaitFa,
    AwaitFbStep,
}

/// SAVE storage shared by `dstzr` and `dzror` (`cligen.f:5480-5500`).
#[derive(Debug, Clone)]
pub struct DzrorState {
    xxlo: f64,
    xxhi: f64,
    abstol: f64,
    reltol: f64,
    stage: ZrorStage,
    x: f64,
    xlo: f64,
    xhi: f64,
    a: f64,
    b: f64,
    c: f64,
    d: f64,
    fa: f64,
    fb: f64,
    fc: f64,
    fd: f64,
    w: f64,
    mb: f64,
    ext: i32,
    first: bool,
    qleft: bool,
    qhi: bool,
}

impl Default for DzrorState {
    fn default() -> Self {
        Self {
            xxlo: 0.0,
            xxhi: 0.0,
            abstol: 0.0,
            reltol: 0.0,
            stage: ZrorStage::Unset,
            x: 0.0,
            xlo: 0.0,
            xhi: 0.0,
            a: 0.0,
            b: 0.0,
            c: 0.0,
            d: 0.0,
            fa: 0.0,
            fb: 0.0,
            fc: 0.0,
            fd: 0.0,
            w: 0.0,
            mb: 0.0,
            ext: 0,
            first: false,
            qleft: false,
            qhi: false,
        }
    }
}

/// Owning aggregate for the two independent ACM SAVE units.
#[derive(Debug, Clone, Default)]
pub struct AcmState {
    pub dinvr: DinvrState,
    pub dzror: DzrorState,
}

/// `dstinv` ENTRY — configure inverse search (`cligen.f:5316-5407`).
#[allow(clippy::too_many_arguments)]
pub fn dstinv(
    zsmall: f64,
    zbig: f64,
    zabsst: f64,
    zrelst: f64,
    zstpmu: f64,
    zabsto: f64,
    zrelto: f64,
    state: &mut DinvrState,
) {
    state.small = zsmall;
    state.big = zbig;
    state.absstp = zabsst;
    state.relstp = zrelst;
    state.stpmul = zstpmu;
    state.abstol = zabsto;
    state.reltol = zrelto;
    state.stage = InvrStage::Unset;
    state.qleft = false;
    state.qhi = false;
}

/// `dstzr` ENTRY — configure zero search (`cligen.f:5623-5691`).
pub fn dstzr(zxlo: f64, zxhi: f64, zabstl: f64, zreltl: f64, state: &mut DzrorState) {
    state.xxlo = zxlo;
    state.xxhi = zxhi;
    state.abstol = zabstl;
    state.reltol = zreltl;
    state.stage = ZrorStage::Unset;
    state.qleft = false;
    state.qhi = false;
}

fn dzror_result(status: i32, state: &DzrorState) -> DzrorResult {
    DzrorResult {
        status,
        x: state.x,
        xlo: state.xlo,
        xhi: state.xhi,
        qleft: state.qleft,
        qhi: state.qhi,
    }
}

/// Bus–Dekker zero finder with reverse communication — faithful `dzror`
/// (`cligen.f:5419-5700`).
pub fn dzror(status: i32, x: f64, fx: f64, state: &mut DzrorState) -> DzrorResult {
    if status <= 0 {
        state.xlo = state.xxlo;
        state.xhi = state.xxhi;
        state.b = state.xlo;
        state.x = state.xlo;
        state.stage = ZrorStage::AwaitFb;
        return dzror_result(1, state);
    }
    state.x = x;
    loop {
        match state.stage {
            ZrorStage::Unset => panic!("dzror: dstzr/status=0 initialization required"),
            ZrorStage::AwaitFb => {
                state.fb = fx;
                state.xlo = state.xhi;
                state.a = state.xlo;
                state.x = state.xlo;
                state.stage = ZrorStage::AwaitFa;
                return dzror_result(1, state);
            }
            ZrorStage::AwaitFa => {
                if state.fb < 0.0 {
                    if fx < 0.0 {
                        state.qleft = fx < state.fb;
                        state.qhi = false;
                        return dzror_result(-1, state);
                    }
                } else if state.fb > 0.0 && fx > 0.0 {
                    state.qleft = fx > state.fb;
                    state.qhi = true;
                    return dzror_result(-1, state);
                }
                state.fa = fx;
                state.first = true;
                restart_zror(state);
                state.stage = ZrorStage::AwaitFbStep;
            }
            ZrorStage::AwaitFbStep => {
                if state.x == x {
                    state.fb = fx;
                    if state.fc * state.fb >= 0.0 {
                        restart_zror(state);
                    } else if state.w == state.mb {
                        state.ext = 0;
                    } else {
                        state.ext += 1;
                    }
                }
            }
        }
        if let Some(result) = refine_zror(state) {
            return result;
        }
    }
}

fn restart_zror(state: &mut DzrorState) {
    state.c = state.a;
    state.fc = state.fa;
    state.ext = 0;
}

// `p = fda*p` retains operand order from cligen.f:5574.
#[allow(clippy::assign_op_pattern)]
fn refine_zror(state: &mut DzrorState) -> Option<DzrorResult> {
    // Labels 80-240, cligen.f:5546-5621. No algebraic reassociation.
    if state.fc.abs() < state.fb.abs() {
        if state.c != state.a {
            state.d = state.a;
            state.fd = state.fa;
        }
        state.a = state.b;
        state.fa = state.fb;
        state.xlo = state.c;
        state.b = state.xlo;
        state.fb = state.fc;
        state.c = state.a;
        state.fc = state.fa;
    }
    let tol = 0.5 * state.abstol.max(state.reltol * state.xlo.abs());
    let m = (state.c + state.b) * 0.5;
    state.mb = m - state.b;
    if state.mb.abs() <= tol {
        state.xhi = state.c;
        let qrzero = (state.fc >= 0.0 && state.fb <= 0.0) || (state.fc < 0.0 && state.fb >= 0.0);
        return Some(dzror_result(if qrzero { 0 } else { -1 }, state));
    }
    let w = if state.ext > 3 {
        state.mb
    } else {
        let tol = if state.mb < 0.0 {
            -tol.abs()
        } else {
            tol.abs()
        };
        let mut p = (state.b - state.a) * state.fb;
        let mut q;
        if state.first {
            q = state.fa - state.fb;
            state.first = false;
        } else {
            let fdb = (state.fd - state.fb) / (state.d - state.b);
            let fda = (state.fd - state.fa) / (state.d - state.a);
            p = fda * p;
            q = fdb * state.fa - fda * state.fb;
        }
        if p < 0.0 {
            p = -p;
            q = -q;
        }
        if state.ext == 3 {
            p *= 2.0;
        }
        if p * 1.0 == 0.0 || p <= q * tol {
            tol
        } else if p < state.mb * q {
            p / q
        } else {
            state.mb
        }
    };
    state.w = w;
    state.d = state.a;
    state.fd = state.fa;
    state.a = state.b;
    state.fa = state.fb;
    state.b += w;
    state.xlo = state.b;
    state.x = state.xlo;
    state.stage = ZrorStage::AwaitFbStep;
    Some(dzror_result(1, state))
}

fn dinvr_result(status: i32, x: f64, state: &DinvrState) -> DinvrResult {
    DinvrResult {
        status,
        x,
        qleft: state.qleft,
        qhi: state.qhi,
    }
}

/// Bound and find a monotone-function zero with reverse communication —
/// faithful `dinvr` (`cligen.f:5070-5416`).
pub fn dinvr(
    status: i32,
    x: f64,
    fx: f64,
    state: &mut DinvrState,
    zero: &mut DzrorState,
) -> DinvrResult {
    if status <= 0 {
        assert!(
            state.small <= x && x <= state.big,
            "dinvr: SMALL, X, BIG not monotone"
        );
        state.xsave = x;
        state.stage = InvrStage::AwaitSmall;
        return dinvr_result(1, state.small, state);
    }
    match state.stage {
        InvrStage::Unset => panic!("dinvr: dstinv/status=0 initialization required"),
        InvrStage::AwaitSmall => {
            state.fsmall = fx;
            state.stage = InvrStage::AwaitBig;
            dinvr_result(1, state.big, state)
        }
        InvrStage::AwaitBig => dinvr_after_bounds(x, fx, state),
        InvrStage::AwaitInitial => dinvr_after_initial(x, fx, state),
        InvrStage::AwaitUpper => dinvr_after_upper(fx, state, zero),
        InvrStage::AwaitLower => dinvr_after_lower(fx, state, zero),
        InvrStage::InZero => {
            let zr = dzror(status, x, fx, zero);
            if zr.status == 1 {
                dinvr_result(1, zr.x, state)
            } else {
                // Source label 290 returns xlo/status=0 even if dzror
                // returned -1 (cligen.f:5302-5314).
                dinvr_result(0, zr.xlo, state)
            }
        }
    }
}

fn dinvr_after_bounds(x: f64, fx: f64, state: &mut DinvrState) -> DinvrResult {
    state.fbig = fx;
    state.qincr = state.fbig > state.fsmall;
    if state.qincr {
        if state.fsmall > 0.0 {
            state.qleft = true;
            state.qhi = true;
            return dinvr_result(-1, x, state);
        }
        if state.fbig < 0.0 {
            state.qleft = false;
            state.qhi = false;
            return dinvr_result(-1, x, state);
        }
    } else {
        if state.fsmall < 0.0 {
            state.qleft = true;
            state.qhi = false;
            return dinvr_result(-1, x, state);
        }
        if state.fbig > 0.0 {
            state.qleft = false;
            state.qhi = true;
            return dinvr_result(-1, x, state);
        }
    }
    state.step = state.absstp.max(state.relstp * state.xsave.abs());
    state.stage = InvrStage::AwaitInitial;
    dinvr_result(1, state.xsave, state)
}

fn dinvr_after_initial(x: f64, fx: f64, state: &mut DinvrState) -> DinvrResult {
    if fx == 0.0 {
        return dinvr_result(0, x, state);
    }
    let qup = (state.qincr && fx < 0.0) || (!state.qincr && fx > 0.0);
    if qup {
        state.xlb = state.xsave;
        state.xub = (state.xlb + state.step).min(state.big);
        state.stage = InvrStage::AwaitUpper;
        dinvr_result(1, state.xub, state)
    } else {
        state.xub = state.xsave;
        state.xlb = (state.xub - state.step).max(state.small);
        state.stage = InvrStage::AwaitLower;
        dinvr_result(1, state.xlb, state)
    }
}

// Step multiplication retains cligen.f:5245 operand order.
#[allow(clippy::assign_op_pattern)]
fn dinvr_after_upper(fx: f64, state: &mut DinvrState, zero: &mut DzrorState) -> DinvrResult {
    let qbdd = (state.qincr && fx >= 0.0) || (!state.qincr && fx <= 0.0);
    let qlim = state.xub >= state.big;
    if qbdd {
        start_invr_zero(state, zero);
        let zr = dzror(0, 0.0, 0.0, zero);
        dinvr_result(1, zr.x, state)
    } else if qlim {
        state.qleft = false;
        state.qhi = !state.qincr;
        dinvr_result(-1, state.big, state)
    } else {
        state.step = state.stpmul * state.step;
        state.xlb = state.xub;
        state.xub = (state.xlb + state.step).min(state.big);
        dinvr_result(1, state.xub, state)
    }
}

// Step multiplication retains cligen.f:5280 operand order.
#[allow(clippy::assign_op_pattern)]
fn dinvr_after_lower(fx: f64, state: &mut DinvrState, zero: &mut DzrorState) -> DinvrResult {
    let qbdd = (state.qincr && fx <= 0.0) || (!state.qincr && fx >= 0.0);
    let qlim = state.xlb <= state.small;
    if qbdd {
        start_invr_zero(state, zero);
        let zr = dzror(0, 0.0, 0.0, zero);
        dinvr_result(1, zr.x, state)
    } else if qlim {
        state.qleft = true;
        state.qhi = state.qincr;
        dinvr_result(-1, state.small, state)
    } else {
        state.step = state.stpmul * state.step;
        state.xub = state.xlb;
        state.xlb = (state.xub - state.step).max(state.small);
        dinvr_result(1, state.xlb, state)
    }
}

fn start_invr_zero(state: &mut DinvrState, zero: &mut DzrorState) {
    dstzr(state.xlb, state.xub, state.abstol, state.reltol, zero);
    state.stage = InvrStage::InZero;
}

/// Embedded integer machine constants (`cligen.f:6575-7002`).
pub fn ipmpar(i: i32) -> i32 {
    const IMACH: [i32; 10] = [2, 31, 2_147_483_647, 2, 24, -125, 128, 53, -1021, 1024];
    assert!((1..=10).contains(&i), "ipmpar: i outside 1..=10");
    IMACH[(i - 1) as usize]
}

/// Embedded binary64 machine constants (`cligen.f:7095-7165`).
pub fn spmpar(i: i32) -> f64 {
    assert!((1..=3).contains(&i), "spmpar: i outside 1..=3");
    if i == 1 {
        let b = ipmpar(4) as f64;
        return libm::pow(b, (1 - ipmpar(8)) as f64);
    }
    if i == 2 {
        let b = ipmpar(4) as f64;
        let binv = 1.0 / b;
        let w = libm::pow(b, (ipmpar(9) + 2) as f64);
        return ((w * binv) * binv) * binv;
    }
    let ibeta = ipmpar(4);
    let m = ipmpar(8);
    let emax = ipmpar(10);
    let b = ibeta as f64;
    let bm1 = (ibeta - 1) as f64;
    let z = libm::pow(b, (m - 1) as f64);
    let w = ((z - 1.0) * b + bm1) / (b * z);
    let z = libm::pow(b, (emax - 2) as f64);
    ((w * z) * b) * b
}

/// Safe exponential argument bound (`cligen.f:5890-5939`).
// Constants are the source literals at cligen.f:5918-5927.
#[allow(clippy::approx_constant)]
pub fn exparg(l: i32) -> f64 {
    let b = ipmpar(4);
    let lnb = match b {
        2 => 0.69314718055995,
        8 => 2.0794415416798,
        16 => 2.7725887222398,
        _ => libm::log(b as f64),
    };
    let m = if l == 0 { ipmpar(10) } else { ipmpar(9) - 1 };
    0.99999 * (m as f64 * lnb)
}

/// Accurate `exp(x)-1` approximation (`cligen.f:7005-7036`).
pub fn rexp(x: f64) -> f64 {
    const P1: f64 = 0.914041914819518e-9;
    const P2: f64 = 0.238082361044469e-1;
    const Q1: f64 = -0.499999999085958;
    const Q2: f64 = 0.107141568980644;
    const Q3: f64 = -0.119041179760821e-1;
    const Q4: f64 = 0.595130811860248e-3;
    if x.abs() <= 0.15 {
        return x * (((P2 * x + P1) * x + 1.0) / ((((Q4 * x + Q3) * x + Q2) * x + Q1) * x + 1.0));
    }
    let w = exp_pinned(x);
    if x > 0.0 {
        w * (0.5 + (0.5 - 1.0 / w))
    } else {
        (w - 0.5) - 0.5
    }
}

/// Accurate `x - 1 - ln(x)` approximation (`cligen.f:7039-7092`).
pub fn rlog(x: f64) -> f64 {
    const A: f64 = 0.566749439387324e-1;
    const B: f64 = 0.456512608815524e-1;
    const P0: f64 = 0.333333333333333;
    const P1: f64 = -0.224696413112536;
    const P2: f64 = 0.620886815375787e-2;
    const Q1: f64 = -0.127408923933623e1;
    const Q2: f64 = 0.354508718369557;
    if !(0.61..=1.57).contains(&x) {
        return ((x - 0.5) - 0.5) - libm::log(x);
    }
    let (u, w1) = if x < 0.82 {
        let u = (x - 0.7) / 0.7;
        (u, A - u * 0.3)
    } else if x > 1.18 {
        let u = 0.75 * x - 1.0;
        (u, B + u / 3.0)
    } else {
        ((x - 0.5) - 0.5, 0.0)
    };
    let r = u / (u + 2.0);
    let t = r * r;
    let w = ((P2 * t + P1) * t + P0) / ((Q2 * t + Q1) * t + 1.0);
    2.0 * t * (1.0 / (1.0 - r) - r * w) + w1
}

/// `1/gamma(a+1)-1` (`cligen.f:5942-6004`).
pub fn gam1(a: f64) -> f64 {
    const P: [f64; 7] = [
        0.577215664901533,
        -0.409078193005776,
        -0.230975380857675,
        0.597275330452234e-1,
        0.766968181649490e-2,
        -0.514889771323592e-2,
        0.589597428611429e-3,
    ];
    const Q: [f64; 5] = [
        1.0,
        0.427569613095214,
        0.158451672430138,
        0.261132021441447e-1,
        0.423244297896961e-2,
    ];
    const R: [f64; 9] = [
        -0.422784335098468,
        -0.771330383816272,
        -0.244757765222226,
        0.118378989872749,
        0.930357293360349e-3,
        -0.118290993445146e-1,
        0.223047661158249e-2,
        0.266505979058923e-3,
        -0.132674909766242e-3,
    ];
    const S1: f64 = 0.273076135303957;
    const S2: f64 = 0.559398236957378e-1;
    let d = a - 0.5;
    let t = if d > 0.0 { d - 0.5 } else { a };
    if t == 0.0 {
        return 0.0;
    }
    if t > 0.0 {
        let top =
            ((((((P[6] * t + P[5]) * t + P[4]) * t + P[3]) * t + P[2]) * t + P[1]) * t) + P[0];
        let bot = (((Q[4] * t + Q[3]) * t + Q[2]) * t + Q[1]) * t + 1.0;
        let w = top / bot;
        if d > 0.0 {
            (t / a) * ((w - 0.5) - 0.5)
        } else {
            a * w
        }
    } else {
        let top = (((((((R[8] * t + R[7]) * t + R[6]) * t + R[5]) * t + R[4]) * t + R[3]) * t
            + R[2])
            * t
            + R[1])
            * t
            + R[0];
        let bot = (S2 * t + S1) * t + 1.0;
        let w = top / bot;
        if d > 0.0 {
            t * w / a
        } else {
            a * ((w + 0.5) + 0.5)
        }
    }
}

/// Complete gamma function (`cligen.f:6007-6155`). Source failure paths
/// return the sentinel `0.0`, which is preserved.
// PI/D are copied verbatim from cligen.f:6045-6046; product assignments
// preserve source operand order at 6075/6088/6091.
#[allow(
    clippy::approx_constant,
    clippy::assign_op_pattern,
    clippy::excessive_precision
)]
pub fn gamma(a: f64) -> f64 {
    const PI: f64 = 3.1415926535898;
    const D: f64 = 0.41893853320467274178;
    const P: [f64; 7] = [
        0.539637273585445e-3,
        0.261939260042690e-2,
        0.204493667594920e-1,
        0.730981088720487e-1,
        0.279648642639792,
        0.553413866010467,
        1.0,
    ];
    const Q: [f64; 7] = [
        -0.832979206704073e-3,
        0.470059485860584e-2,
        0.225211131035340e-1,
        -0.170458969313360,
        -0.567902761974940e-1,
        0.113062953091122e1,
        1.0,
    ];
    const R1: f64 = 0.820756370353826e-3;
    const R2: f64 = -0.595156336428591e-3;
    const R3: f64 = 0.793650663183693e-3;
    const R4: f64 = -0.277777777770481e-2;
    const R5: f64 = 0.833333333333333e-1;
    let mut x = a;
    if a.abs() < 15.0 {
        let mut t = 1.0;
        let m = a as i32 - 1;
        if m > 0 {
            for _ in 1..=m {
                x -= 1.0;
                t = x * t;
            }
            x -= 1.0;
        } else if m == 0 {
            x -= 1.0;
        } else {
            t = a;
            if a <= 0.0 {
                let m = -m - 1;
                for _ in 1..=m {
                    x += 1.0;
                    t = x * t;
                }
                x = (x + 0.5) + 0.5;
                t = x * t;
                if t == 0.0 {
                    return 0.0;
                }
            }
            if t.abs() < 1e-30 {
                if t.abs() * spmpar(3) <= 1.0001 {
                    return 0.0;
                }
                return 1.0 / t;
            }
        }
        let mut top = P[0];
        let mut bot = Q[0];
        for i in 1..7 {
            top = P[i] + x * top;
            bot = Q[i] + x * bot;
        }
        let result = top / bot;
        return if a < 1.0 { result / t } else { result * t };
    }
    if a.abs() >= 1e3 {
        return 0.0;
    }
    let mut s = 0.0;
    if a <= 0.0 {
        x = -a;
        let n = x as i32;
        let mut t = x - n as f64;
        if t > 0.9 {
            t = 1.0 - t;
        }
        s = libm::sin(PI * t) / PI;
        if n % 2 == 0 {
            s = -s;
        }
        if s == 0.0 {
            return 0.0;
        }
    }
    let reciprocal = 1.0 / x;
    let t = reciprocal * reciprocal;
    let g = ((((R1 * t + R2) * t + R3) * t + R4) * t + R5) / x;
    let lnx = libm::log(x);
    let g = (D + g) + (x - 0.5) * (lnx - 1.0);
    let w = g;
    let t = g - w;
    if w > 0.99999 * exparg(0) {
        return 0.0;
    }
    let result = exp_pinned(w) * (1.0 + t);
    if a < 0.0 {
        (1.0 / (result * s)) / x
    } else {
        result
    }
}

const ERF_C: f64 = 0.564189583547756;
const ERF_A: [f64; 5] = [
    0.771058495001320e-4,
    -0.133733772997339e-2,
    0.323076579225834e-1,
    0.479137145607681e-1,
    0.128379167095513,
];
const ERF_B: [f64; 3] = [
    0.301048631703895e-2,
    0.538971687740286e-1,
    0.375795757275549,
];
const ERF_P: [f64; 8] = [
    -1.36864857382717e-7,
    5.64195517478974e-1,
    7.21175825088309,
    4.31622272220567e1,
    1.52989285046940e2,
    3.39320816734344e2,
    4.51918953711873e2,
    3.00459261020162e2,
];
const ERF_Q: [f64; 8] = [
    1.0,
    1.27827273196294e1,
    7.70001529352295e1,
    2.77585444743988e2,
    6.38980264465631e2,
    9.31354094850610e2,
    7.90950925327898e2,
    3.00459260956983e2,
];
const ERF_R: [f64; 5] = [
    2.10144126479064,
    2.62370141675169e1,
    2.13688200555087e1,
    4.65807828718470,
    2.82094791773523e-1,
];
const ERF_S: [f64; 4] = [
    9.41537750555460e1,
    1.87114811799590e2,
    9.90191814623914e1,
    1.80124575948747e1,
];

fn erf_rationals(ax: f64) -> (f64, f64) {
    let mut top = ERF_P[0];
    let mut bot = ERF_Q[0];
    for i in 1..8 {
        top = top * ax + ERF_P[i];
        bot = bot * ax + ERF_Q[i];
    }
    (top, bot)
}

/// Real error function (`cligen.f:5703-5775`).
pub fn erf(x: f64) -> f64 {
    let ax = x.abs();
    if ax <= 0.5 {
        let t = x * x;
        let top =
            ((((ERF_A[0] * t + ERF_A[1]) * t + ERF_A[2]) * t + ERF_A[3]) * t + ERF_A[4]) + 1.0;
        let bot = ((ERF_B[0] * t + ERF_B[1]) * t + ERF_B[2]) * t + 1.0;
        return x * (top / bot);
    }
    if ax <= 4.0 {
        let (top, bot) = erf_rationals(ax);
        let result = 0.5 + (0.5 - exp_pinned(-x * x) * top / bot);
        return if x < 0.0 { -result } else { result };
    }
    if ax < 5.8 {
        let x2 = x * x;
        let t = 1.0 / x2;
        let top = (((ERF_R[0] * t + ERF_R[1]) * t + ERF_R[2]) * t + ERF_R[3]) * t + ERF_R[4];
        let bot = (((ERF_S[0] * t + ERF_S[1]) * t + ERF_S[2]) * t + ERF_S[3]) * t + 1.0;
        let tail = (ERF_C - top / (x2 * bot)) / ax;
        let result = 0.5 + (0.5 - exp_pinned(-x2) * tail);
        return if x < 0.0 { -result } else { result };
    }
    if x < 0.0 {
        -1.0
    } else {
        1.0
    }
}

/// Complementary error function, optionally scaled by `exp(x*x)` —
/// faithful `erfc1` (`cligen.f:5778-5887`).
// Final assembly keeps `erfc1 = factor*erfc1` from cligen.f:5872.
#[allow(clippy::assign_op_pattern)]
pub fn erfc1(ind: i32, x: f64) -> f64 {
    let ax = x.abs();
    if ax <= 0.5 {
        let t = x * x;
        let top =
            ((((ERF_A[0] * t + ERF_A[1]) * t + ERF_A[2]) * t + ERF_A[3]) * t + ERF_A[4]) + 1.0;
        let bot = ((ERF_B[0] * t + ERF_B[1]) * t + ERF_B[2]) * t + 1.0;
        let result = 0.5 + (0.5 - x * (top / bot));
        return if ind == 0 {
            result
        } else {
            exp_pinned(t) * result
        };
    }
    let mut result;
    if ax <= 4.0 {
        let (top, bot) = erf_rationals(ax);
        result = top / bot;
    } else {
        if x <= -5.6 {
            return if ind == 0 {
                2.0
            } else {
                2.0 * exp_pinned(x * x)
            };
        }
        if ind == 0 && (x > 100.0 || x * x > -exparg(1)) {
            return 0.0;
        }
        let reciprocal = 1.0 / x;
        let t = reciprocal * reciprocal;
        let top = (((ERF_R[0] * t + ERF_R[1]) * t + ERF_R[2]) * t + ERF_R[3]) * t + ERF_R[4];
        let bot = (((ERF_S[0] * t + ERF_S[1]) * t + ERF_S[2]) * t + ERF_S[3]) * t + 1.0;
        result = (ERF_C - t * top / bot) / ax;
    }
    if ind != 0 {
        if x < 0.0 {
            result = 2.0 * exp_pinned(x * x) - result;
        }
        return result;
    }
    let w = x * x;
    let t = w;
    let e = w - t;
    result = ((0.5 + (0.5 - e)) * exp_pinned(-t)) * result;
    if x < 0.0 {
        2.0 - result
    } else {
        result
    }
}

#[derive(Debug, Clone, Copy)]
enum GratioAccuracy {
    Max,
    Digits6,
    Digits3,
}

impl GratioAccuracy {
    fn from_ind(ind: i32) -> Self {
        match ind {
            0 => Self::Max,
            1 => Self::Digits6,
            _ => Self::Digits3,
        }
    }

    fn constants(self) -> (f64, f64, f64, f64) {
        match self {
            Self::Max => (5e-15, 0.25e-3, 31.0, 20.0),
            Self::Digits6 => (5e-7, 0.25e-1, 17.0, 14.0),
            Self::Digits3 => (5e-4, 0.14, 9.7, 10.0),
        }
    }
}

/// Incomplete gamma ratio functions P(a,x), Q(a,x) — faithful `gratio`
/// (`cligen.f:6158-6572`). The `2.0` first-component sentinel is retained.
pub fn gratio(a: f64, x: f64, ind: i32) -> (f64, f64) {
    if a < 0.0 || x < 0.0 || (a == 0.0 && x == 0.0) {
        return (2.0, 0.0);
    }
    if a * x == 0.0 {
        return if x <= a { (0.0, 1.0) } else { (1.0, 0.0) };
    }
    gratio_core(a, x, GratioAccuracy::from_ind(ind))
}

// ALOG10 is the literal at cligen.f:6227, not Rust's full-precision LN_10.
#[allow(clippy::approx_constant)]
fn gratio_core(a: f64, x: f64, accuracy: GratioAccuracy) -> (f64, f64) {
    const ALOG10: f64 = 2.30258509299405;
    const RT2PIN: f64 = 0.398942280401433;
    let (acc0, e0, x0, big) = accuracy.constants();
    let e = spmpar(1);
    let acc = acc0.max(e);
    let r;
    if a < 1.0 {
        if a == 0.5 {
            let rtx = libm::sqrt(x);
            return if x < 0.25 {
                let ans = erf(rtx);
                (ans, 0.5 + (0.5 - ans))
            } else {
                let qans = erfc1(0, rtx);
                (0.5 + (0.5 - qans), qans)
            };
        }
        if x < 1.1 {
            return gratio_taylor_xa(a, x, acc);
        }
        let t1 = a * libm::log(x) - x;
        let u = a * exp_pinned(t1);
        if u == 0.0 {
            return (1.0, 0.0);
        }
        r = u * (1.0 + gam1(a));
        return gratio_continued_fraction(a, x, r, acc, e);
    }
    if a < big {
        if a <= x && x < x0 {
            let twoa = a + a;
            let m = twoa as i32;
            if twoa == m as f64 {
                let i = m / 2;
                return gratio_finite_q(x, i, a == i as f64);
            }
        }
        let t1 = a * libm::log(x) - x;
        r = exp_pinned(t1) / gamma(a);
    } else {
        let l = x / a;
        if l == 0.0 {
            return (0.0, 1.0);
        }
        let s = 0.5 + (0.5 - l);
        let z = rlog(l);
        if z >= 700.0 / a {
            if s.abs() <= 2.0 * e {
                return (2.0, 0.0);
            }
            return if x <= a { (0.0, 1.0) } else { (1.0, 0.0) };
        }
        let y = a * z;
        let rta = libm::sqrt(a);
        if s.abs() <= e0 / rta {
            return gratio_temme_l1(a, l, z, y, e, accuracy);
        }
        if s.abs() <= 0.4 {
            return gratio_temme_general(a, l, z, y, rta, e, accuracy);
        }
        let reciprocal = 1.0 / a;
        let t = reciprocal * reciprocal;
        let mut t1 = (((0.75 * t - 1.0) * t + 3.5) * t - 105.0) / (a * 1260.0);
        t1 -= y;
        r = RT2PIN * rta * exp_pinned(t1);
    }
    if r == 0.0 {
        return if x <= a { (0.0, 1.0) } else { (1.0, 0.0) };
    }
    if x <= a.max(ALOG10) {
        return gratio_taylor_r(a, x, r, acc);
    }
    if x < x0 {
        return gratio_continued_fraction(a, x, r, acc, e);
    }
    gratio_asymptotic_q(a, x, r, acc)
}

fn gratio_taylor_xa(a: f64, x: f64, acc: f64) -> (f64, f64) {
    let mut an = 3.0;
    let mut c = x;
    let mut sum = x / (a + 3.0);
    let tol = 3.0 * acc / (a + 1.0);
    loop {
        an += 1.0;
        c = -c * (x / an);
        let t = c / (a + an);
        sum += t;
        if t.abs() <= tol {
            break;
        }
    }
    let j = a * x * ((sum / 6.0 - 0.5 / (a + 2.0)) * x + 1.0 / (a + 1.0));
    let z = a * libm::log(x);
    let h = gam1(a);
    let g = 1.0 + h;
    let label_200 = if x < 0.25 { z > -0.13394 } else { a < x / 2.59 };
    if label_200 {
        let l = rexp(z);
        let w = 0.5 + (0.5 + l);
        let qans = (w * j - l) * g - h;
        if qans < 0.0 {
            return (1.0, 0.0);
        }
        (0.5 + (0.5 - qans), qans)
    } else {
        let w = exp_pinned(z);
        let ans = w * g * (0.5 + (0.5 - j));
        (ans, 0.5 + (0.5 - ans))
    }
}

// Source-shaped recurrence assignments, cligen.f:6336/6345.
#[allow(clippy::assign_op_pattern)]
fn gratio_taylor_r(a: f64, x: f64, r: f64, acc: f64) -> (f64, f64) {
    let mut wk = [0.0; 20];
    let mut apn = a + 1.0;
    let mut t = x / apn;
    wk[0] = t;
    let mut n = 20usize;
    for source_n in 2..=20 {
        apn += 1.0;
        t = t * (x / apn);
        if t <= 1e-3 {
            n = source_n;
            break;
        }
        wk[source_n - 1] = t;
    }
    let mut sum = t;
    let tol = 0.5 * acc;
    loop {
        apn += 1.0;
        t = t * (x / apn);
        sum += t;
        if t <= tol {
            break;
        }
    }
    for index in (0..n - 1).rev() {
        sum += wk[index];
    }
    let ans = (r / a) * (1.0 + sum);
    (ans, 0.5 + (0.5 - ans))
}

fn gratio_continued_fraction(a: f64, x: f64, r: f64, acc: f64, e: f64) -> (f64, f64) {
    let tol = (5.0 * e).max(acc);
    let mut a2nm1 = 1.0;
    let mut a2n = 1.0;
    let mut b2nm1 = x;
    let mut b2n = x + (1.0 - a);
    let mut c = 1.0;
    loop {
        a2nm1 = x * a2n + c * a2nm1;
        b2nm1 = x * b2n + c * b2nm1;
        let am0 = a2nm1 / b2nm1;
        c += 1.0;
        let cma = c - a;
        a2n = a2nm1 + cma * a2n;
        b2n = b2nm1 + cma * b2n;
        let an0 = a2n / b2n;
        if (an0 - am0).abs() < tol * an0 {
            let qans = r * an0;
            return (0.5 + (0.5 - qans), qans);
        }
    }
}

// Source-shaped recurrence assignments, cligen.f:6365/6374.
#[allow(clippy::assign_op_pattern)]
fn gratio_asymptotic_q(a: f64, x: f64, r: f64, acc: f64) -> (f64, f64) {
    let mut wk = [0.0; 20];
    let mut amn = a - 1.0;
    let mut t = amn / x;
    wk[0] = t;
    let mut n = 20usize;
    for source_n in 2..=20 {
        amn -= 1.0;
        t = t * (amn / x);
        if t.abs() <= 1e-3 {
            n = source_n;
            break;
        }
        wk[source_n - 1] = t;
    }
    let mut sum = t;
    while t.abs() > acc {
        amn -= 1.0;
        t = t * (amn / x);
        sum += t;
    }
    for index in (0..n - 1).rev() {
        sum += wk[index];
    }
    let qans = (r / x) * (1.0 + sum);
    (0.5 + (0.5 - qans), qans)
}

fn gratio_finite_q(x: f64, i: i32, a_is_integer: bool) -> (f64, f64) {
    let (mut sum, mut t, mut n, mut c) = if a_is_integer {
        let sum = exp_pinned(-x);
        (sum, sum, 1, 0.0)
    } else {
        let rtx = libm::sqrt(x);
        (
            erfc1(0, rtx),
            exp_pinned(-x) / (1.77245385090552 * rtx),
            0,
            -0.5,
        )
    };
    while n != i {
        n += 1;
        c += 1.0;
        t = (x * t) / c;
        sum += t;
    }
    (0.5 + (0.5 - sum), sum)
}

const GD0: [f64; 13] = [
    0.833333333333333e-1,
    -0.148148148148148e-1,
    0.115740740740741e-2,
    0.352733686067019e-3,
    -0.178755144032922e-3,
    0.391926317852244e-4,
    -0.218544851067999e-5,
    -0.185406221071516e-5,
    0.829671134095309e-6,
    -0.176659527368261e-6,
    0.670785354340150e-8,
    0.102618097842403e-7,
    -0.438203601845335e-8,
];
const GD1: [f64; 12] = [
    -0.347222222222222e-2,
    0.264550264550265e-2,
    -0.990226337448560e-3,
    0.205761316872428e-3,
    -0.401877572016461e-6,
    -0.180985503344900e-4,
    0.764916091608111e-5,
    -0.161209008945634e-5,
    0.464712780280743e-8,
    0.137863344691572e-6,
    -0.575254560351770e-7,
    0.119516285997781e-7,
];
const GD2: [f64; 10] = [
    -0.268132716049383e-2,
    0.771604938271605e-3,
    0.200938786008230e-5,
    -0.107366532263652e-3,
    0.529234488291201e-4,
    -0.127606351886187e-4,
    0.342357873409614e-7,
    0.137219573090629e-5,
    -0.629899213838006e-6,
    0.142806142060642e-6,
];
const GD3: [f64; 8] = [
    0.229472093621399e-3,
    -0.469189494395256e-3,
    0.267720632062839e-3,
    -0.756180167188398e-4,
    -0.239650511386730e-6,
    0.110826541153473e-4,
    -0.567495282699160e-5,
    0.142309007324359e-5,
];
const GD4: [f64; 6] = [
    0.784039221720067e-3,
    -0.299072480303190e-3,
    -0.146384525788434e-5,
    0.664149821546512e-4,
    -0.396836504717943e-4,
    0.113757269706784e-4,
];
const GD5: [f64; 4] = [
    -0.697281375836586e-4,
    0.277275324495939e-3,
    -0.199325705161888e-3,
    0.679778047793721e-4,
];
const GD6: [f64; 2] = [-0.592166437353694e-3, 0.270878209671804e-3];
const GD10: f64 = -0.185185185185185e-2;
const GD20: f64 = 0.413359788359788e-2;
const GD30: f64 = 0.649434156378601e-3;
const GD40: f64 = -0.861888290916712e-3;
const GD50: f64 = -0.336798553366358e-3;
const GD60: f64 = 0.531307936463992e-3;
const GD70: f64 = 0.344367606892378e-3;

fn horner(coefficients: &[f64], x: f64) -> f64 {
    let mut value = *coefficients.last().expect("nonempty coefficient table");
    for coefficient in coefficients[..coefficients.len() - 1].iter().rev() {
        value = value * x + coefficient;
    }
    value
}

fn temme_polynomial(z: f64, u: f64, accuracy: GratioAccuracy, close: bool) -> f64 {
    const THIRD: f64 = 0.333333333333333;
    let (c0, c1, c2, c3, c4, c5, c6) = match (accuracy, close) {
        (GratioAccuracy::Max, true) => (
            horner(&GD0[..7], z) * z - THIRD,
            horner(&GD1[..6], z) * z + GD10,
            horner(&GD2[..5], z) * z + GD20,
            horner(&GD3[..4], z) * z + GD30,
            horner(&GD4[..2], z) * z + GD40,
            horner(&GD5[..2], z) * z + GD50,
            GD6[0] * z + GD60,
        ),
        (GratioAccuracy::Max, false) => (
            horner(&GD0, z) * z - THIRD,
            horner(&GD1, z) * z + GD10,
            horner(&GD2, z) * z + GD20,
            horner(&GD3, z) * z + GD30,
            horner(&GD4, z) * z + GD40,
            horner(&GD5, z) * z + GD50,
            horner(&GD6, z) * z + GD60,
        ),
        (GratioAccuracy::Digits6, _) => (
            horner(&GD0[..6], z) * z - THIRD,
            horner(&GD1[..4], z) * z + GD10,
            GD2[0] * z + GD20,
            0.0,
            0.0,
            0.0,
            0.0,
        ),
        (GratioAccuracy::Digits3, _) => (
            horner(&GD0[..3], z) * z - THIRD,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ),
    };
    match accuracy {
        GratioAccuracy::Max => {
            ((((((GD70 * u + c6) * u + c5) * u + c4) * u + c3) * u + c2) * u + c1) * u + c0
        }
        GratioAccuracy::Digits6 => (c2 * u + c1) * u + c0,
        GratioAccuracy::Digits3 => c0,
    }
}

fn gratio_temme_general(
    a: f64,
    l: f64,
    z_in: f64,
    y: f64,
    rta: f64,
    e: f64,
    accuracy: GratioAccuracy,
) -> (f64, f64) {
    const RT2PIN: f64 = 0.398942280401433;
    let s = 0.5 + (0.5 - l);
    if s.abs() <= 2.0 * e && a * e * e > 3.28e-3 {
        return (2.0, 0.0);
    }
    let c = exp_pinned(-y);
    let w = 0.5 * erfc1(1, libm::sqrt(y));
    let u = 1.0 / a;
    let mut z = libm::sqrt(z_in + z_in);
    if l < 1.0 {
        z = -z;
    }
    let t = temme_polynomial(z, u, accuracy, s.abs() <= 1e-3);
    if l < 1.0 {
        let ans = c * (w - RT2PIN * t / rta);
        (ans, 0.5 + (0.5 - ans))
    } else {
        let qans = c * (w + RT2PIN * t / rta);
        (0.5 + (0.5 - qans), qans)
    }
}

fn gratio_temme_l1(
    a: f64,
    l: f64,
    z_in: f64,
    y: f64,
    e: f64,
    accuracy: GratioAccuracy,
) -> (f64, f64) {
    const RT2PIN: f64 = 0.398942280401433;
    const RTPI: f64 = 1.77245385090552;
    if a * e * e > 3.28e-3 {
        return (2.0, 0.0);
    }
    let c = 0.5 + (0.5 - y);
    let w = (0.5 - libm::sqrt(y) * (0.5 + (0.5 - y / 3.0)) / RTPI) / c;
    let u = 1.0 / a;
    let mut z = libm::sqrt(z_in + z_in);
    if l < 1.0 {
        z = -z;
    }
    let t = match accuracy {
        GratioAccuracy::Max => {
            let c0 = horner(&GD0[..7], z) * z - 0.333333333333333;
            let c1 = horner(&GD1[..6], z) * z + GD10;
            let c2 = horner(&GD2[..5], z) * z + GD20;
            let c3 = horner(&GD3[..4], z) * z + GD30;
            let c4 = horner(&GD4[..2], z) * z + GD40;
            let c5 = horner(&GD5[..2], z) * z + GD50;
            let c6 = GD6[0] * z + GD60;
            ((((((GD70 * u + c6) * u + c5) * u + c4) * u + c3) * u + c2) * u + c1) * u + c0
        }
        GratioAccuracy::Digits6 => {
            let c0 = (GD0[1] * z + GD0[0]) * z - 0.333333333333333;
            let c1 = GD1[0] * z + GD10;
            (GD20 * u + c1) * u + c0
        }
        GratioAccuracy::Digits3 => GD0[0] * z - 0.333333333333333,
    };
    let rta = libm::sqrt(a);
    if l < 1.0 {
        let ans = c * (w - RT2PIN * t / rta);
        (ans, 0.5 + (0.5 - ans))
    } else {
        let qans = c * (w + RT2PIN * t / rta);
        (0.5 + (0.5 - qans), qans)
    }
}

/// Cumulative incomplete gamma (`cligen.f:5008-5067`).
pub fn cumgam(x: f64, a: f64) -> (f64, f64) {
    if x <= 0.0 {
        (0.0, 1.0)
    } else {
        gratio(a, x, 0)
    }
}

/// Cumulative chi-square distribution (`cligen.f:4954-5005`).
pub fn cumchi(x: f64, df: f64) -> (f64, f64) {
    cumgam(x * 0.5, df * 0.5)
}

/// Chi-square CDF dispatcher/inverter (`cligen.f:4705-4951`).
pub fn cdfchi(which: i32, p: f64, q: f64, x: f64, df: f64, state: &mut AcmState) -> CdfChiResult {
    const TOL: f64 = 1e-8;
    const ATOL: f64 = 1e-50;
    const ZERO: f64 = 1e-100;
    const INF: f64 = 1e100;
    if let Some(invalid) = validate_cdfchi(which, p, q, x, df) {
        return invalid;
    }
    let mut result = CdfChiResult {
        p,
        q,
        x,
        df,
        status: 0,
        bound: 0.0,
    };
    if which == 1 {
        (result.p, result.q) = cumchi(x, df);
        if result.p > 1.5 {
            result.status = 10;
        }
        return result;
    }
    let qporq = p <= q;
    let porq = if qporq { p } else { q };
    let (small, mut value) = if which == 2 { (0.0, 5.0) } else { (ZERO, 5.0) };
    dstinv(small, INF, 0.5, 0.5, 5.0, ATOL, TOL, &mut state.dinvr);
    let mut status = 0;
    let mut fx = 0.0;
    loop {
        let step = dinvr(status, value, fx, &mut state.dinvr, &mut state.dzror);
        status = step.status;
        value = step.x;
        if status != 1 {
            break;
        }
        let (cum, ccum) = if which == 2 {
            cumchi(value, df)
        } else {
            cumchi(x, value)
        };
        fx = if qporq { cum - p } else { ccum - q };
        if fx + porq > 1.5 {
            result.status = 10;
            return result;
        }
    }
    if which == 2 {
        result.x = value;
    } else {
        result.df = value;
    }
    result.status = status;
    if status == -1 {
        if state.dinvr.qleft {
            result.status = 1;
            result.bound = small;
        } else {
            result.status = 2;
            result.bound = INF;
        }
    }
    result
}

// Argument checks preserve the source's ordered labels 10--150
// (`cligen.f:4815-4879`).  Keeping this source block separate also keeps
// the reverse-communication dispatcher below the package complexity cap.
fn validate_cdfchi(which: i32, p: f64, q: f64, x: f64, df: f64) -> Option<CdfChiResult> {
    let mut result = CdfChiResult {
        p,
        q,
        x,
        df,
        status: 0,
        bound: 0.0,
    };
    if !(1..=3).contains(&which) {
        result.bound = if which < 1 { 1.0 } else { 3.0 };
        result.status = -1;
        return Some(result);
    }
    if which != 1 && !(0.0..=1.0).contains(&p) {
        result.bound = if p < 0.0 { 0.0 } else { 1.0 };
        result.status = -2;
        return Some(result);
    }
    if which != 1 && (q <= 0.0 || q > 1.0) {
        result.bound = if q <= 0.0 { 0.0 } else { 1.0 };
        result.status = -3;
        return Some(result);
    }
    if which != 2 && x < 0.0 {
        result.bound = 0.0;
        result.status = -4;
        return Some(result);
    }
    if which != 3 && df <= 0.0 {
        result.bound = 0.0;
        result.status = -5;
        return Some(result);
    }
    if which != 1 {
        let pq = p + q;
        if (((pq - 0.5) - 0.5).abs()) > 3.0 * spmpar(1) {
            result.bound = if pq < 0.0 { 0.0 } else { 1.0 };
            result.status = 3;
            return Some(result);
        }
    }
    None
}
