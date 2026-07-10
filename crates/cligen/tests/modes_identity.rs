//! Cold-start faithful-mode identity: the ported `day_gen` drives
//! whole runs from block-data seeds (+ `-r` burn) + the ported
//! main-program setup + the real `.par`/`.prn` inputs — **zero
//! injected state** — and every daily row must equal the expectation
//! built from the captured cg/wg/sd streams. Year plans
//! `(iyear, ntd, nbt)` come from the captured B-lines (the `wxr_gen`
//! year loop is item 8).
//!
//! Per-day localization finer than the row lives in the five earlier
//! replay suites; this gate proves the end-to-end trajectory.

use cligen::cbk1::Cbk1State;
use cligen::cbk4::Cbk4State;
use cligen::cbk7::Cbk7State;
use cligen::cinterp::CinterpState;
use cligen::modes::{day_gen, generation_setup, DailyRow, DayGenExit, CLT};
use cligen::observed::{PrnDay, PrnError, PrnReader};
use cligen::par::{sta_parms, ParFile};
use cligen::storm::SingleStormParams;
use std::path::{Path, PathBuf};

/// (case, .par, .prn (observed), interp, iopt, burn)
#[allow(clippy::type_complexity)]
const CASES: [(&str, &str, Option<&str>, i32, i32, u32); 10] = [
    ("new-meadows-id-seed0", "new-meadows-id/id106388.par", None, 0, 5, 0),
    (
        "new-meadows-id-seed17",
        "new-meadows-id/id106388.par",
        None,
        0,
        5,
        17,
    ),
    ("jeogla-au-seed0", "jeogla-au/ASN00057011.par", None, 0, 5, 0),
    (
        "mt-wilson-ca-observed-seed0",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        2,
        6,
        0,
    ),
    (
        "fish-springs-ut-observed-padded-seed0",
        "fish-springs-ut/ut422852.par",
        Some("fixtures/fish-springs-ut/ws.prn"),
        2,
        6,
        0,
    ),
    (
        "fish-springs-ut-observed-truncated-seed0",
        "fish-springs-ut/ut422852.par",
        Some(
            "docs/work-packages/20260709-golden-fixture-harness/artifacts/inputs/fish-springs-ut/ws-truncated.prn",
        ),
        2,
        6,
        0,
    ),
    (
        "new-meadows-id-single-storm-seed0",
        "new-meadows-id/id106388.par",
        None,
        0,
        4,
        0,
    ),
    ("new-meadows-id-I1", "new-meadows-id/id106388.par", None, 1, 5, 0),
    ("new-meadows-id-I3", "new-meadows-id/id106388.par", None, 3, 5, 0),
    (
        "mt-wilson-ca-observed-I3",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        3,
        6,
        0,
    ),
];

