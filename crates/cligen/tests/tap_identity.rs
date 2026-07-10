//! Faithful-mode bit-identity tests against Fortran tap fixtures.
//!
//! Tap provenance: docs/work-packages/20260709-rng-deviates-port/
//! artifacts/{tap-schema.md,tap-manifest.md}. Committed samples live in
//! fixtures/taps/ (first 1,000 rn/n1 records per fixture; dg streams in
//! full). Full-stream verification against the local capture tree runs
//! via the `#[ignore]`-gated tests (`cargo test -- --ignored`).

use cligen::acm::AcmState;
use cligen::cbk4::Cbk4State;
use cligen::cbk7::Cbk7State;
use cligen::crandom3::Crandom3State;
use cligen::deviates::{dstg, dstn1, DstgState};
use cligen::rng::{randn, ranset, RansetState, SeedState};
use std::path::{Path, PathBuf};

const CASES: [&str; 12] = [
    "new-meadows-id-seed0",
    "new-meadows-id-seed17",
    "jeogla-au-seed0",
    "jeogla-au-seed17",
    "mt-wilson-ca-observed-seed0",
    "mt-wilson-ca-observed-seed17",
    "fish-springs-ut-observed-padded-seed0",
    "fish-springs-ut-observed-padded-seed17",
    "fish-springs-ut-observed-truncated-seed0",
    "fish-springs-ut-observed-truncated-seed17",
    "new-meadows-id-single-storm-seed0",
    "new-meadows-id-single-storm-seed17",
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn sample_dir(case: &str) -> PathBuf {
    repo_root().join("fixtures/taps").join(case)
}

fn tap_runs_dir(case: &str) -> PathBuf {
    repo_root()
        .join("docs/work-packages/20260709-rng-deviates-port/artifacts/tap-runs")
        .join(case)
}

/// `format(4i5,1x,z8.8)` — entry seed state + result bits.
fn parse_rn(line: &str) -> ([i32; 4], u32) {
    let mut it = line.split_whitespace();
    let k = [(); 4].map(|_| it.next().unwrap().parse::<i32>().unwrap());
    let bits = u32::from_str_radix(it.next().unwrap(), 16).unwrap();
    (k, bits)
}

/// `format(3(z8.8,1x))` — rn1, rn2, result bits.
fn parse_n1(line: &str) -> (u32, u32, u32) {
    let mut it = line.split_whitespace();
    let mut f = || u32::from_str_radix(it.next().unwrap(), 16).unwrap();
    (f(), f(), f())
}

struct DgRec {
    mox: i32,
    iarrct: usize,
    k7: [i32; 4],
    ai: u32,
    result: u32,
}

/// `format(i3,1x,i3,1x,4i5,1x,z8.8,1x,z8.8)`.
fn parse_dg(line: &str) -> DgRec {
    let mut it = line.split_whitespace();
    let mox = it.next().unwrap().parse().unwrap();
    let iarrct = it.next().unwrap().parse().unwrap();
    let k7 = [(); 4].map(|_| it.next().unwrap().parse::<i32>().unwrap());
    let ai = u32::from_str_radix(it.next().unwrap(), 16).unwrap();
    let result = u32::from_str_radix(it.next().unwrap(), 16).unwrap();
    DgRec {
        mox,
        iarrct,
        k7,
        ai,
        result,
    }
}

struct RsStats {
    g_dimi: i32,
    g_dimp: i32,
    g_dsum: u64,
    g_ssum: u64,
    chicnt: [i32; 20],
}

struct RsRec {
    mox: i32,
    ntd: i32,
    iyear: i32,
    iopt: i32,
    entry_ell: i32,
    prw: [u32; 2],
    entry_seeds: [[i32; 4]; 10],
    entry_last: [u32; 9],
    exit_ell: i32,
    exit_seeds: [[i32; 4]; 10],
    exit_last: [u32; 9],
    ranary: [[u32; 31]; 9],
    stats: [RsStats; 9],
}

fn parse_hex32(field: &str) -> u32 {
    u32::from_str_radix(field, 16).unwrap()
}

fn parse_hex64(field: &str) -> u64 {
    u64::from_str_radix(field, 16).unwrap()
}

fn parse_rs_seeds(fields: &[&str]) -> [[i32; 4]; 10] {
    assert_eq!(fields[0], "K");
    assert_eq!(fields.len(), 41);
    let values: Vec<i32> = fields[1..]
        .iter()
        .map(|field| field.parse().unwrap())
        .collect();
    std::array::from_fn(|stream| std::array::from_fn(|word| values[stream * 4 + word]))
}

fn parse_rs_last(fields: &[&str]) -> [u32; 9] {
    assert_eq!(fields[0], "L");
    assert_eq!(fields.len(), 10);
    std::array::from_fn(|i| parse_hex32(fields[i + 1]))
}

fn parse_rs_stream(path: &Path) -> Vec<RsRec> {
    let data = std::fs::read_to_string(path).unwrap();
    let lines: Vec<Vec<&str>> = data
        .lines()
        .map(|line| line.split_whitespace().collect())
        .collect();
    assert_eq!(
        lines.len() % 24,
        0,
        "{}: partial ranset record",
        path.display()
    );
    let mut records = Vec::new();
    for chunk in lines.chunks_exact(24) {
        let b = &chunk[0];
        assert_eq!(b[0], "B");
        let entry_seeds = parse_rs_seeds(&chunk[1]);
        let entry_last = parse_rs_last(&chunk[2]);
        let e = &chunk[3];
        assert_eq!(e[0], "E");
        let exit_seeds = parse_rs_seeds(&chunk[4]);
        let exit_last = parse_rs_last(&chunk[5]);
        let mut ranary = [[0u32; 31]; 9];
        let mut stats = Vec::with_capacity(9);
        for j in 0..9 {
            let a = &chunk[6 + j * 2];
            assert_eq!(a[0], "A");
            assert_eq!(a[1].parse::<usize>().unwrap(), j + 1);
            ranary[j] = std::array::from_fn(|i| parse_hex32(a[i + 2]));
            let g = &chunk[7 + j * 2];
            assert_eq!(g[0], "G");
            assert_eq!(g[1].parse::<usize>().unwrap(), j + 1);
            stats.push(RsStats {
                g_dimi: g[2].parse().unwrap(),
                g_dimp: g[3].parse().unwrap(),
                g_dsum: parse_hex64(g[4]),
                g_ssum: parse_hex64(g[5]),
                chicnt: std::array::from_fn(|i| g[i + 6].parse().unwrap()),
            });
        }
        records.push(RsRec {
            mox: b[1].parse().unwrap(),
            ntd: b[2].parse().unwrap(),
            iyear: b[3].parse().unwrap(),
            iopt: b[4].parse().unwrap(),
            entry_ell: b[5].parse().unwrap(),
            prw: [parse_hex32(b[6]), parse_hex32(b[7])],
            entry_seeds,
            entry_last,
            exit_ell: e[2].parse().unwrap(),
            exit_seeds,
            exit_last,
            ranary,
            stats: stats.try_into().ok().unwrap(),
        });
    }
    records
}

fn seed_matrix(seeds: &Cbk7State) -> [[i32; 4]; 10] {
    [
        seeds.k1.0,
        seeds.k2.0,
        seeds.k3.0,
        seeds.k4.0,
        seeds.k5.0,
        seeds.k6.0,
        seeds.k7.0,
        seeds.k8.0,
        seeds.k9.0,
        seeds.k10.0,
    ]
}

fn set_seed_matrix(seeds: &mut Cbk7State, values: [[i32; 4]; 10]) {
    seeds.k1 = SeedState(values[0]);
    seeds.k2 = SeedState(values[1]);
    seeds.k3 = SeedState(values[2]);
    seeds.k4 = SeedState(values[3]);
    seeds.k5 = SeedState(values[4]);
    seeds.k6 = SeedState(values[5]);
    seeds.k7 = SeedState(values[6]);
    seeds.k8 = SeedState(values[7]);
    seeds.k9 = SeedState(values[8]);
    seeds.k10 = SeedState(values[9]);
}

fn replay_rs_stream(path: &Path) -> usize {
    let records = parse_rs_stream(path);
    if records.is_empty() {
        return 0;
    }
    let mut seeds = Cbk7State::default();
    set_seed_matrix(&mut seeds, records[0].entry_seeds);
    let mut sv = RansetState::default();
    let mut acm = AcmState::default();
    let mut cr = Crandom3State::default();
    for (index, rec) in records.iter().enumerate() {
        let initial_common = if index == 0 {
            Some([0usize, 1, 2, 3, 4, 5, 7, 8, 9].map(|stream| {
                let mut seed = SeedState(rec.entry_seeds[stream]);
                randn(&mut seed).to_bits()
            }))
        } else {
            None
        };
        let before = seed_matrix(&seeds);
        for stream in (0..10).filter(|stream| !matches!(*stream, 4 | 6 | 9)) {
            assert_eq!(
                before[stream],
                rec.entry_seeds[stream],
                "{}:{} entry seed stream {}",
                path.display(),
                index + 1,
                stream + 1
            );
        }
        // k5/k7/k10 have live external draw sites between month calls
        // (clgen's v7 band-aid, dstg, and timepk respectively). Treat their
        // captured entries as external input, exactly as replay_dg_stream
        // treats mox.
        seeds.k5 = SeedState(rec.entry_seeds[4]);
        seeds.k7 = SeedState(rec.entry_seeds[6]);
        seeds.k10 = SeedState(rec.entry_seeds[9]);
        assert_eq!(
            sv.ell,
            rec.entry_ell,
            "{}:{} entry ell",
            path.display(),
            index + 1
        );
        assert_eq!(
            sv.last_r.map(f32::to_bits),
            rec.entry_last,
            "{}:{} entry last_r",
            path.display(),
            index + 1
        );
        cr.mox = rec.mox;
        let month = (rec.mox - 1) as usize;
        seeds.prw[month] = rec.prw.map(f32::from_bits);
        let bk4 = Cbk4State {
            iopt: rec.iopt,
            ..Cbk4State::default()
        };
        ranset(
            rec.ntd,
            rec.iyear,
            &bk4,
            &mut seeds,
            &mut sv,
            &mut acm,
            &mut cr,
            &mut Default::default(),
        );
        assert_eq!(
            seed_matrix(&seeds),
            rec.exit_seeds,
            "{}:{} exit seeds",
            path.display(),
            index + 1
        );
        assert_eq!(
            sv.ell,
            rec.exit_ell,
            "{}:{} exit ell",
            path.display(),
            index + 1
        );
        assert_eq!(
            sv.last_r.map(f32::to_bits),
            rec.exit_last,
            "{}:{} exit last_r",
            path.display(),
            index + 1
        );
        if let Some(expected) = initial_common {
            // The first-call branch writes the common-block rolling values
            // from one draw off each captured entry seed
            // (cligen.f:4099-4117). Those values have external writers
            // between later month calls, so assert them only here.
            assert_eq!(
                cr.vv.to_bits(),
                expected[0],
                "{}: initial vv",
                path.display()
            );
            assert_eq!(
                seeds.v1.to_bits(),
                expected[1],
                "{}: initial v1",
                path.display()
            );
            assert_eq!(
                seeds.v3.to_bits(),
                expected[2],
                "{}: initial v3",
                path.display()
            );
            assert_eq!(
                seeds.v5.to_bits(),
                expected[3],
                "{}: initial v5",
                path.display()
            );
            assert_eq!(
                seeds.v7.to_bits(),
                expected[4],
                "{}: initial v7",
                path.display()
            );
            assert_eq!(
                cr.fx.to_bits(),
                expected[5],
                "{}: initial fx",
                path.display()
            );
            assert_eq!(
                seeds.v9.to_bits(),
                expected[6],
                "{}: initial v9",
                path.display()
            );
            assert_eq!(
                seeds.v11.to_bits(),
                expected[7],
                "{}: initial v11",
                path.display()
            );
            assert_eq!(cr.z.to_bits(), expected[8], "{}: initial z", path.display());
        }
        for j in 0..9 {
            assert_eq!(
                cr.ranary[j].map(f32::to_bits),
                rec.ranary[j],
                "{}:{} ranary parameter {}",
                path.display(),
                index + 1,
                j + 1
            );
            assert_eq!(
                cr.g_dimi[month],
                rec.stats[j].g_dimi,
                "{}:{} g_dimi",
                path.display(),
                index + 1
            );
            assert_eq!(
                cr.g_dimp[month],
                rec.stats[j].g_dimp,
                "{}:{} g_dimp",
                path.display(),
                index + 1
            );
            assert_eq!(
                cr.g_dsum[j][month].to_bits(),
                rec.stats[j].g_dsum,
                "{}:{} g_dsum parameter {}",
                path.display(),
                index + 1,
                j + 1
            );
            assert_eq!(
                cr.g_ssum[j][month].to_bits(),
                rec.stats[j].g_ssum,
                "{}:{} g_ssum parameter {}",
                path.display(),
                index + 1,
                j + 1
            );
            assert_eq!(
                cr.chicnt[j][month],
                rec.stats[j].chicnt,
                "{}:{} chicnt parameter {}",
                path.display(),
                index + 1,
                j + 1
            );
        }
    }
    records.len()
}

fn check_rn_stream(path: &Path) -> usize {
    let data = std::fs::read_to_string(path).unwrap();
    let mut n = 0;
    for (idx, line) in data.lines().enumerate() {
        let (k, bits) = parse_rn(line);
        let mut state = SeedState(k);
        let got = randn(&mut state);
        assert_eq!(
            got.to_bits(),
            bits,
            "{}:{}: randn({:?}) = {:e}, expected bits {:08X}",
            path.display(),
            idx + 1,
            k,
            got,
            bits
        );
        n += 1;
    }
    n
}

fn check_n1_stream(path: &Path) -> usize {
    let data = std::fs::read_to_string(path).unwrap();
    let mut n = 0;
    for (idx, line) in data.lines().enumerate() {
        let (a, b, r) = parse_n1(line);
        let got = dstn1(f32::from_bits(a), f32::from_bits(b));
        assert_eq!(
            got.to_bits(),
            r,
            "{}:{}: dstn1(bits {:08X}, {:08X}) diverged",
            path.display(),
            idx + 1,
            a,
            b
        );
        n += 1;
    }
    n
}

/// Sequential per-fixture replay per the tap schema: initialize from the
/// first record's captured state, then assert `iarrct`/`k7` before every
/// call (localizing any divergence) and result bits after.
fn replay_dg_stream(path: &Path) -> usize {
    let data = std::fs::read_to_string(path).unwrap();
    let recs: Vec<DgRec> = data.lines().map(parse_dg).collect();
    if recs.is_empty() {
        return 0;
    }
    assert_eq!(
        recs[0].iarrct, 30,
        "first dstg call must see an empty batch"
    );
    let mut k7 = SeedState(recs[0].k7);
    let mut sv = DstgState::default();
    let mut cr = Crandom3State::default();
    for (idx, rec) in recs.iter().enumerate() {
        assert_eq!(
            sv.iarrct,
            rec.iarrct,
            "{}:{}: iarrct desync (external mutation or QC divergence)",
            path.display(),
            idx + 1
        );
        assert_eq!(
            k7.0,
            rec.k7,
            "{}:{}: k7 desync (external mutation or QC divergence)",
            path.display(),
            idx + 1
        );
        cr.mox = rec.mox;
        let got = dstg(
            f32::from_bits(rec.ai),
            &mut k7,
            &mut sv,
            &mut cr,
            &mut Default::default(),
        );
        assert_eq!(
            got.to_bits(),
            rec.result,
            "{}:{}: dstg result diverged",
            path.display(),
            idx + 1
        );
    }
    recs.len()
}

#[test]
fn randn_matches_fortran_tap_samples() {
    let mut total = 0;
    for case in CASES {
        total += check_rn_stream(&sample_dir(case).join("rn-sample.tap"));
    }
    assert!(
        total >= 10_000,
        "expected substantial sample coverage, got {total}"
    );
}

#[test]
fn dstn1_matches_fortran_tap_samples() {
    let mut total = 0;
    for case in CASES {
        total += check_n1_stream(&sample_dir(case).join("n1-sample.tap"));
    }
    assert!(total > 0);
}

#[test]
fn dstg_replays_fortran_tap_streams() {
    let mut total = 0;
    for case in CASES {
        let dg = sample_dir(case).join("dg.tap");
        if dg.exists() {
            // dg taps are committed in full (single-storm mode never
            // calls dstg and has none).
            total += replay_dg_stream(&dg);
        }
    }
    assert!(total >= 25_000, "expected full dg coverage, got {total}");
}

/// The `-r` burn (k1..k9, k10 excluded; cligen.f:723-737) plus the main
/// program's single warm draw from k7 (cligen.f:891) must land exactly
/// on the k7 state the first dstg call observed.
#[test]
fn burn_and_warm_draw_reach_first_dstg_state() {
    for case in CASES {
        let dg = sample_dir(case).join("dg.tap");
        if !dg.exists() {
            continue;
        }
        let first = parse_dg(
            std::fs::read_to_string(&dg)
                .unwrap()
                .lines()
                .next()
                .unwrap(),
        );
        let mut seeds = Cbk7State::default();
        if case.ends_with("seed17") {
            seeds.burn(17);
        }
        let _warm = randn(&mut seeds.k7);
        assert_eq!(
            seeds.k7.0, first.k7,
            "{case}: burn+warm k7 does not reach first dstg entry state"
        );
    }
}

#[test]
fn ranset_replays_fortran_tap_samples() {
    let mut total = 0;
    for case in CASES {
        total += replay_rs_stream(&sample_dir(case).join("rs-sample.tap"));
    }
    assert!(
        total >= 100,
        "expected multi-fixture ranset coverage, got {total}"
    );
}

#[test]
#[should_panic(expected = "mox=0/out-of-range")]
fn ranset_fails_closed_on_fortran_month_zero_underrun() {
    let bk4 = Cbk4State {
        iopt: 5,
        ..Cbk4State::default()
    };
    let mut seeds = Cbk7State::default();
    let mut sv = RansetState::default();
    let mut acm = AcmState::default();
    let mut cr = Crandom3State::default();
    ranset(
        365,
        1,
        &bk4,
        &mut seeds,
        &mut sv,
        &mut acm,
        &mut cr,
        &mut Default::default(),
    );
}

#[test]
#[ignore = "full-stream verification against local tap-runs capture (evidence gate)"]
fn full_tap_streams_bit_identical() {
    let mut rn_total = 0usize;
    let mut n1_total = 0usize;
    let mut dg_total = 0usize;
    for case in CASES {
        let d = tap_runs_dir(case);
        assert!(d.exists(), "local tap capture missing: {}", d.display());
        rn_total += check_rn_stream(&d.join("cligen_rn.tap"));
        n1_total += check_n1_stream(&d.join("cligen_n1.tap"));
        let dg = d.join("cligen_dg.tap");
        if std::fs::metadata(&dg).map(|m| m.len() > 0).unwrap_or(false) {
            dg_total += replay_dg_stream(&dg);
        }
    }
    println!("full-stream identity: randn={rn_total} dstn1={n1_total} dstg={dg_total}");
    assert!(rn_total > 1_000_000);
}

#[test]
#[ignore = "full ranset replay against local Stage C tap-runs capture (evidence gate)"]
fn full_ranset_streams_bit_identical() {
    let mut total = 0usize;
    for case in CASES {
        let path = tap_runs_dir(case).join("cligen_rs.tap");
        assert!(
            path.exists(),
            "local ranset capture missing: {}",
            path.display()
        );
        total += replay_rs_stream(&path);
    }
    println!("full ranset replay: calls={total}");
    assert!(total > 1_000);
}
