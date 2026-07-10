//! Faithful-mode bit-identity for the storm package: the day loop
//! replayed with the duration/Ipeak chain in source order
//! (clgen → wet_day_duration → storm_block), asserting the sd/tp tap
//! streams (fixtures/taps/storm/, storm tap-schema.md).
//!
//! Relative to the item-5 cg replay protocol, `k7` (alphb's dstg
//! draws) and `k10` (timepk's observed-mode draws) are **internal**
//! here — every one of the ten seed streams is asserted per record.
//! `windg` is deliberately not driven: nothing in the chain consumes
//! its outputs, and its `v9` rolling pair stays a per-record external
//! input exactly as in the cg replay.

use cligen::acm::AcmState;
use cligen::cbk1::Cbk1State;
use cligen::cbk3::Cbk3State;
use cligen::cbk4::Cbk4State;
use cligen::cbk5::Cbk5State;
use cligen::cbk7::Cbk7State;
use cligen::cinterp::CinterpState;
use cligen::crandom3::Crandom3State;
use cligen::daily::clgen;
use cligen::deviates::DstgState;
use cligen::libm_pinned::{cosf_pinned, sinf_pinned};
use cligen::monthlies::lintrp;
use cligen::par::{sta_parms, ParFile};
use cligen::rng::{RansetState, SeedState};
use cligen::storm::{storm_block, wet_day_duration, SingleStormParams};
use std::path::{Path, PathBuf};