/// Every local full capture: inputs plus the independently recorded
/// endpoint `(days, (year, month, day), day_gen exit)`.
#[allow(clippy::type_complexity)]
const FULL_CASES: [
    (
        &str,
        &str,
        Option<&str>,
        i32,
        i32,
        u32,
        usize,
        (i32, i32, i32),
        DayGenExit,
    );
    24
] = [
    (
        "fish-springs-ut-observed-padded-I0",
        "fish-springs-ut/ut422852.par",
        Some("fixtures/fish-springs-ut/ws.prn"),
        0,
        6,
        0,
        2_557,
        (2026, 12, 31),
        DayGenExit::Stop,
    ),
    (
        "fish-springs-ut-observed-padded-I1",
        "fish-springs-ut/ut422852.par",
        Some("fixtures/fish-springs-ut/ws.prn"),
        1,
        6,
        0,
        2_557,
        (2026, 12, 31),
        DayGenExit::Stop,
    ),
    (
        "fish-springs-ut-observed-padded-I3",
        "fish-springs-ut/ut422852.par",
        Some("fixtures/fish-springs-ut/ws.prn"),
        3,
        6,
        0,
        2_557,
        (2026, 12, 31),
        DayGenExit::Stop,
    ),
    (
        "fish-springs-ut-observed-padded-seed0",
        "fish-springs-ut/ut422852.par",
        Some("fixtures/fish-springs-ut/ws.prn"),
        2,
        6,
        0,
        2_557,
        (2026, 12, 31),
        DayGenExit::Stop,
    ),
    (
        "fish-springs-ut-observed-padded-seed17",
        "fish-springs-ut/ut422852.par",
        Some("fixtures/fish-springs-ut/ws.prn"),
        2,
        6,
        17,
        2_557,
        (2026, 12, 31),
        DayGenExit::Stop,
    ),
    (
        "fish-springs-ut-observed-truncated-seed0",
        "fish-springs-ut/ut422852.par",
        Some(
            "docs/work-packages/20260709-golden-fixture-harness/artifacts/inputs/fish-springs-ut/ws-truncated.prn",
        ),
        2,
        6,
        0,
        2_380,
        (2026, 7, 7),
        DayGenExit::Stop,
    ),
    (
        "fish-springs-ut-observed-truncated-seed17",
        "fish-springs-ut/ut422852.par",
        Some(
            "docs/work-packages/20260709-golden-fixture-harness/artifacts/inputs/fish-springs-ut/ws-truncated.prn",
        ),
        2,
        6,
        17,
        2_380,
        (2026, 7, 7),
        DayGenExit::Stop,
    ),
    (
        "jeogla-au-I1",
        "jeogla-au/ASN00057011.par",
        None,
        1,
        5,
        0,
        15_340,
        (42, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "jeogla-au-I2",
        "jeogla-au/ASN00057011.par",
        None,
        2,
        5,
        0,
        15_340,
        (42, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "jeogla-au-I3",
        "jeogla-au/ASN00057011.par",
        None,
        3,
        5,
        0,
        15_340,
        (42, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "jeogla-au-seed0",
        "jeogla-au/ASN00057011.par",
        None,
        0,
        5,
        0,
        15_340,
        (42, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "jeogla-au-seed17",
        "jeogla-au/ASN00057011.par",
        None,
        0,
        5,
        17,
        15_340,
        (42, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "mt-wilson-ca-observed-I0",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        0,
        6,
        0,
        7_670,
        (2010, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "mt-wilson-ca-observed-I1",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        1,
        6,
        0,
        7_670,
        (2010, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "mt-wilson-ca-observed-I3",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        3,
        6,
        0,
        7_670,
        (2010, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "mt-wilson-ca-observed-seed0",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        2,
        6,
        0,
        7_670,
        (2010, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "mt-wilson-ca-observed-seed17",
        "mt-wilson-ca/ca046006.par",
        Some("fixtures/mt-wilson-ca/ws.prn"),
        2,
        6,
        17,
        7_670,
        (2010, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-I1",
        "new-meadows-id/id106388.par",
        None,
        1,
        5,
        0,
        11_322,
        (31, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-I2",
        "new-meadows-id/id106388.par",
        None,
        2,
        5,
        0,
        11_322,
        (31, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-I3",
        "new-meadows-id/id106388.par",
        None,
        3,
        5,
        0,
        11_322,
        (31, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-seed0",
        "new-meadows-id/id106388.par",
        None,
        0,
        5,
        0,
        11_322,
        (31, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-seed17",
        "new-meadows-id/id106388.par",
        None,
        0,
        5,
        17,
        11_322,
        (31, 12, 31),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-single-storm-seed0",
        "new-meadows-id/id106388.par",
        None,
        0,
        4,
        0,
        1,
        (12, 6, 15),
        DayGenExit::YearComplete,
    ),
    (
        "new-meadows-id-single-storm-seed17",
        "new-meadows-id/id106388.par",
        None,
        0,
        4,
        17,
        1,
        (12, 6, 15),
        DayGenExit::YearComplete,
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

/// Per-day expectation assembled from the captured streams.
struct DayExpect {
    iyear: i32,
    ntd: i32,
    ida: i32,
    // From sd S at the unit-7 operand seam (day_gen:3175):
    // jd mo iyear + xr dur tpr xmav.
    jd: i32,
    mo: i32,
    s: [u32; 4],
    // From cg A before day_gen's 3110-3112 conversion:
    // r tmxg tmng tdp ra rmx (F-scale temps/tdp).
    a: [u32; 6],
    // From wg X at windg exit, before day_gen:3104:
    // wv th(rad) v9 j.
    wv: u32,
    th_rad: u32,
}

fn load_expectations(cg: &Path, sd: &Path, wg: &Path) -> Vec<DayExpect> {
    let cg_lines: Vec<Vec<String>> = std::fs::read_to_string(cg)
        .unwrap()
        .lines()
        .map(|l| l.split_whitespace().map(str::to_owned).collect())
        .collect();
    let sd_lines: Vec<Vec<String>> = std::fs::read_to_string(sd)
        .unwrap()
        .lines()
        .map(|l| l.split_whitespace().map(str::to_owned).collect())
        .collect();
    let wg_lines: Vec<Vec<String>> = std::fs::read_to_string(wg)
        .unwrap()
        .lines()
        .map(|l| l.split_whitespace().map(str::to_owned).collect())
        .collect();
    let days = cg_lines.len() / 5;
    assert_eq!(sd_lines.len() / 2, days);
    assert_eq!(wg_lines.len() / 2, days);
    (0..days)
        .map(|i| {
            let b = &cg_lines[i * 5];
            let a = &cg_lines[i * 5 + 4];
            let s = &sd_lines[i * 2 + 1];
            let x = &wg_lines[i * 2 + 1];
            DayExpect {
                iyear: b[4].parse().unwrap(),
                ntd: b[3].parse().unwrap(),
                ida: b[2].parse().unwrap(),
                jd: s[1].parse().unwrap(),
                mo: s[2].parse().unwrap(),
                s: std::array::from_fn(|k| hex(&s[k + 4])),
                a: std::array::from_fn(|k| hex(&a[k + 1])),
                wv: hex(&x[1]),
                th_rad: hex(&x[2]),
            }
        })
        .collect()
}

fn f2c(f_bits: u32) -> u32 {
    // day_gen:3110-3112 in f32.
    ((f32::from_bits(f_bits) - 32.0) * (5.0 / 9.0)).to_bits()
}

fn expected_row(e: &DayExpect) -> DailyRow {
    DailyRow {
        jd: e.jd,
        mo: e.mo,
        iyear: e.iyear,
        xr: f32::from_bits(e.s[0]),
        dur: f32::from_bits(e.s[1]),
        tpr: f32::from_bits(e.s[2]),
        xmav: f32::from_bits(e.s[3]),
        tmxg: f32::from_bits(f2c(e.a[1])),
        tmng: f32::from_bits(f2c(e.a[2])),
        radg: f32::from_bits(e.a[4]),
        wv: f32::from_bits(e.wv),
        // day_gen:3104 in f32.
        th: f32::from_bits(e.th_rad) * CLT,
        tdp: f32::from_bits(f2c(e.a[3])),
    }
}

fn rows_equal_bits(a: &DailyRow, b: &DailyRow) -> bool {
    (a.jd, a.mo, a.iyear) == (b.jd, b.mo, b.iyear)
        && a.xr.to_bits() == b.xr.to_bits()
        && a.dur.to_bits() == b.dur.to_bits()
        && a.tpr.to_bits() == b.tpr.to_bits()
        && a.xmav.to_bits() == b.xmav.to_bits()
        && a.tmxg.to_bits() == b.tmxg.to_bits()
        && a.tmng.to_bits() == b.tmng.to_bits()
        && a.radg.to_bits() == b.radg.to_bits()
        && a.wv.to_bits() == b.wv.to_bits()
        && a.th.to_bits() == b.th.to_bits()
        && a.tdp.to_bits() == b.tdp.to_bits()
}

struct RunSummary {
    checked: usize,
    last_day: Option<(i32, i32, i32)>,
    final_exit: DayGenExit,
}

#[allow(clippy::too_many_arguments)]
fn cold_start_run(
    case: &str,
    par_rel: &str,
    prn_rel: Option<&str>,
    interp: i32,
    iopt: i32,
    burn: u32,
    expect: &[DayExpect],
    max_days: Option<usize>,
) -> RunSummary {
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
    // Cold start: block-data seeds + the -r burn (cligen.f:723-737).
    bk7.burn(burn);
    let out = sta_parms(&par, &mut bk7, &mut bk1, &mut bk9, &mut ci);
    let bk4 = Cbk4State {
        iopt,
        ..Cbk4State::default()
    };
    let mut st = generation_setup(bk1, bk4, bk7, bk9, ci, out.ylt);
    let ss = if iopt == 4 {
        // golden harness single-storm.inp
        SingleStormParams {
            mo: 6,
            jd: 15,
            ibyear: 12,
            damt: 2.25,
            usdur: 6.0,
            ustpr: 0.4,
            uxmav: 1.5,
        }
    } else {
        SingleStormParams::default()
    };
    let mut prn = prn_rel.map(|rel| {
        PrnReader::new(&std::fs::read(root.join(rel)).unwrap()).expect("fixture .prn parses")
    });

    // Year plan from the captured B-lines.
    let mut checked = 0usize;
    let mut day_idx = 0usize;
    let mut last_day = None;
    let mut final_exit = DayGenExit::YearComplete;
    let limit = max_days.unwrap_or(expect.len()).min(expect.len());
    while day_idx < expect.len() {
        let e0 = &expect[day_idx];
        let (iyear, ntd) = (e0.iyear, e0.ntd);
        let nbt = e0.ida; // 1 for daily modes; the storm day for iopt 4
        let ntd1 = if iopt == 4 { e0.ida } else { 0 };
        st.ccl1.zero_year(); // wxr_gen:3768-3775
        let mut rows = Vec::new();
        let exit = day_gen(
            nbt,
            iyear,
            &out.timpkd,
            &ss,
            out.itype,
            ntd1,
            ntd,
            prn.as_mut(),
            &mut st,
            &mut rows,
        )
        .expect("fixture .prn records parse");
        final_exit = exit;
        let mut checked_this_call = 0usize;
        for row in &rows {
            if day_idx >= limit {
                assert!(
                    max_days.is_some(),
                    "{case}: emitted rows after captured endpoint"
                );
                break;
            }
            let want = expected_row(&expect[day_idx]);
            assert!(
                rows_equal_bits(row, &want),
                "{case}: day {}: row mismatch\n got {row:?}\nwant {want:?}",
                day_idx + 1
            );
            day_idx += 1;
            checked += 1;
            checked_this_call += 1;
            last_day = Some((row.iyear, row.mo, row.jd));
        }
        if max_days.is_none() && day_idx == expect.len() {
            assert_eq!(
                checked_this_call,
                rows.len(),
                "{case}: final day_gen call emitted rows after captured endpoint"
            );
        }
        if day_idx >= limit {
            break;
        }
        if exit == DayGenExit::Stop {
            break;
        }
    }
    if max_days.is_none() {
        assert_eq!(
            checked,
            expect.len(),
            "{case}: run ended before all captured days were reproduced"
        );
    }
    RunSummary {
        checked,
        last_day,
        final_exit,
    }
}

#[test]
fn prn_reader_pads_short_records_and_maps_blank_fields_to_zero() {
    let short = format!("{}12", "x".repeat(15));
    let blanks = format!("{}{}{}{}", "x".repeat(15), "     ", "  70 ", "     ");
    let input = format!("{short}\n{blanks}\n");
    let mut reader = PrnReader::new(input.as_bytes()).unwrap();
    assert_eq!(
        reader.next().unwrap(),
        Some(PrnDay {
            irida: 12,
            itmxg: 0,
            itmng: 0,
        })
    );
    assert_eq!(
        reader.next().unwrap(),
        Some(PrnDay {
            irida: 0,
            itmxg: 70,
            itmng: 0,
        })
    );
    assert_eq!(reader.next().unwrap(), None);
}

#[test]
fn prn_reader_rejects_nonnumeric_fields_and_non_ascii_input() {
    let input = b"               12   70   40   \n               12   bad! 40   \n";
    let mut reader = PrnReader::new(input).unwrap();
    assert!(reader.next().unwrap().is_some());
    let err = reader.next().unwrap_err();
    match &err {
        PrnError::Field { record, cols, text } => {
            assert_eq!((*record, *cols), (2, (21, 25)));
            assert_eq!(text, "bad! ");
        }
        PrnError::MissingStream | PrnError::NotText => panic!("expected a field error"),
    }
    assert_eq!(
        err.to_string(),
        ".prn record 2 cols 21-25: unparseable field \"bad! \""
    );

    let err = PrnReader::new("               12   70   40   é".as_bytes()).unwrap_err();
    assert!(matches!(err, PrnError::NotText));
    assert_eq!(err.to_string(), ".prn file is not ASCII text");
}

#[test]
fn prn_reader_treats_crlf_and_lf_records_identically() {
    let lf = "               55   72   40   \n               0    41   24   \n";
    let crlf = lf.replace('\n', "\r\n");
    let read_all = |bytes: &[u8]| {
        let mut reader = PrnReader::new(bytes).unwrap();
        let mut days = Vec::new();
        while let Some(day) = reader.next().unwrap() {
            days.push(day);
        }
        days
    };
    assert_eq!(read_all(lf.as_bytes()), read_all(crlf.as_bytes()));
}

#[test]
fn generation_setup_resets_nt_and_observed_mode_requires_prn() {
    let bk4 = Cbk4State {
        nt: 1,
        iopt: 6,
        ..Cbk4State::default()
    };
    let mut st = generation_setup(
        Cbk1State::default(),
        bk4,
        Cbk7State::default(),
        cligen::cbk9::Cbk9State::default(),
        CinterpState::default(),
        0.0,
    );
    assert_eq!(st.bk4.nt, 0, "main:881 unconditionally resets nt");

    let err = day_gen(
        1,
        1990,
        &[0.0; 13],
        &SingleStormParams::default(),
        1,
        0,
        365,
        None,
        &mut st,
        &mut Vec::new(),
    )
    .unwrap_err();
    assert_eq!(err, PrnError::MissingStream);
    assert_eq!(err.to_string(), "observed mode requires a .prn stream");
}

#[test]
fn cold_start_reproduces_first_year_from_samples() {
    let root = repo_root();
    let mut total = 0;
    for (case, par_rel, prn_rel, interp, iopt, burn) in CASES {
        let expect = load_expectations(
            &root
                .join("fixtures/taps/daily")
                .join(case)
                .join("cg-sample.tap"),
            &root
                .join("fixtures/taps/storm")
                .join(case)
                .join("sd-sample.tap"),
            &root
                .join("fixtures/taps/daily")
                .join(case)
                .join("wg-sample.tap"),
        );
        let n = expect.len().min(400);
        total +=
            cold_start_run(case, par_rel, prn_rel, interp, iopt, burn, &expect, Some(n)).checked;
    }
    assert!(total >= 3_000, "expected substantial coverage, got {total}");
}

#[test]
#[ignore = "cold-start full-run replay against local tap-runs captures (evidence gate)"]
fn cold_start_full_runs_bit_identical() {
    let root = repo_root();
    let daily = root.join("docs/work-packages/20260709-daily-core-port/artifacts/tap-runs");
    let storm = root.join("docs/work-packages/20260709-storm-machinery-port/artifacts/tap-runs");
    let mut total = 0;
    for (
        case,
        par_rel,
        prn_rel,
        interp,
        iopt,
        burn,
        expected_days,
        expected_last_day,
        expected_exit,
    ) in FULL_CASES
    {
        let expect = load_expectations(
            &daily.join(case).join("cligen_cg.tap"),
            &storm.join(case).join("cligen_sd.tap"),
            &daily.join(case).join("cligen_wg.tap"),
        );
        assert_eq!(expect.len(), expected_days, "{case}: capture day count");
        let captured_last = expect.last().unwrap();
        assert_eq!(
            (captured_last.iyear, captured_last.mo, captured_last.jd),
            expected_last_day,
            "{case}: capture endpoint"
        );
        let summary = cold_start_run(case, par_rel, prn_rel, interp, iopt, burn, &expect, None);
        assert_eq!(summary.checked, expected_days, "{case}: reproduced days");
        assert_eq!(
            summary.last_day,
            Some(expected_last_day),
            "{case}: reproduced endpoint"
        );
        assert_eq!(summary.final_exit, expected_exit, "{case}: final exit");
        total += summary.checked;
    }
    println!("cold-start full replay: days={total}");
    assert!(total > 180_000);
}
