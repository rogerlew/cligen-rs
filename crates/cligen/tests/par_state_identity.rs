//! Faithful-mode bit-identity for the par package: `ParFile::parse` +
//! `sta_parms` (with `fouri1`/`ryf1` on the interp-2/3 paths) must
//! reproduce every value of the Fortran par-state snapshots, and
//! `to_bytes` must reproduce the fixture `.par` bytes.
//!
//! Snapshot provenance: docs/work-packages/20260709-par-monthlies-port/
//! artifacts/{tap-schema.md,tap-manifest.md}. Committed snapshots are
//! complete (191 lines per station × interp combo) — unlike the
//! rn/n1 streams there is no larger local capture to gate separately;
//! the byte-identical seed/mode equivalence classes are recorded in the
//! manifest.

use cligen::cbk1::Cbk1State;
use cligen::cbk7::Cbk7State;
use cligen::cbk9::Cbk9State;
use cligen::cinterp::CinterpState;
use cligen::monthlies::{fouri2, lintrp, ryf2};
use cligen::par::{header, sta_dat, sta_name, sta_parms, ParError, ParFile, StaDatSelection};
use std::collections::HashMap;
use std::error::Error as _;
use std::path::{Path, PathBuf};

const STATIONS: [(&str, &str); 4] = [
    ("new-meadows-id", "new-meadows-id/id106388.par"),
    ("jeogla-au", "jeogla-au/ASN00057011.par"),
    ("mt-wilson-ca", "mt-wilson-ca/ca046006.par"),
    ("fish-springs-ut", "fish-springs-ut/ut422852.par"),
];
const INTERPS: [i32; 4] = [0, 1, 2, 3];

const FULL_F2_CASES: [(&str, &str, &str); 8] = [
    (
        "new-meadows-id-I2",
        "new-meadows-id",
        "new-meadows-id/id106388.par",
    ),
    ("jeogla-au-I2", "jeogla-au", "jeogla-au/ASN00057011.par"),
    (
        "mt-wilson-ca-observed-seed0",
        "mt-wilson-ca",
        "mt-wilson-ca/ca046006.par",
    ),
    (
        "mt-wilson-ca-observed-seed17",
        "mt-wilson-ca",
        "mt-wilson-ca/ca046006.par",
    ),
    (
        "fish-springs-ut-observed-padded-seed0",
        "fish-springs-ut",
        "fish-springs-ut/ut422852.par",
    ),
    (
        "fish-springs-ut-observed-padded-seed17",
        "fish-springs-ut",
        "fish-springs-ut/ut422852.par",
    ),
    (
        "fish-springs-ut-observed-truncated-seed0",
        "fish-springs-ut",
        "fish-springs-ut/ut422852.par",
    ),
    (
        "fish-springs-ut-observed-truncated-seed17",
        "fish-springs-ut",
        "fish-springs-ut/ut422852.par",
    ),
];

