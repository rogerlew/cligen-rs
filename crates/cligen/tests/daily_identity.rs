//! Faithful-mode bit-identity for the daily package: `clgen` replayed
//! sequentially against the cg tap streams (fixtures/taps/daily/,
//! provenance in the daily-core tap-schema.md).
//!
//! Replay protocol: initialize from the FIRST record's captured state,
//! then per record assert every internally-evolved surface (seeds
//! except the externally-advanced k7/k10, rolling v's except windg's
//! v9, `l`/`mox`/`dax`, the clamped skew) before the call — localizing
//! any desync — and the generated surface after it. Externally-written
//! surfaces (`mo`, `ida`, `nsim`, `msim`, observed `r(ida)`,
//! day_gen's in-place F→C `tmxg`/`tmng`, windg's `v9`, dstg's `k7`,
//! timepk's `k10`) are set from the capture as per-record inputs,
//! exactly as the item-3 `dstg`/`ranset` replays treat `mox`/`k5`.

use cligen::acm::AcmState;
use cligen::cbk1::Cbk1State;
use cligen::cbk3::Cbk3State;
use cligen::cbk4::Cbk4State;
use cligen::cbk5::Cbk5State;
use cligen::cbk7::Cbk7State;
use cligen::cbk9::Cbk9State;
use cligen::cinterp::CinterpState;
use cligen::crandom3::Crandom3State;
use cligen::daily::{alphb, clgen, r5monb, windg};
use cligen::deviates::DstgState;
use cligen::libm_pinned::{cosf_pinned, sinf_pinned};
use cligen::monthlies::lintrp;
use cligen::par::{sta_parms, ParFile};
use cligen::rng::{RansetState, SeedState};
use std::path::{Path, PathBuf};

/// (tap case dir, .par path, interp mode, iopt)
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
    v: [u32; 6], // v1 v3 v5 v7 v9 v11
    tmxg_in: u32,
    tmng_in: u32,
    rst3_in: u32,
    dax_post: i32,
    cols: [u32; 6], // vvx v2x v4x v6x v8x v12x at dax_post
    out: [u32; 6],  // r tmxg tmng tdp ra rmx
    l_out: i32,
}

fn hex(field: &str) -> u32 {
    u32::from_str_radix(field, 16).unwrap()
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
            let (b, k, v, cc, a) = (&c[0], &c[1], &c[2], &c[3], &c[4]);
            assert_eq!((b[0], k[0], v[0], cc[0], a[0]), ("B", "K", "V", "C", "A"));
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
                rst3_in: hex(v[9]),
                dax_post: cc[1].parse().unwrap(),
                cols: std::array::from_fn(|i| hex(cc[i + 2])),
                out: std::array::from_fn(|i| hex(a[i + 1])),
                l_out: a[7].parse().unwrap(),
            }
        })
        .collect()
}

struct WgRec {
    mo: i32,
    dax: i32,
    v9_in: u32,
    fx: u32,
    wv: u32,
    th: u32,
    v9_out: u32,
    j: i32,
}

fn parse_wg(path: &Path) -> Vec<WgRec> {
    let data = std::fs::read_to_string(path).unwrap();
    let lines: Vec<Vec<&str>> = data
        .lines()
        .map(|line| line.split_whitespace().collect())
        .collect();
    assert_eq!(lines.len() % 2, 0, "{}: partial wg record", path.display());
    lines
        .chunks_exact(2)
        .map(|record| {
            let (w, x) = (&record[0], &record[1]);
            assert_eq!((w[0], x[0]), ("W", "X"));
            WgRec {
                mo: w[1].parse().unwrap(),
                dax: w[2].parse().unwrap(),
                v9_in: hex(w[3]),
                fx: hex(w[4]),
                wv: hex(x[1]),
                th: hex(x[2]),
                v9_out: hex(x[3]),
                j: x[4].parse().unwrap(),
            }
        })
        .collect()
}

