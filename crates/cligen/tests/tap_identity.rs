//! Faithful-mode bit-identity tests against Fortran tap fixtures.
//!
//! Tap provenance: docs/work-packages/20260709-rng-deviates-port/
//! artifacts/{tap-schema.md,tap-manifest.md}. Committed samples live in
//! fixtures/taps/ (first 1,000 rn/n1 records per fixture; dg streams in
//! full). Full-stream verification against the local capture tree runs
//! via the `#[ignore]`-gated tests (`cargo test -- --ignored`).

use cligen::cbk7::Cbk7Seeds;
use cligen::crandom3::Crandom3State;
use cligen::deviates::{dstg, dstn1, DstgState};
use cligen::rng::{randn, SeedState};
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
        let got = dstg(f32::from_bits(rec.ai), &mut k7, &mut sv, &mut cr);
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
        let mut seeds = Cbk7Seeds::default();
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