const FULL_MODE_CASES: [(&str, &str, &str); 4] = [
    (
        "new-meadows-id",
        "new-meadows-id",
        "new-meadows-id/id106388.par",
    ),
    ("jeogla-au", "jeogla-au", "jeogla-au/ASN00057011.par"),
    (
        "mt-wilson-ca-observed",
        "mt-wilson-ca",
        "mt-wilson-ca/ca046006.par",
    ),
    (
        "fish-springs-ut-observed-padded",
        "fish-springs-ut",
        "fish-springs-ut/ut422852.par",
    ),
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

/// One parsed 191-line snapshot (tap-schema.md record grammar).
struct Snapshot {
    stidd: String,
    interp: i32,
    o_mo: i32,
    ylt: u32,
    yll: u32,
    tp6: u32,
    years: i32,
    itype: i32,
    elev: i32,
    wgt: [u32; 3],
    site: [String; 3],
    timpkd: [u32; 13],
    rst: [[u32; 3]; 12],
    prw: [[u32; 2]; 12],
    monthly: [[u32; 12]; 12], // obmx obmn stdtx stdtm obsl stdsl cvs cvtx cvtm wi rh calm
    wvl: [[[u32; 12]; 4]; 16],
    dir: [[u32; 17]; 12],
    x_bar: [u32; 14],
    c: [[u32; 14]; 6],
    t: [[u32; 14]; 6],
    emv: [[u32; 14]; 14],
    pmt: [[u32; 14]; 13],
    pmv: [[u32; 14]; 13],
    xes: [[u32; 14]; 12],
    nst: i32,
    nstat: i32,
    igcode: i32,
}

fn hex(field: &str) -> u32 {
    u32::from_str_radix(field, 16).unwrap()
}

fn parse_snapshot(path: &Path) -> Snapshot {
    let data = std::fs::read_to_string(path).unwrap();
    let mut lines = data.lines();
    let mut snap = Snapshot {
        stidd: String::new(),
        interp: -1,
        o_mo: -1,
        ylt: 0,
        yll: 0,
        tp6: 0,
        years: -1,
        itype: -1,
        elev: -1,
        wgt: [0; 3],
        site: Default::default(),
        timpkd: [0; 13],
        rst: [[0; 3]; 12],
        prw: [[0; 2]; 12],
        monthly: [[0; 12]; 12],
        wvl: [[[0; 12]; 4]; 16],
        dir: [[0; 17]; 12],
        x_bar: [0; 14],
        c: [[0; 14]; 6],
        t: [[0; 14]; 6],
        emv: [[0; 14]; 14],
        pmt: [[0; 14]; 13],
        pmv: [[0; 14]; 13],
        xes: [[0; 14]; 12],
        nst: -1,
        nstat: -1,
        igcode: -1,
    };
    let mut seen: HashMap<&str, usize> = HashMap::new();
    let mut done = false;
    for line in lines.by_ref() {
        let mut it = line.split_whitespace();
        let tag = it.next().unwrap();
        match tag {
            "SNAP" | "I" | "A" | "Y" | "W" | "S" | "K" | "R" | "M" | "V" | "D" | "F" | "E"
            | "Q" | "U" | "Z" | "H" | "DONE" => *seen.entry(tag).or_insert(0) += 1,
            other => panic!("unknown snapshot tag {other:?} in {}", path.display()),
        }
        match tag {
            "SNAP" => {
                snap.stidd = line[line.find('|').unwrap() + 1..line.rfind('|').unwrap()].to_owned();
            }
            "I" => {
                snap.interp = it.next().unwrap().parse().unwrap();
                snap.o_mo = it.next().unwrap().parse().unwrap();
            }
            "A" => {
                snap.ylt = hex(it.next().unwrap());
                snap.yll = hex(it.next().unwrap());
                snap.tp6 = hex(it.next().unwrap());
            }
            "Y" => {
                snap.years = it.next().unwrap().parse().unwrap();
                snap.itype = it.next().unwrap().parse().unwrap();
                snap.elev = it.next().unwrap().parse().unwrap();
            }
            "W" => {
                for slot in &mut snap.wgt {
                    *slot = hex(it.next().unwrap());
                }
            }
            "S" => {
                let parts: Vec<&str> = line.split('|').collect();
                assert_eq!(parts.len(), 5, "S record shape");
                for (slot, part) in snap.site.iter_mut().zip(&parts[1..4]) {
                    *slot = (*part).to_owned();
                }
            }
            "K" => {
                let i: usize = it.next().unwrap().parse().unwrap();
                snap.timpkd[i] = hex(it.next().unwrap());
            }
            "R" => {
                let m: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for stat in 0..3 {
                    snap.rst[m][stat] = hex(it.next().unwrap());
                }
                for state in 0..2 {
                    snap.prw[m][state] = hex(it.next().unwrap());
                }
            }
            "M" => {
                let m: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for k in 0..12 {
                    snap.monthly[k][m] = hex(it.next().unwrap());
                }
            }
            "V" => {
                let i: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                let j: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for k in 0..12 {
                    snap.wvl[i][j][k] = hex(it.next().unwrap());
                }
            }
            "D" => {
                let m: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for j in 0..17 {
                    snap.dir[m][j] = hex(it.next().unwrap());
                }
            }
            "F" => {
                let p: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                snap.x_bar[p] = hex(it.next().unwrap());
                for j in 0..6 {
                    snap.c[j][p] = hex(it.next().unwrap());
                }
                for j in 0..6 {
                    snap.t[j][p] = hex(it.next().unwrap());
                }
            }
            "E" => {
                let p: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for i in 0..14 {
                    snap.emv[i][p] = hex(it.next().unwrap());
                }
            }
            "Q" => {
                let p: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for i in 0..13 {
                    snap.pmt[i][p] = hex(it.next().unwrap());
                }
            }
            "U" => {
                let p: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for i in 0..13 {
                    snap.pmv[i][p] = hex(it.next().unwrap());
                }
            }
            "Z" => {
                let p: usize = it.next().unwrap().parse::<usize>().unwrap() - 1;
                for i in 0..12 {
                    snap.xes[i][p] = hex(it.next().unwrap());
                }
            }
            "H" => {
                snap.nst = it.next().unwrap().parse().unwrap();
                snap.nstat = it.next().unwrap().parse().unwrap();
                snap.igcode = it.next().unwrap().parse().unwrap();
            }
            "DONE" => {
                done = true;
            }
            _ => unreachable!(),
        }
    }
    assert!(done, "{}: missing DONE marker", path.display());
    for (tag, count) in [
        ("K", 13),
        ("R", 12),
        ("M", 12),
        ("V", 64),
        ("D", 12),
        ("F", 14),
        ("E", 14),
        ("Q", 14),
        ("U", 14),
        ("Z", 14),
    ] {
        assert_eq!(seen[tag], count, "{}: {tag} record count", path.display());
    }
    snap
}

fn bits1(a: &[f32]) -> Vec<u32> {
    a.iter().map(|v| v.to_bits()).collect()
}

/// Load one fixture and run the already snapshot-gated `sta_parms`
/// setup for an evaluator's interpolation mode.
fn setup_interp(par_rel: &str, interp: i32) -> CinterpState {
    let bytes = std::fs::read(repo_root().join("fixtures").join(par_rel)).unwrap();
    let par = ParFile::parse(&bytes).unwrap();
    let mut bk7 = Cbk7State::default();
    let mut bk1 = Cbk1State::default();
    let mut bk9 = Cbk9State::default();
    let mut ci = CinterpState {
        interp,
        ..CinterpState::default()
    };
    let _ = sta_parms(&par, &mut bk7, &mut bk1, &mut bk9, &mut ci);
    ci
}

fn check_f2_stream(path: &Path, par_rel: &str, label: &str) -> usize {
    let ci = setup_interp(par_rel, 2);
    let data = std::fs::read_to_string(path).unwrap();
    let mut count = 0usize;
    for (record, line) in data.lines().enumerate() {
        let mut it = line.split_whitespace();
        let indpar: usize = it.next().unwrap().parse().unwrap();
        let ida: i32 = it.next().unwrap().parse().unwrap();
        let expected = hex(it.next().unwrap());
        assert!(it.next().is_none(), "{label}: f2 record shape");
        assert_eq!(
            fouri2(indpar, ida, &ci).to_bits(),
            expected,
            "{label}: fouri2 record {} indpar={indpar} ida={ida}",
            record + 1
        );
        count += 1;
    }
    count
}

fn check_y2_stream(path: &Path, par_rel: &str, label: &str) -> usize {
    let ci = setup_interp(par_rel, 3);
    let data = std::fs::read_to_string(path).unwrap();
    let mut count = 0usize;
    for (record, line) in data.lines().enumerate() {
        let mut it = line.split_whitespace();
        let mo: i32 = it.next().unwrap().parse().unwrap();
        let jd: i32 = it.next().unwrap().parse().unwrap();
        let ntd: i32 = it.next().unwrap().parse().unwrap();
        let indpar: usize = it.next().unwrap().parse().unwrap();
        let expected = hex(it.next().unwrap());
        assert!(it.next().is_none(), "{label}: y2 record shape");
        assert_eq!(
            ryf2(mo, jd, ntd, indpar, &ci).to_bits(),
            expected,
            "{label}: ryf2 record {} mo={mo} jd={jd} ntd={ntd} indpar={indpar}",
            record + 1
        );
        count += 1;
    }
    count
}

fn check_li_stream(path: &Path, par_rel: &str, label: &str) -> usize {
    let mut ci = setup_interp(par_rel, 1);
    let data = std::fs::read_to_string(path).unwrap();
    let mut count = 0usize;
    for (record, line) in data.lines().enumerate() {
        let mut it = line.split_whitespace();
        let mo: i32 = it.next().unwrap().parse().unwrap();
        let jd: i32 = it.next().unwrap().parse().unwrap();
        let ntd: i32 = it.next().unwrap().parse().unwrap();
        let expected_o_mo: i32 = it.next().unwrap().parse().unwrap();
        let expected_lf = hex(it.next().unwrap());
        let expected_rf = hex(it.next().unwrap());
        assert!(it.next().is_none(), "{label}: li record shape");
        lintrp(mo, jd, ntd, &mut ci);
        assert_eq!(
            (ci.o_mo, ci.lf.to_bits(), ci.rf.to_bits()),
            (expected_o_mo, expected_lf, expected_rf),
            "{label}: lintrp record {} mo={mo} jd={jd} ntd={ntd}",
            record + 1
        );
        count += 1;
    }
    count
}

/// Run parse + sta_parms for one (station, interp) and assert every
/// snapshot value bit-exactly.
fn check_combo(station: &str, par_rel: &str, interp: i32) {
    let root = repo_root();
    let combo = format!("{station}-I{interp}");
    let snap = parse_snapshot(
        &root
            .join("fixtures/taps/par")
            .join(&combo)
            .join("cligen_par.tap"),
    );
    let bytes = std::fs::read(root.join("fixtures").join(par_rel)).unwrap();
    let par = ParFile::parse(&bytes).unwrap_or_else(|e| panic!("{combo}: parse: {e}"));

    let mut bk7 = Cbk7State::default();
    let mut bk1 = Cbk1State::default();
    let mut bk9 = Cbk9State::default();
    let mut ci = CinterpState {
        interp,
        ..CinterpState::default()
    };
    let out = sta_parms(&par, &mut bk7, &mut bk1, &mut bk9, &mut ci);

    // sta_dat record-1 surface (H record).
    assert_eq!(par.stidd, snap.stidd, "{combo}: stidd");
    assert_eq!(
        (par.nst, par.nstat, par.igcode),
        (snap.nst, snap.nstat, snap.igcode),
        "{combo}: H record"
    );
    // Output arguments.
    assert_eq!(out.ylt.to_bits(), snap.ylt, "{combo}: ylt");
    assert_eq!(out.yll.to_bits(), snap.yll, "{combo}: yll");
    assert_eq!(out.tp6.to_bits(), snap.tp6, "{combo}: tp6");
    assert_eq!(
        (out.years, out.itype, out.elev),
        (snap.years, snap.itype, snap.elev),
        "{combo}: years/itype/elev"
    );
    assert_eq!(out.wgt.map(f32::to_bits), snap.wgt, "{combo}: wgt");
    assert_eq!(out.site, snap.site, "{combo}: site");
    assert_eq!(out.timpkd.map(f32::to_bits), snap.timpkd, "{combo}: timpkd");
    // cbk7/cbk9/cbk1 monthly state (R + M records).
    for m in 0..12 {
        assert_eq!(
            bits1(&bk7.rst[m]),
            snap.rst[m],
            "{combo}: rst month {}",
            m + 1
        );
        assert_eq!(
            bits1(&bk7.prw[m]),
            snap.prw[m],
            "{combo}: prw month {}",
            m + 1
        );
    }
    let monthly: [(&str, [f32; 12]); 12] = [
        ("obmx", bk7.obmx),
        ("obmn", bk7.obmn),
        ("stdtx", bk7.stdtx),
        ("stdtm", bk7.stdtm),
        ("obsl", bk7.obsl),
        ("stdsl", bk7.stdsl),
        ("cvs", bk7.cvs),
        ("cvtx", bk7.cvtx),
        ("cvtm", bk7.cvtm),
        ("wi", bk9.wi),
        ("rh", bk1.rh),
        ("calm", bk1.calm),
    ];
    for (k, (name, values)) in monthly.iter().enumerate() {
        assert_eq!(values.map(f32::to_bits), snap.monthly[k], "{combo}: {name}");
    }
    for i in 0..16 {
        for j in 0..4 {
            assert_eq!(
                bk1.wvl[i][j].map(f32::to_bits),
                snap.wvl[i][j],
                "{combo}: wvl({},{})",
                i + 1,
                j + 1
            );
        }
    }
    for m in 0..12 {
        assert_eq!(
            bk1.dir[m].map(f32::to_bits),
            snap.dir[m],
            "{combo}: dir month {}",
            m + 1
        );
    }
    // cinterp state (I + F + E/Q/U/Z records).
    assert_eq!(
        (ci.interp, ci.o_mo),
        (snap.interp, snap.o_mo),
        "{combo}: interp/o_mo"
    );
    assert_eq!(ci.x_bar.map(f32::to_bits), snap.x_bar, "{combo}: x_bar");
    for j in 0..6 {
        assert_eq!(
            ci.c[j].map(f32::to_bits),
            snap.c[j],
            "{combo}: c harmonic {}",
            j + 1
        );
        assert_eq!(
            ci.t[j].map(f32::to_bits),
            snap.t[j],
            "{combo}: t harmonic {}",
            j + 1
        );
    }
    for i in 0..14 {
        assert_eq!(
            ci.emv[i].map(f32::to_bits),
            snap.emv[i],
            "{combo}: emv slot {}",
            i + 1
        );
    }
    for i in 0..13 {
        assert_eq!(
            ci.pmt[i].map(f32::to_bits),
            snap.pmt[i],
            "{combo}: pmt slot {}",
            i + 1
        );
        assert_eq!(
            ci.pmv[i].map(f32::to_bits),
            snap.pmv[i],
            "{combo}: pmv slot {}",
            i + 1
        );
    }
    for i in 0..12 {
        assert_eq!(
            ci.xes[i].map(f32::to_bits),
            snap.xes[i],
            "{combo}: xes slot {}",
            i + 1
        );
    }
}

/// The full-matrix par-state identity gate: 4 stations × interp
/// {0,1,2,3} — every captured snapshot value bit-exact.
#[test]
fn sta_parms_matches_fortran_snapshots_full_matrix() {
    for (station, par_rel) in STATIONS {
        for interp in INTERPS {
            check_combo(station, par_rel, interp);
        }
    }
}

/// SPEC-PAR invariant 1: byte-preserving round-trip on all four
/// fixture `.par` files (adjudication in
/// par-roundtrip-adjudication.md).
#[test]
fn par_roundtrip_fixture_bytes() {
    let root = repo_root();
    for (_, par_rel) in STATIONS {
        let bytes = std::fs::read(root.join("fixtures").join(par_rel)).unwrap();
        let par = ParFile::parse(&bytes).unwrap();
        assert_eq!(par.to_bytes(), bytes, "{par_rel}: to_bytes(parse(b)) != b");
    }
}

/// Fail-closed surface: too few records and unparseable numerics are
/// typed errors, not inferred defaults.
#[test]
fn par_parse_fails_closed() {
    assert!(ParFile::parse(&[0xFF, 0xFE, 0x00]).is_err(), "non-text");
    assert!(
        matches!(ParFile::parse("é\n".as_bytes()), Err(ParError::NotText)),
        "non-ASCII fixed-column text"
    );
    assert!(
        ParFile::parse(b"only\nthree\nrecords\n").is_err(),
        "record count"
    );
    let root = repo_root();
    let mut text = String::from_utf8(
        std::fs::read(root.join("fixtures/new-meadows-id/id106388.par")).unwrap(),
    )
    .unwrap();
    // corrupt one numeric field on record 4 (MEAN P January)
    text = text.replacen("   .26", "  x.26", 1);
    assert!(ParFile::parse(text.as_bytes()).is_err(), "bad numeric");

    let fixture =
        std::fs::read_to_string(root.join("fixtures/new-meadows-id/id106388.par")).unwrap();
    let crlf = fixture.replace('\n', "\r\n");
    assert!(matches!(
        ParFile::parse(crlf.as_bytes()),
        Err(ParError::InvalidLineEnding)
    ));
    let tabbed = fixture.replacen("   .26", "  \t.26", 1);
    assert!(matches!(
        ParFile::parse(tabbed.as_bytes()),
        Err(ParError::Field { .. })
    ));
}

/// Committed first-1,000-record vectors for all four station states.
/// Each evaluator receives state produced by the snapshot-gated parser
/// and `sta_parms` path before its records are replayed.
#[test]
fn monthlies_evaluators_match_fortran_tap_samples() {
    let root = repo_root().join("fixtures/taps/par");
    let mut f2_total = 0usize;
    let mut y2_total = 0usize;
    let mut li_total = 0usize;
    for (station, par_rel) in STATIONS {
        let f2_label = format!("{station}-I2");
        f2_total += check_f2_stream(
            &root.join(&f2_label).join("f2-sample.tap"),
            par_rel,
            &f2_label,
        );
        let y2_label = format!("{station}-I3");
        y2_total += check_y2_stream(
            &root.join(&y2_label).join("y2-sample.tap"),
            par_rel,
            &y2_label,
        );
        let li_label = format!("{station}-I1");
        li_total += check_li_stream(
            &root.join(&li_label).join("li-sample.tap"),
            par_rel,
            &li_label,
        );
    }
    assert_eq!((f2_total, y2_total, li_total), (4_000, 4_000, 4_000));
}

/// Full local Stage S captures. These files are intentionally
/// gitignored; the manifest pins their provenance and hashes.
#[test]
#[ignore = "full monthlies replay against local par tap-runs capture (evidence gate)"]
fn full_monthlies_streams_bit_identical() {
    let tap_runs =
        repo_root().join("docs/work-packages/20260709-par-monthlies-port/artifacts/tap-runs");
    let mut f2_total = 0usize;
    let mut y2_total = 0usize;
    let mut li_total = 0usize;

    for (case, station, par_rel) in FULL_F2_CASES {
        f2_total += check_f2_stream(
            &tap_runs.join(case).join("cligen_f2.tap"),
            par_rel,
            &format!("{station}: {case}"),
        );
    }
    for (case_prefix, station, par_rel) in FULL_MODE_CASES {
        let y2_case = format!("{case_prefix}-I3");
        y2_total += check_y2_stream(
            &tap_runs.join(&y2_case).join("cligen_y2.tap"),
            par_rel,
            &format!("{station}: {y2_case}"),
        );
        let li_case = format!("{case_prefix}-I1");
        li_total += check_li_stream(
            &tap_runs.join(&li_case).join("cligen_li.tap"),
            par_rel,
            &format!("{station}: {li_case}"),
        );
    }

    println!("full monthlies identity: fouri2={f2_total} ryf2={y2_total} lintrp={li_total}");
    assert_eq!(f2_total, 380_436);
    assert_eq!(y2_total, 275_452);
    assert_eq!(li_total, 36_889);
}

#[test]
fn header_matches_fortran_banner() {
    let mut bytes = Vec::new();
    header(&mut bytes, 5.3230).unwrap();
    let expected = concat!(
        "\n\n",
        "  ********************************************************************\n",
        "  *                                                                  *\n",
        "  *              USDA - WATER EROSION PREDICTION PROJECT             *\n",
        "  *                 WEPP CLIMATE INPUT DATA GENERATOR                *\n",
        "  *                                                                  *\n",
        "  *                    CONTINUOUS SIMULATION AND                     *\n",
        "  *                       SINGLE STORM OPTIONS                       *\n",
        "  *                    with Command Line Options,                    *\n",
        "  *                        and Corrections to                        *\n",
        "  *                  Rainfall Intensity Calculations                 *\n",
        "  *                   and Random Number Generation.                  *\n",
        "  *                                                                  *\n",
        "  *                          VERSION 5.32300                         *\n",
        "  *                     Revised from VERSION 4.2                     *\n",
        "  *                          September 2024                          *\n",
        "  *                                                                  *\n",
        "  *           (Use -h or /h to list command line options.)           *\n",
        "  *                                                                  *\n",
        "  ********************************************************************\n",
        "\n\n",
    );
    assert_eq!(String::from_utf8(bytes).unwrap(), expected);
}

#[test]
fn sta_dat_single_file_routes_parse_and_distribution() {
    let root = repo_root();
    for (station, par_rel) in STATIONS {
        let path = root.join("fixtures").join(par_rel);
        let mut bk7 = Cbk7State::default();
        let mut bk1 = Cbk1State::default();
        let mut bk9 = Cbk9State::default();
        let mut ci = CinterpState {
            interp: 2,
            ..CinterpState::default()
        };
        let mut screen = Vec::new();
        let out = sta_dat(
            StaDatSelection::SingleFile(&path),
            5.3230,
            &mut screen,
            &mut bk7,
            &mut bk1,
            &mut bk9,
            &mut ci,
        )
        .unwrap_or_else(|e| panic!("{station}: sta_dat: {e}"));

        let snap = parse_snapshot(
            &root
                .join("fixtures/taps/par")
                .join(format!("{station}-I2"))
                .join("cligen_par.tap"),
        );
        assert_eq!(out.stidd, snap.stidd, "{station}: stidd");
        assert_eq!(
            (out.nst, out.nstat, out.igcode),
            (snap.nst, snap.nstat, snap.igcode),
            "{station}: header codes"
        );
        assert_eq!(out.parms.ylt.to_bits(), snap.ylt, "{station}: ylt");
        assert_eq!(out.parms.elev, snap.elev, "{station}: elev");
        assert_eq!(bk7.rst[0].map(f32::to_bits), snap.rst[0], "{station}: rst");
        assert_eq!(ci.x_bar.map(f32::to_bits), snap.x_bar, "{station}: fouri1");
        assert!(
            String::from_utf8(screen)
                .unwrap()
                .contains(path.to_str().unwrap()),
            "{station}: filename banner"
        );
    }
}

#[test]
fn sta_dat_deferred_paths_fail_closed() {
    let mut bk7 = Cbk7State::default();
    let mut bk1 = Cbk1State::default();
    let mut bk9 = Cbk9State::default();
    let mut ci = CinterpState::default();
    let mut screen = Vec::new();
    let missing = repo_root().join("fixtures/does-not-exist.par");
    assert!(matches!(
        sta_dat(
            StaDatSelection::SingleFile(&missing),
            5.3230,
            &mut screen,
            &mut bk7,
            &mut bk1,
            &mut bk9,
            &mut ci,
        ),
        Err(ParError::Io { .. })
    ));
    assert!(matches!(
        sta_dat(
            StaDatSelection::StateStationFile {
                path: &missing,
                state_code: 10,
                station_code: 6388,
            },
            5.3230,
            &mut screen,
            &mut bk7,
            &mut bk1,
            &mut bk9,
            &mut ci,
        ),
        Err(ParError::Unsupported { .. })
    ));
    assert!(matches!(
        sta_dat(
            StaDatSelection::Interactive,
            5.3230,
            &mut screen,
            &mut bk7,
            &mut bk1,
            &mut bk9,
            &mut ci,
        ),
        Err(ParError::InteractiveOnly { .. })
    ));
    assert!(matches!(sta_name(), Err(ParError::InteractiveOnly { .. })));
}

#[test]
fn par_error_variants_report_context_and_sources() {
    let io = ParError::Io {
        path: PathBuf::from("missing.par"),
        source: std::io::Error::new(std::io::ErrorKind::NotFound, "gone"),
    };
    assert_eq!(io.to_string(), "cannot read .par file missing.par: gone");
    assert!(io.source().is_some());

    let output = ParError::Output {
        source: std::io::Error::new(std::io::ErrorKind::BrokenPipe, "closed"),
    };
    assert_eq!(
        output.to_string(),
        "cannot write station intake output: closed"
    );
    assert!(output.source().is_some());

    let unsupported = ParError::Unsupported {
        surface: "state scan",
    };
    assert_eq!(
        unsupported.to_string(),
        "unsupported .par surface: state scan"
    );
    assert!(unsupported.source().is_none());

    let interactive = ParError::InteractiveOnly { surface: "prompts" };
    assert_eq!(
        interactive.to_string(),
        "interactive-only .par surface: prompts"
    );
    assert_eq!(ParError::NotText.to_string(), ".par file is not ASCII text");
    assert_eq!(
        ParError::InvalidLineEnding.to_string(),
        ".par file must use LF line endings"
    );
    assert_eq!(
        ParError::TooFewRecords { found: 2 }.to_string(),
        ".par has 2 records; CLIGEN reads 83"
    );
    assert_eq!(
        ParError::Field {
            record: 4,
            cols: (9, 14),
            text: " x.26".to_owned(),
        }
        .to_string(),
        ".par record 4 cols 9-14: unparseable field \" x.26\""
    );
}