struct AbRec {
    mo: i32,
    ida: i32,
    k7: [i32; 4],
    r: u32,
    wi: u32,
    sml: u32,
    r1: u32,
}

fn parse_ab(path: &Path) -> Vec<AbRec> {
    let data = std::fs::read_to_string(path).unwrap();
    let lines: Vec<Vec<&str>> = data
        .lines()
        .map(|line| line.split_whitespace().collect())
        .collect();
    assert_eq!(lines.len() % 2, 0, "{}: partial ab record", path.display());
    lines
        .chunks_exact(2)
        .map(|record| {
            let (g, h) = (&record[0], &record[1]);
            assert_eq!((g[0], h[0]), ("G", "H"));
            AbRec {
                mo: g[1].parse().unwrap(),
                ida: g[2].parse().unwrap(),
                k7: std::array::from_fn(|i| g[i + 3].parse().unwrap()),
                r: hex(g[7]),
                wi: hex(g[8]),
                sml: hex(g[9]),
                r1: hex(h[1]),
            }
        })
        .collect()
}

fn parse_r5(path: &Path) -> [u32; 12] {
    let data = std::fs::read_to_string(path).unwrap();
    let fields: Vec<&str> = data.split_whitespace().collect();
    assert_eq!(fields.len(), 13, "{}: malformed r5 record", path.display());
    assert_eq!(fields[0], "R5");
    std::array::from_fn(|i| hex(fields[i + 1]))
}

struct Replay {
    bk1: Cbk1State,
    bk3: Cbk3State,
    bk4: Cbk4State,
    bk5: Cbk5State,
    bk7: Cbk7State,
    bk9: Cbk9State,
    ci: CinterpState,
    cr: Crandom3State,
    rs: RansetState,
    acm: AcmState,
    dg: DstgState,
}

/// Station setup: sta_parms + the main program's latitude/constant
/// block (`cligen.f:882-887`: clt = 57.296, yls/ylc from f32 sin/cos,
/// pit = 58.13).
fn setup(par_rel: &str, interp: i32, iopt: i32) -> Replay {
    let root = repo_root();
    let bytes = std::fs::read(root.join("fixtures").join(par_rel)).unwrap();
    let par = ParFile::parse(&bytes).unwrap();
    let mut bk1 = Cbk1State::default();
    let mut bk7 = Cbk7State::default();
    let mut bk9 = Cbk9State::default();
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
    // Source literal pi2 = 6.283185 (cligen.f:884) resembles TAU but is
    // the specification's constant.
    #[allow(clippy::approx_constant)]
    {
        bk1.pi2 = 6.283185;
    }
    Replay {
        bk1,
        bk3: Cbk3State::default(),
        bk4: Cbk4State {
            iopt,
            ..Cbk4State::default()
        },
        bk5: Cbk5State::default(),
        bk7,
        bk9,
        ci,
        cr: Crandom3State::default(),
        rs: RansetState::default(),
        acm: AcmState::default(),
        dg: DstgState::default(),
    }
}

fn seed_matrix(bk7: &Cbk7State) -> [[i32; 4]; 10] {
    [
        bk7.k1.0, bk7.k2.0, bk7.k3.0, bk7.k4.0, bk7.k5.0, bk7.k6.0, bk7.k7.0, bk7.k8.0, bk7.k9.0,
        bk7.k10.0,
    ]
}

