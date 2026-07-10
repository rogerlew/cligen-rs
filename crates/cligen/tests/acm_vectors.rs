//! Bit-exact vectors captured from every ACM unit in the copied Stage C
//! Fortran tap build. These tests also adjudicate faithful-path f64 log,
//! sin, and exp through direct source-function results.

use cligen::acm::{
    cdfchi, cumchi, cumgam, dinvr, dstinv, dstzr, dzror, erf, erfc1, exparg, gam1, gamma, gratio,
    ipmpar, rexp, rlog, spmpar, AcmState, DinvrState, DzrorState,
};
use std::path::Path;

fn bits(field: &str) -> u64 {
    u64::from_str_radix(field, 16).unwrap()
}

fn logical(field: &str) -> bool {
    match field {
        "T" => true,
        "F" => false,
        _ => panic!("invalid Fortran logical {field}"),
    }
}

fn vector_lines() -> Vec<Vec<String>> {
    let path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/taps/stage-c-vectors.tap");
    std::fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|line| line.split_whitespace().map(str::to_owned).collect())
        .collect()
}

#[test]
fn acm_scalar_and_cumulative_units_match_fortran_bits() {
    let mut state = AcmState::default();
    let mut count = 0;
    for f in vector_lines() {
        match f[0].as_str() {
            "CDFCHI" => {
                let which = f[1].parse::<i32>().unwrap();
                let expected_status = f[2].parse::<i32>().unwrap();
                let input_p = f64::from_bits(bits(&f[3]));
                let input_q = f64::from_bits(bits(&f[4]));
                let input_x = f64::from_bits(bits(&f[5]));
                let input_df = f64::from_bits(bits(&f[6]));
                let got = cdfchi(which, input_p, input_q, input_x, input_df, &mut state);
                assert_eq!(got.status, expected_status, "{f:?}");
                assert_eq!(got.p.to_bits(), bits(&f[3]), "{f:?}");
                assert_eq!(got.q.to_bits(), bits(&f[4]), "{f:?}");
                assert_eq!(got.x.to_bits(), bits(&f[5]), "{f:?}");
                assert_eq!(got.df.to_bits(), bits(&f[6]), "{f:?}");
                assert_eq!(got.bound.to_bits(), bits(&f[7]), "{f:?}");
                count += 1;
            }
            "CUMCHI" | "CUMGAM" => {
                let x = f64::from_bits(bits(&f[2]));
                let a = f64::from_bits(bits(&f[3]));
                let got = if f[0] == "CUMCHI" {
                    cumchi(x, a)
                } else {
                    cumgam(x, a)
                };
                assert_eq!(got.0.to_bits(), bits(&f[4]), "{f:?}");
                assert_eq!(got.1.to_bits(), bits(&f[5]), "{f:?}");
                count += 1;
            }
            "ERF" => {
                let x = f64::from_bits(bits(&f[2]));
                assert_eq!(erf(x).to_bits(), bits(&f[3]), "{f:?}");
                count += 1;
            }
            "ERFC1" => {
                let ind = f[1].parse().unwrap();
                let x = f64::from_bits(bits(&f[2]));
                assert_eq!(erfc1(ind, x).to_bits(), bits(&f[3]), "{f:?}");
                count += 1;
            }
            "EXPARG" => {
                let l = f[1].parse().unwrap();
                assert_eq!(exparg(l).to_bits(), bits(&f[2]), "{f:?}");
                count += 1;
            }
            "GAM1" => {
                let a = f64::from_bits(bits(&f[2]));
                assert_eq!(gam1(a).to_bits(), bits(&f[3]), "{f:?}");
                count += 1;
            }
            "GAMMA" => {
                let a = f64::from_bits(bits(&f[2]));
                assert_eq!(gamma(a).to_bits(), bits(&f[3]), "{f:?}");
                count += 1;
            }
            "GRATIO" => {
                let ind = f[1].parse().unwrap();
                let a = f64::from_bits(bits(&f[2]));
                let x = f64::from_bits(bits(&f[3]));
                let got = gratio(a, x, ind);
                assert_eq!(got.0.to_bits(), bits(&f[4]), "{f:?}");
                assert_eq!(got.1.to_bits(), bits(&f[5]), "{f:?}");
                count += 1;
            }
            "IPMPAR" => {
                let i = f[1].parse::<i32>().unwrap();
                let expected = f[2].parse::<i32>().unwrap();
                assert_eq!(ipmpar(i), expected, "{f:?}");
                count += 1;
            }
            "REXP" | "RLOG" => {
                let x = f64::from_bits(bits(&f[2]));
                let got = if f[0] == "REXP" { rexp(x) } else { rlog(x) };
                assert_eq!(got.to_bits(), bits(&f[3]), "{f:?}");
                count += 1;
            }
            "SPMPAR" => {
                let i = f[1].parse().unwrap();
                assert_eq!(spmpar(i).to_bits(), bits(&f[2]), "{f:?}");
                count += 1;
            }
            _ => {}
        }
    }
    assert_eq!(count, 71);
}