/// (tap case dir, .par path, interp, iopt). Single-storm parameters
/// for the iopt-4 case come from the golden harness's
/// `single-storm.inp` (damt 2.25, usdur 6.0, ustpr 0.4, uxmav 1.5).
const CASES: [(&str, &str, i32, i32); 10] = [
    ("new-meadows-id-seed0", "new-meadows-id/id106388.par", 0, 5),
    ("new-meadows-id-seed17", "new-meadows-id/id106388.par", 0, 5),
    ("jeogla-au-seed0", "jeogla-au/ASN00057011.par", 0, 5),
    (
        "mt-wilson-ca-observed-seed0",
        "mt-wilson-ca/ca046006.par",
        2,
        6,
    ),
    (
        "fish-springs-ut-observed-padded-seed0",
        "fish-springs-ut/ut422852.par",
        2,
        6,
    ),
    (
        "fish-springs-ut-observed-truncated-seed0",
        "fish-springs-ut/ut422852.par",
        2,
        6,
    ),
    (
        "new-meadows-id-single-storm-seed0",
        "new-meadows-id/id106388.par",
        0,
        4,
    ),
    ("new-meadows-id-I1", "new-meadows-id/id106388.par", 1, 5),
    ("new-meadows-id-I3", "new-meadows-id/id106388.par", 3, 5),
    (
        "mt-wilson-ca-observed-I3",
        "mt-wilson-ca/ca046006.par",
        3,
        6,
    ),
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn hex(field: &str) -> u32 {
    u32::from_str_radix(field, 16).unwrap()
}

struct CgRec {
    mo: i32,
    ida: i32,
    ntd: i32,
    iyear: i32,
    nsim: i32,
    msim: i32,
    l: i32,
    mox: i32,
    dax: i32,
    seeds: [[i32; 4]; 10],
    v: [u32; 6],
    tmxg_in: u32,
    tmng_in: u32,
    out: [u32; 6],
}

fn parse_cg(path: &Path) -> Vec<CgRec> {
    let data = std::fs::read_to_string(path).unwrap();
    let lines: Vec<Vec<&str>> = data
        .lines()
        .map(|l| l.split_whitespace().collect())
        .collect();
    assert_eq!(lines.len() % 5, 0, "{}: partial cg record", path.display());
    lines
        .chunks_exact(5)
        .map(|c| {
            let (b, k, v, a) = (&c[0], &c[1], &c[2], &c[4]);
            let ki: Vec<i32> = k[1..41].iter().map(|s| s.parse().unwrap()).collect();
            CgRec {
                mo: b[1].parse().unwrap(),
                ida: b[2].parse().unwrap(),
                ntd: b[3].parse().unwrap(),
                iyear: b[4].parse().unwrap(),
                nsim: b[5].parse().unwrap(),
                msim: b[6].parse().unwrap(),
                l: b[7].parse().unwrap(),
                mox: b[8].parse().unwrap(),
                dax: b[9].parse().unwrap(),
                seeds: std::array::from_fn(|s| std::array::from_fn(|w| ki[s * 4 + w])),
                v: std::array::from_fn(|i| hex(v[i + 1])),
                tmxg_in: hex(v[7]),
                tmng_in: hex(v[8]),
                out: std::array::from_fn(|i| hex(a[i + 1])),
            }
        })
        .collect()
}

struct SdRec {
    dur: u32,
    r1: u32,
    jd: i32,
    mo: i32,
    iyear: i32,
    s: [u32; 4], // xr dur tpr xmav
}

fn parse_sd(path: &Path) -> Vec<SdRec> {
    let data = std::fs::read_to_string(path).unwrap();
    let lines: Vec<Vec<&str>> = data
        .lines()
        .map(|l| l.split_whitespace().collect())
        .collect();
    assert_eq!(lines.len() % 2, 0, "{}: partial sd record", path.display());
    lines
        .chunks_exact(2)
        .map(|c| {
            let (d, s) = (&c[0], &c[1]);
            assert_eq!((d[0], s[0]), ("D", "S"));
            SdRec {
                dur: hex(d[1]),
                r1: hex(d[2]),
                jd: s[1].parse().unwrap(),
                mo: s[2].parse().unwrap(),
                iyear: s[3].parse().unwrap(),
                s: std::array::from_fn(|i| hex(s[i + 4])),
            }
        })
        .collect()
}

struct TpRec {
    iopt: i32,
    dax: i32,
    k10: [i32; 4],
    z: u32,
    result: u32,
}

fn parse_tp(path: &Path) -> Vec<TpRec> {
    let data = std::fs::read_to_string(path).unwrap();
    data.lines()
        .map(|l| {
            let f: Vec<&str> = l.split_whitespace().collect();
            assert_eq!(f[0], "T");
            TpRec {
                iopt: f[1].parse().unwrap(),
                dax: f[2].parse().unwrap(),
                k10: std::array::from_fn(|i| f[i + 3].parse().unwrap()),
                z: hex(f[7]),
                result: hex(f[8]),
            }
        })
        .collect()
}

struct Replay {
    bk1: Cbk1State,
    bk3: Cbk3State,
    bk4: Cbk4State,
    bk5: Cbk5State,
    bk7: Cbk7State,
    bk9: cligen::cbk9::Cbk9State,
    ci: CinterpState,
    cr: Crandom3State,
    rs: RansetState,
    acm: AcmState,
    dg: DstgState,
    timpkd: [f32; 13],
    itype: i32,
}

/// Station + main-program setup, plus `r5monb` (main:878 order: the
/// chain's `alphb` calls read the converted `wi`).
fn setup(par_rel: &str, interp: i32, iopt: i32) -> Replay {
    let root = repo_root();
    let bytes = std::fs::read(root.join("fixtures").join(par_rel)).unwrap();
    let par = ParFile::parse(&bytes).unwrap();
    let mut bk1 = Cbk1State::default();
    let mut bk7 = Cbk7State::default();
    let mut bk9 = cligen::cbk9::Cbk9State::default();
    let mut ci = CinterpState {
        interp,
        ..CinterpState::default()
    };
    let out = sta_parms(&par, &mut bk7, &mut bk1, &mut bk9, &mut ci);
    let clt = 57.296f32;
    let xx = out.ylt / clt;
    bk7.yls = sinf_pinned(xx);
    bk7.ylc = cosf_pinned(xx);
    bk7.pit = 58.13;
    let bk4 = Cbk4State {
        iopt,
        ..Cbk4State::default()
    };
    cligen::daily::r5monb(&bk4, &bk7, &mut bk9);
    Replay {
        bk1,
        bk3: Cbk3State::default(),
        bk4,
        bk5: Cbk5State::default(),
        bk7,
        bk9,
        ci,
        cr: Crandom3State::default(),
        rs: RansetState::default(),
        acm: AcmState::default(),
        dg: DstgState::default(),
        timpkd: out.timpkd,
        itype: out.itype,
    }
}

fn seed_matrix(bk7: &Cbk7State) -> [[i32; 4]; 10] {
    [
        bk7.k1.0, bk7.k2.0, bk7.k3.0, bk7.k4.0, bk7.k5.0, bk7.k6.0, bk7.k7.0, bk7.k8.0, bk7.k9.0,
        bk7.k10.0,
    ]
}

fn single_storm_params(iopt: i32) -> SingleStormParams {
    if iopt == 4 {
        // golden harness single-storm.inp: 2.25 / 6.0 / 0.4 / 1.5
        SingleStormParams {
            damt: 2.25,
            usdur: 6.0,
            ustpr: 0.4,
            uxmav: 1.5,
        }
    } else {
        SingleStormParams::default()
    }
}

/// Committed-sample gate: the storm chain replayed over the 10 cases'
/// 500-day prefixes (sd/tp samples pair with the daily cg samples).
#[test]
fn storm_chain_replays_fortran_samples() {
    let root = repo_root();
    let mut days = 0;
    let mut tps = 0;
    for (case, par_rel, interp, iopt) in CASES {
        // Committed prefixes: cg from the daily package, sd/tp here.
        let daily = root.join("fixtures/taps/daily").join(case);
        let storm = root.join("fixtures/taps/storm").join(case);
        let cg = parse_cg(&daily.join("cg-sample.tap"));
        let sd = parse_sd(&storm.join("sd-sample.tap"));
        let tp_path = storm.join("tp-sample.tap");
        let tp = if tp_path.exists() {
            parse_tp(&tp_path)
        } else {
            Vec::new()
        };
        let (d, t) = replay_storm_parsed(case, par_rel, interp, iopt, cg, sd, tp, true);
        days += d;
        tps += t;
    }
    assert!(days >= 4_000, "expected substantial coverage, got {days}");
    assert!(tps > 500, "expected timepk coverage, got {tps}");
}

#[test]
#[ignore = "full storm replay against local tap-runs captures (evidence gate)"]
fn full_storm_streams_bit_identical() {
    let root = repo_root();
    let daily_runs = root.join("docs/work-packages/20260709-daily-core-port/artifacts/tap-runs");
    let storm_runs =
        root.join("docs/work-packages/20260709-storm-machinery-port/artifacts/tap-runs");
    let mut days = 0;
    let mut tps = 0;
    for (case, par_rel, interp, iopt) in CASES {
        let cg = parse_cg(&daily_runs.join(case).join("cligen_cg.tap"));
        let sd = parse_sd(&storm_runs.join(case).join("cligen_sd.tap"));
        let tp = parse_tp(&storm_runs.join(case).join("cligen_tp.tap"));
        let (d, t) = replay_storm_parsed(case, par_rel, interp, iopt, cg, sd, tp, false);
        days += d;
        tps += t;
    }
    println!("full storm replay: days={days} timepk={tps}");
    assert!(days > 80_000);
}

#[allow(clippy::too_many_arguments)]
fn replay_storm_parsed(
    case: &str,
    par_rel: &str,
    interp: i32,
    iopt: i32,
    cg: Vec<CgRec>,
    sd: Vec<SdRec>,
    tp: Vec<TpRec>,
    truncate_to_shortest: bool,
) -> (usize, usize) {
    // The committed cg/sd samples are prefix cuts of different lengths
    // (2500-line cg = 500 days; 1000-line sd = 500 days) — align on
    // the shortest when running the sample gate.
    let n = if truncate_to_shortest {
        cg.len().min(sd.len())
    } else {
        assert_eq!(cg.len(), sd.len(), "{case}: cg/sd day counts differ");
        cg.len()
    };
    if n == 0 {
        return (0, 0);
    }
    let mut st = setup(par_rel, interp, iopt);
    let ss = single_storm_params(iopt);
    let first = &cg[0];
    let s = first.seeds;
    st.bk7.k1 = SeedState(s[0]);
    st.bk7.k2 = SeedState(s[1]);
    st.bk7.k3 = SeedState(s[2]);
    st.bk7.k4 = SeedState(s[3]);
    st.bk7.k5 = SeedState(s[4]);
    st.bk7.k6 = SeedState(s[5]);
    st.bk7.k7 = SeedState(s[6]);
    st.bk7.k8 = SeedState(s[7]);
    st.bk7.k9 = SeedState(s[8]);
    st.bk7.k10 = SeedState(s[9]);
    st.bk7.v1 = f32::from_bits(first.v[0]);
    st.bk7.v3 = f32::from_bits(first.v[1]);
    st.bk7.v5 = f32::from_bits(first.v[2]);
    st.bk7.v7 = f32::from_bits(first.v[3]);
    st.bk7.v11 = f32::from_bits(first.v[5]);
    st.bk7.l = first.l;
    st.cr.mox = first.mox;
    st.cr.dax = first.dax;

    let mut tp_idx = 0usize;
    for idx in 0..n {
        let rec = &cg[idx];
        let sd_rec = &sd[idx];
        let at = |what: &str| format!("{case}:{}: {what}", idx + 1);
        let sm = seed_matrix(&st.bk7);
        for (si, got) in sm.iter().enumerate() {
            assert_eq!(*got, rec.seeds[si], "{}", at(&format!("seed k{}", si + 1)));
        }
        st.bk7.v9 = f32::from_bits(rec.v[4]);
        st.bk7.tmxg = f32::from_bits(rec.tmxg_in);
        st.bk7.tmng = f32::from_bits(rec.tmng_in);
        st.bk4.mo = rec.mo;
        st.bk3.ida = rec.ida;
        st.bk7.nsim = rec.nsim;
        st.bk7.msim = rec.msim;
        if rec.nsim == 0 {
            st.bk5.r[(rec.ida - 1) as usize] = f32::from_bits(rec.out[0]);
        }
        if st.ci.interp == 1 {
            let jd = if rec.mo != rec.mox { 1 } else { rec.dax + 1 };
            lintrp(rec.mo, jd, rec.ntd, &mut st.ci);
        }
        let _ = clgen(
            rec.ntd,
            rec.iyear,
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
        // day_gen:3110-3112 converts the generated temps F -> C in
        // place before the storm block; the chain's mean-temp floor
        // reads Celsius.
        st.bk7.tmxg = (st.bk7.tmxg - 32.0) * (5.0 / 9.0);
        st.bk7.tmng = (st.bk7.tmng - 32.0) * (5.0 / 9.0);
        st.bk1.tdp = (st.bk1.tdp - 32.0) * (5.0 / 9.0);
        let wet = st.bk5.r[(rec.ida - 1) as usize] > 0.0;
        let dur = wet_day_duration(
            &st.bk3,
            &st.bk4,
            &mut st.bk5,
            &mut st.bk7,
            &mut st.bk9,
            &mut st.dg,
            &mut st.cr,
        );
        assert_eq!(dur.to_bits(), sd_rec.dur, "{}", at("dur (D record)"));
        if wet {
            assert_eq!(st.bk9.r1.to_bits(), sd_rec.r1, "{}", at("r1 (D record)"));
        }
        assert_eq!(
            (sd_rec.mo, sd_rec.iyear),
            (rec.mo, rec.iyear),
            "{}",
            at("S record day key")
        );
        if iopt != 4 {
            // Daily modes advance dax with the day of month; the
            // single-storm mode jumps to the storm date (jd = 15 with
            // one clgen call, dax = 1).
            assert_eq!(sd_rec.jd, st.cr.dax, "{}", at("S record jd"));
        }
        let q = storm_block(
            dur,
            &st.timpkd,
            st.itype,
            &ss,
            &st.bk3,
            &st.bk4,
            &mut st.bk5,
            &mut st.bk7,
            &mut st.bk9,
            &mut st.dg,
            &mut st.cr,
        );
        assert_eq!(q.xr.to_bits(), sd_rec.s[0], "{}", at("xr"));
        assert_eq!(q.dur.to_bits(), sd_rec.s[1], "{}", at("dur (S record)"));
        assert_eq!(q.tpr.to_bits(), sd_rec.s[2], "{}", at("tpr"));
        assert_eq!(q.xmav.to_bits(), sd_rec.s[3], "{}", at("xmav"));
        if wet && tp_idx < tp.len() {
            let t = &tp[tp_idx];
            assert_eq!(t.iopt, iopt, "{}", at("tp iopt"));
            assert_eq!(t.dax, st.cr.dax, "{}", at("tp dax"));
            // The T record captures k10 at timepk EXIT (the tap writes
            // before return): post-draw for iopt = 6, unchanged for the
            // batch path. storm_block's own timepk call is the only
            // k10 site between here and the record.
            assert_eq!(t.k10, st.bk7.k10.0, "{}", at("tp k10"));
            assert_eq!(st.cr.z.to_bits(), t.z, "{}", at("tp z"));
            let recomputed = timepk_result_check(&st, t);
            assert_eq!(recomputed, t.result, "{}", at("tp result"));
            tp_idx += 1;
        }
    }
    if !truncate_to_shortest {
        assert_eq!(tp_idx, tp.len(), "{case}: unconsumed timepk records");
    }
    (n, tp_idx)
}

/// Re-evaluate the pure interpolation part of `timepk` from the
/// captured `z` (a per-record vector check on top of the in-loop
/// consumption).
fn timepk_result_check(st: &Replay, t: &TpRec) -> u32 {
    let z = f32::from_bits(t.z);
    let mut i = 0usize;
    loop {
        i += 1;
        if !(st.timpkd[i] < z && i < 12) {
            break;
        }
    }
    let diff1 = st.timpkd[i] - z;
    let diff2 = st.timpkd[i] - st.timpkd[i - 1];
    let ratio = diff1 / diff2;
    (0.08333f32 * (i as f32) - ratio * 0.08333).to_bits()
}
