//! Origin-Class: CLIGEN-5.32.3-Public-Domain (behavioral surface)
//! Migration-Method: output-format adjudication (the §1.3 discipline
//!   applied to formatted output): gfortran's F/I edit-descriptor
//!   emission, pinned empirically against the reference runtime
//! Precision-Map: exact integer decimal arithmetic over the f32's
//!   binary value — no float rounding of any kind
//! Faithful-Acceptance: descriptor sweep bit-exact text equality
//!   (6.37M probe lines × 9 descriptors, format-rounding-adjudication
//!   artifact) + the 12-golden byte-parity gate
//!
//! Adjudicated semantics (Ran, 2026-07-09, pinned gfortran profile):
//! - F(w.d) rounds the **exact binary value** to `d` decimals with
//!   **ties-to-even** (verified on exact binary halves: 0.25→0.2,
//!   0.75→0.8, 2.5→"2.", 3.5→"4.", 0.0625→0.06).
//! - `d = 0` emits a trailing decimal point ("619.", "  0.").
//! - The sign of negative zero is preserved ("-0.0").
//! - If the rendering exceeds the width, the leading zero of "0." /
//!   "-0." is dropped ("-.00", "-.00017"); if it still exceeds, the
//!   field fills with asterisks.
//! - I(w) right-justifies; overflow fills with asterisks.

/// Fortran `Fw.d` output editing of an f32.
pub fn f_edit(v: f32, w: usize, d: usize) -> String {
    let bits = v.to_bits();
    let neg = bits & 0x8000_0000 != 0;
    let exp = ((bits >> 23) & 0xFF) as i32;
    let man = (bits & 0x007F_FFFF) as u128;
    // Exact value = m * 2^e.
    let (m, e): (u128, i32) = if exp == 0 {
        (man, -126 - 23)
    } else if exp == 0xFF {
        // Inf/NaN never reach the .cli surface; fail closed.
        panic!("f_edit: non-finite value");
    } else {
        (man | 0x0080_0000, exp - 127 - 23)
    };
    let pow10 = 10u128.pow(d as u32);
    // n = round_half_even(|v| * 10^d) in exact integer arithmetic.
    let n: u128 = if m == 0 {
        0
    } else if e >= 0 {
        m.checked_shl(e as u32)
            .and_then(|x| x.checked_mul(pow10))
            .unwrap_or(u128::MAX) // forces asterisk fill below
    } else {
        let shift = (-e) as u32;
        if shift >= 128 {
            0 // below any representable rounding threshold
        } else {
            let num = m * pow10;
            let den = 1u128 << shift;
            let q = num / den;
            let r = num % den;
            // ties-to-even on the exact remainder
            match (2 * r).cmp(&den) {
                std::cmp::Ordering::Greater => q + 1,
                std::cmp::Ordering::Equal => q + (q & 1),
                std::cmp::Ordering::Less => q,
            }
        }
    };
    let mut text = if d == 0 {
        format!("{n}.")
    } else {
        format!("{}.{:0width$}", n / pow10, n % pow10, width = d)
    };
    if neg {
        text.insert(0, '-');
    }
    if text.len() > w {
        // gfortran drops the leading zero of 0.xxx to fit the width.
        let dropped = if let Some(rest) = text.strip_prefix("0.") {
            format!(".{rest}")
        } else if let Some(rest) = text.strip_prefix("-0.") {
            format!("-.{rest}")
        } else {
            text.clone()
        };
        text = dropped;
    }
    if text.len() > w {
        return "*".repeat(w);
    }
    format!("{text:>w$}")
}

/// Fortran `Iw` output editing.
pub fn i_edit(v: i64, w: usize) -> String {
    let text = format!("{v}");
    if text.len() > w {
        return "*".repeat(w);
    }
    format!("{text:>w$}")
}