#[test]
fn cdfchi_rejects_each_invalid_argument_with_source_bounds() {
    let cases: [(i32, f64, f64, f64, f64, i32, f64); 9] = [
        (0, 0.0, 0.0, 1.0, 1.0, -1, 1.0),
        (4, 0.0, 0.0, 1.0, 1.0, -1, 3.0),
        (2, -0.1, 1.1, 1.0, 1.0, -2, 0.0),
        (2, 1.1, -0.1, 1.0, 1.0, -2, 1.0),
        (2, 0.5, 0.0, 1.0, 1.0, -3, 0.0),
        (2, 0.5, 1.1, 1.0, 1.0, -3, 1.0),
        (1, 0.0, 0.0, -1.0, 1.0, -4, 0.0),
        (1, 0.0, 0.0, 1.0, 0.0, -5, 0.0),
        (2, 0.2, 0.7, 1.0, 1.0, 3, 1.0),
    ];

    for (which, p, q, x, df, status, bound) in cases {
        let got = cdfchi(which, p, q, x, df, &mut AcmState::default());
        assert_eq!(
            got.status, status,
            "which={which} p={p} q={q} x={x} df={df}"
        );
        assert_eq!(got.bound.to_bits(), bound.to_bits());
    }
}

#[test]
fn dinvr_reverse_communication_matches_fortran_trace() {
    assert_dinvr_trace("DINVR", 1.0);
    assert_dinvr_trace("DINVRL", 9.0);
}

fn assert_dinvr_trace(tag: &str, initial_x: f64) {
    let records: Vec<_> = vector_lines().into_iter().filter(|f| f[0] == tag).collect();
    let mut state = DinvrState::default();
    let mut zero = DzrorState::default();
    dstinv(0.0, 10.0, 0.5, 0.5, 5.0, 1e-50, 1e-8, &mut state);
    let mut status = 0;
    let mut x = initial_x;
    let mut fx: f64 = 0.0;
    for f in records {
        assert_eq!(fx.to_bits(), bits(&f[5]), "entry fx: {f:?}");
        let got = dinvr(status, x, fx, &mut state, &mut zero);
        assert_eq!(got.status, f[1].parse::<i32>().unwrap(), "{f:?}");
        assert_eq!(got.qleft, logical(&f[2]), "{f:?}");
        assert_eq!(got.qhi, logical(&f[3]), "{f:?}");
        assert_eq!(got.x.to_bits(), bits(&f[4]), "{f:?}");
        status = got.status;
        x = got.x;
        if status == 1 {
            fx = x * x - 2.0;
        }
    }
    assert_eq!(status, 0);
}

#[test]
fn dzror_reverse_communication_matches_fortran_trace() {
    let records: Vec<_> = vector_lines()
        .into_iter()
        .filter(|f| f[0] == "DZROR")
        .collect();
    let mut state = DzrorState::default();
    dstzr(0.0, 10.0, 1e-50, 1e-8, &mut state);
    let mut status = 0;
    let mut x: f64 = 0.0;
    let mut fx: f64 = 0.0;
    for f in records {
        assert_eq!(fx.to_bits(), bits(&f[5]), "entry fx: {f:?}");
        let got = dzror(status, x, fx, &mut state);
        assert_eq!(got.status, f[1].parse::<i32>().unwrap(), "{f:?}");
        assert_eq!(got.qleft, logical(&f[2]), "{f:?}");
        assert_eq!(got.qhi, logical(&f[3]), "{f:?}");
        assert_eq!(got.x.to_bits(), bits(&f[4]), "{f:?}");
        assert_eq!(got.xlo.to_bits(), bits(&f[6]), "{f:?}");
        assert_eq!(got.xhi.to_bits(), bits(&f[7]), "{f:?}");
        status = got.status;
        x = got.x;
        if status == 1 {
            fx = x * x - 2.0;
        }
    }
    assert_eq!(status, 0);
}
