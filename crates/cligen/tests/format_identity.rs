//! Format-descriptor bit-exact text identity: `fortran_format::f_edit`
//! against reference-runtime formatted output (probe provenance in the
//! output-cli package's format-rounding-adjudication artifact).
//!
//! Committed sample: `fixtures/taps/format/fmt-pairs-sample.txt`
//! (first 20,000 probe lines = 180,000 fields). The full 6,371,240-line
//! sweep (57,341,160 fields) is a local evidence capture and runs
//! behind `#[ignore]` when present.

use cligen::fortran_format::f_edit;
use std::path::{Path, PathBuf};

const DESCS: [(usize, usize); 9] = [
    (4, 0),
    (4, 1),
    (4, 2),
    (5, 1),
    (5, 2),
    (6, 2),
    (7, 5),
    (8, 5),
    (9, 2),
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

/// Each probe line is `hex-bits|F4.0|F4.1|F4.2|F5.1|F5.2|F6.2|F7.5|F8.5|F9.2`
/// with a `-` prefix on the hex field for negated values.
fn check(path: &Path) -> (u64, u64) {
    let data = std::fs::read_to_string(path).unwrap();
    let (mut n, mut bad) = (0u64, 0u64);
    for line in data.lines() {
        let fields: Vec<&str> = line.split('|').collect();
        let (neg, hexpart) = if let Some(h) = fields[0].strip_prefix('-') {
            (true, h)
        } else {
            (false, fields[0])
        };
        let mut v = f32::from_bits(u32::from_str_radix(hexpart, 16).unwrap());
        if neg {
            v = -v;
        }
        for (i, (w, d)) in DESCS.iter().enumerate() {
            let got = f_edit(v, *w, *d);
            n += 1;
            if got != fields[i + 1] {
                if bad < 5 {
                    eprintln!(
                        "MISMATCH v={v:e} F{w}.{d}: got {got:?} want {:?}",
                        fields[i + 1]
                    );
                }
                bad += 1;
            }
        }
    }
    (n, bad)
}

#[test]
fn f_edit_matches_gfortran_sample() {
    let (n, bad) = check(&repo_root().join("fixtures/taps/format/fmt-pairs-sample.txt"));
    println!("sample: {n} fields, {bad} mismatches");
    assert_eq!(bad, 0);
    assert!(n >= 100_000);
}

#[test]
#[ignore = "full 57.3M-field sweep; point CLIGEN_FMT_SWEEP at a fmtprobe.f capture"]
fn f_edit_matches_gfortran_full_sweep() {
    let path = PathBuf::from(
        std::env::var("CLIGEN_FMT_SWEEP").expect("set CLIGEN_FMT_SWEEP to the probe capture path"),
    );
    assert!(path.exists(), "probe capture missing at CLIGEN_FMT_SWEEP");
    let (n, bad) = check(&path);
    println!("full sweep: {n} fields, {bad} mismatches");
    assert_eq!(bad, 0);
    assert!(n > 50_000_000);
}