fn replay_wg(case: &str, par_rel: &str, interp: i32, iopt: i32, path: &Path) -> usize {
    let recs = parse_wg(path);
    let mut st = setup(par_rel, interp, iopt);
    for (idx, rec) in recs.iter().enumerate() {
        let at = |what: &str| format!("{case}:{}: windg {what}", idx + 1);
        st.bk4.mo = rec.mo;
        st.cr.dax = rec.dax;
        st.bk7.v9 = f32::from_bits(rec.v9_in);
        st.cr.ranary[5][(rec.dax - 1) as usize] = f32::from_bits(rec.fx);
        // On non-calm records windg shifts v10 into v9, so the exit
        // tap supplies the otherwise-unrecorded batch-column input.
        // Calm records do not read the column.
        st.cr.ranary[6][(rec.dax - 1) as usize] = f32::from_bits(rec.v9_out);

        windg(&mut st.bk1, &mut st.bk3, &st.bk4, &mut st.bk7, &mut st.cr);

        assert_eq!(st.cr.fx.to_bits(), rec.fx, "{}", at("fx"));
        assert_eq!(st.bk1.wv.to_bits(), rec.wv, "{}", at("wv"));
        assert_eq!(st.bk1.th.to_bits(), rec.th, "{}", at("th"));
        assert_eq!(st.bk7.v9.to_bits(), rec.v9_out, "{}", at("v9 out"));
        assert_eq!(st.bk3.j, rec.j, "{}", at("j"));
    }
    recs.len()
}

fn replay_ab(case: &str, par_rel: &str, interp: i32, iopt: i32, path: &Path) -> usize {
    let recs = parse_ab(path);
    if recs.is_empty() {
        return 0;
    }
    let mut st = setup(par_rel, interp, iopt);
    st.bk7.k7 = SeedState(recs[0].k7);
    for (idx, rec) in recs.iter().enumerate() {
        let at = |what: &str| format!("{case}:{}: alphb {what}", idx + 1);
        assert_eq!(st.bk7.k7.0, rec.k7, "{}", at("k7 entry"));
        st.bk4.mo = rec.mo;
        st.bk3.ida = rec.ida;
        st.bk5.r[(rec.ida - 1) as usize] = f32::from_bits(rec.r);
        st.bk5.sml = f32::from_bits(rec.sml);
        st.bk9.wi[(rec.mo - 1) as usize] = f32::from_bits(rec.wi);
        st.cr.mox = rec.mo;

        alphb(
            &st.bk3,
            &st.bk4,
            &st.bk5,
            &mut st.bk7,
            &mut st.bk9,
            &mut st.dg,
            &mut st.cr,
        );

        assert_eq!(st.bk9.r1.to_bits(), rec.r1, "{}", at("r1"));
    }
    recs.len()
}

fn replay_r5(par_rel: &str, interp: i32, iopt: i32, path: &Path) {
    let expected = parse_r5(path);
    let mut st = setup(par_rel, interp, iopt);
    r5monb(&st.bk4, &st.bk7, &mut st.bk9);
    for (month, bits) in expected.iter().enumerate() {
        assert_eq!(
            st.bk9.wi[month].to_bits(),
            *bits,
            "{}: r5 wi({})",
            path.display(),
            month + 1
        );
    }
}

