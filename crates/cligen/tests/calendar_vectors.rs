//! Fixture vectors captured from `jdt`/`jlt` in the copied Stage C tap
//! build. Provenance is recorded in the RNG/deviates work package.

use cligen::calendar::{jdt, jlt};
use std::path::Path;

const NC: [i32; 13] = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365];

#[test]
fn calendar_units_match_fortran_vectors() {
    let path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/taps/stage-c-vectors.tap");
    let data = std::fs::read_to_string(path).unwrap();
    let mut count = 0;
    for line in data.lines() {
        let fields: Vec<_> = line.split_whitespace().collect();
        match fields.first().copied() {
            Some("JDT") => {
                let nt = fields[1].parse().unwrap();
                let m = fields[2].parse().unwrap();
                let i = fields[3].parse().unwrap();
                let expected = fields[4].parse().unwrap();
                assert_eq!(jdt(&NC, i, m, nt), expected, "{line}");
                count += 1;
            }
            Some("JLT") => {
                let ntd = fields[1].parse().unwrap();
                let jday = fields[2].parse().unwrap();
                let mo = fields[3].parse().unwrap();
                let nday = fields[4].parse().unwrap();
                assert_eq!(jlt(ntd, jday), (mo, nday), "{line}");
                count += 1;
            }
            _ => {}
        }
    }
    assert_eq!(count, 804);
}

#[test]
#[should_panic(expected = "day outside month")]
fn jdt_fails_closed_on_invalid_month_day() {
    let _ = jdt(&NC, 29, 2, 0);
}
