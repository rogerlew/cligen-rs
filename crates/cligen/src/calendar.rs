//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:1817-1903 (jdt, jlt)
//! Precision-Map: integer arithmetic
//! Faithful-Acceptance: fixtures/taps/stage-c-vectors.tap (JDT/JLT)
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `nc` | `nc(13)` | non-leap days preceding each month | day |
//! | `nt` | `nt` | live call flag: 1 for leap, 0 for non-leap | flag |
//! | `ntd` | `ntd` | leap selector/year length; ordinal in single-storm mode | day |
//! | `jday` | `jday` | ordinal day within the year | day |
//! | `mo` | `mo` | 1-based month | month |
//! | `nday` | `nday` | 1-based day within the month | day |

/// Convert a month/day pair to an ordinal day — faithful `jdt`
/// (`cligen.f:1817-1842`).
///
/// # Panics
/// Panics for inputs outside the generator's month/day and leap-offset
/// domains rather than reproducing a Fortran out-of-bounds access.
pub fn jdt(nc: &[i32; 13], i: i32, m: i32, nt: i32) -> i32 {
    assert!((1..=12).contains(&m), "jdt: month outside 1..=12");
    assert!(i > 0, "jdt: day must be positive");
    assert!((0..=1).contains(&nt), "jdt: nt outside 0..=1");
    let month = (m - 1) as usize;
    let max_day = nc[month + 1] - nc[month] + if m == 2 { nt } else { 0 };
    assert!(i <= max_day, "jdt: day outside month");
    if m > 2 {
        nc[month] + nt + i
    } else {
        nc[month] + i
    }
}

/// Convert an ordinal day to a month/day pair — faithful `jlt`
/// (`cligen.f:1846-1900`).
///
/// # Panics
/// Panics unless `ntd` is positive and `jday` lies in the source-selected
/// 365/366-day calendar. In single-storm modes `ntd` is an ordinal day,
/// not a year length; only the exact value 366 selects a leap calendar.
pub fn jlt(ntd: i32, jday: i32) -> (i32, i32) {
    assert!(ntd > 0, "jlt: ntd must be positive");
    let days_in_calendar = if ntd == 366 { 366 } else { 365 };
    assert!(
        (1..=days_in_calendar).contains(&jday),
        "jlt: jday outside source-selected calendar"
    );
    // DATA nn/31,28,.../ and leap adjustment, cligen.f:1871-1881.
    let mut nn = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if ntd == 366 {
        nn[1] = 29;
    }
    let mut remaining = jday;
    for (month, days) in nn.into_iter().enumerate() {
        remaining -= days;
        if remaining <= 0 {
            return ((month + 1) as i32, remaining + days);
        }
    }
    unreachable!("validated ordinal day must resolve within twelve months")
}