fn replay_cg(case: &str, par_rel: &str, interp: i32, iopt: i32, path: &Path) -> usize {
    let recs = parse_cg(path);
    if recs.is_empty() {
        return 0;
    }
    let mut st = setup(par_rel, interp, iopt);
    // Initialize the internally-evolved state from the first record.
    let first = &recs[0];
    let seeds = first.seeds;
    st.bk7.k1 = SeedState(seeds[0]);
    st.bk7.k2 = SeedState(seeds[1]);
    st.bk7.k3 = SeedState(seeds[2]);
    st.bk7.k4 = SeedState(seeds[3]);
    st.bk7.k5 = SeedState(seeds[4]);
    st.bk7.k6 = SeedState(seeds[5]);
    st.bk7.k7 = SeedState(seeds[6]);
    st.bk7.k8 = SeedState(seeds[7]);
    st.bk7.k9 = SeedState(seeds[8]);
    st.bk7.k10 = SeedState(seeds[9]);
    st.bk7.v1 = f32::from_bits(first.v[0]);
    st.bk7.v3 = f32::from_bits(first.v[1]);
    st.bk7.v5 = f32::from_bits(first.v[2]);
    st.bk7.v7 = f32::from_bits(first.v[3]);
    st.bk7.v9 = f32::from_bits(first.v[4]);
    st.bk7.v11 = f32::from_bits(first.v[5]);
    st.bk7.l = first.l;
    st.cr.mox = first.mox;
    st.cr.dax = first.dax;

    for (idx, rec) in recs.iter().enumerate() {
        let at = |what: &str| format!("{case}:{}: {what}", idx + 1);
        // Internally-evolved assertions (desync localization).
        let sm = seed_matrix(&st.bk7);
        for (s, got) in sm.iter().enumerate() {
            if s == 6 || s == 9 {
                continue; // k7 (dstg via alphb) and k10 (timepk) are external
            }
            assert_eq!(*got, rec.seeds[s], "{}", at(&format!("seed k{}", s + 1)));
        }
        assert_eq!(st.bk7.v1.to_bits(), rec.v[0], "{}", at("v1"));
        assert_eq!(st.bk7.v3.to_bits(), rec.v[1], "{}", at("v3"));
        assert_eq!(st.bk7.v5.to_bits(), rec.v[2], "{}", at("v5"));
        assert_eq!(st.bk7.v7.to_bits(), rec.v[3], "{}", at("v7"));
        assert_eq!(st.bk7.v11.to_bits(), rec.v[5], "{}", at("v11"));
        assert_eq!(st.bk7.l, rec.l, "{}", at("l"));
        assert_eq!(st.cr.mox, rec.mox, "{}", at("mox"));
        assert_eq!(st.cr.dax, rec.dax, "{}", at("dax"));
        assert_eq!(
            st.bk7.rst[(rec.mo - 1) as usize][2].to_bits(),
            rec.rst3_in,
            "{}",
            at("rst(mo,3)")
        );
        // External per-record inputs.
        st.bk7.k7 = SeedState(rec.seeds[6]);
        st.bk7.k10 = SeedState(rec.seeds[9]);
        st.bk7.v9 = f32::from_bits(rec.v[4]);
        st.bk7.tmxg = f32::from_bits(rec.tmxg_in);
        st.bk7.tmng = f32::from_bits(rec.tmng_in);
        st.bk4.mo = rec.mo;
        st.bk3.ida = rec.ida;
        st.bk7.nsim = rec.nsim;
        st.bk7.msim = rec.msim;
        if rec.nsim == 0 {
            // Observed precipitation: day_gen wrote r(ida) before clgen.
            st.bk5.r[(rec.ida - 1) as usize] = f32::from_bits(rec.out[0]);
        }
        if st.ci.interp == 1 {
            // day_gen calls lintrp before clgen (cligen.f:3090-3093);
            // jd is the day-of-month clgen will land on (== dax after
            // its month-boundary update, which the C line re-verifies).
            let jd = if rec.mo != rec.mox { 1 } else { rec.dax + 1 };
            lintrp(rec.mo, jd, rec.ntd, &mut st.ci);
        }

        let _events = clgen(
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

        // Post-boundary column consumption.
        assert_eq!(st.cr.dax, rec.dax_post, "{}", at("dax post"));
        let d = rec.dax_post as usize;
        let cols = [
            st.cr.vvx(d),
            st.cr.v2x(d),
            st.cr.v4x(d),
            st.cr.v6x(d),
            st.cr.v8x(d),
            st.cr.v12x(d),
        ];
        for (i, c) in cols.iter().enumerate() {
            assert_eq!(c.to_bits(), rec.cols[i], "{}", at(&format!("column {i}")));
        }
        // Generated surface.
        assert_eq!(
            st.bk5.r[(rec.ida - 1) as usize].to_bits(),
            rec.out[0],
            "{}",
            at("r(ida)")
        );
        assert_eq!(st.bk7.tmxg.to_bits(), rec.out[1], "{}", at("tmxg"));
        assert_eq!(st.bk7.tmng.to_bits(), rec.out[2], "{}", at("tmng"));
        assert_eq!(st.bk1.tdp.to_bits(), rec.out[3], "{}", at("tdp"));
        assert_eq!(st.bk7.ra.to_bits(), rec.out[4], "{}", at("ra"));
        assert_eq!(st.bk7.rmx.to_bits(), rec.out[5], "{}", at("rmx"));
        assert_eq!(st.bk7.l, rec.l_out, "{}", at("l out"));
    }
    recs.len()
}

#[test]
fn clgen_replays_fortran_cg_samples() {
    let root = repo_root();
    let mut total = 0;
    for (case, par_rel, interp, iopt) in CASES {
        let path = root
            .join("fixtures/taps/daily")
            .join(case)
            .join("cg-sample.tap");
        total += replay_cg(case, par_rel, interp, iopt, &path);
    }
    assert!(
        total >= 4_000,
        "expected substantial cg replay coverage, got {total}"
    );
}

#[test]
fn windg_replays_fortran_wg_samples() {
    let root = repo_root();
    let mut total = 0;
    for (case, par_rel, interp, iopt) in CASES {
        let path = root
            .join("fixtures/taps/daily")
            .join(case)
            .join("wg-sample.tap");
        total += replay_wg(case, par_rel, interp, iopt, &path);
    }
    assert!(
        total >= 4_000,
        "expected substantial wg replay coverage, got {total}"
    );
}

#[test]
fn alphb_replays_fortran_ab_samples() {
    let root = repo_root();
    let mut total = 0;
    for (case, par_rel, interp, iopt) in CASES {
        let path = root
            .join("fixtures/taps/daily")
            .join(case)
            .join("ab-sample.tap");
        if path.exists() {
            total += replay_ab(case, par_rel, interp, iopt, &path);
        }
    }
    assert!(
        total >= 4_000,
        "expected substantial ab replay coverage, got {total}"
    );
}

#[test]
fn r5monb_matches_fortran_setup_snapshots() {
    let root = repo_root();
    for (case, par_rel, interp, iopt) in CASES {
        let path = root.join("fixtures/taps/daily").join(case).join("r5.tap");
        replay_r5(par_rel, interp, iopt, &path);
    }
}

#[test]
#[ignore = "full windg/alphb/r5monb replay against local daily tap-runs capture"]
fn full_stage_c_unit_streams_bit_identical() {
    let root = repo_root();
    let runs = root.join("docs/work-packages/20260709-daily-core-port/artifacts/tap-runs");
    let mut wg_total = 0;
    let mut ab_total = 0;
    for (case, par_rel, interp, iopt) in CASES {
        let case_dir = runs.join(case);
        wg_total += replay_wg(case, par_rel, interp, iopt, &case_dir.join("cligen_wg.tap"));
        ab_total += replay_ab(case, par_rel, interp, iopt, &case_dir.join("cligen_ab.tap"));
        replay_r5(par_rel, interp, iopt, &case_dir.join("cligen_r5.tap"));
    }
    println!("full unit replays: windg calls={wg_total}, alphb calls={ab_total}, r5 runs=10");
    assert!(wg_total > 80_000);
    assert!(ab_total > 20_000);
}

#[test]
#[ignore = "full cg replay against local daily tap-runs capture (evidence gate)"]
fn full_cg_streams_bit_identical() {
    let root = repo_root();
    let runs = root.join("docs/work-packages/20260709-daily-core-port/artifacts/tap-runs");
    let mut total = 0;
    for (case, par_rel, interp, iopt) in CASES {
        let path = runs.join(case).join("cligen_cg.tap");
        assert!(path.exists(), "local capture missing: {}", path.display());
        total += replay_cg(case, par_rel, interp, iopt, &path);
    }
    println!("full cg replay: calls={total}");
    assert!(total > 80_000);
}
