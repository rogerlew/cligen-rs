//! Pinned f32 transcendentals for faithful mode.
//!
//! Origin-Class: ARM-optimized-routines (MIT) via glibc 2.28+
//! Migration-Method: algorithm transcription, behavior-verified against
//!   the reference build's runtime (glibc 2.39, x86-64 FMA ifunc
//!   variants) over the full tap capture — 26,402,148 dstn1 records,
//!   zero divergence required
//! Precision-Map: f64 internals, f32 boundary (as upstream)
//! Faithful-Acceptance: fixtures/taps/*/n1-sample.tap + full-stream
//!   `#[ignore]` test
//!
//! Why this module exists (ADR-0001 §4 anticipated it): the reference
//! binary links glibc's `logf`/`cosf`. The `libm` crate's f32
//! implementations (older musl lineage) diverge from glibc on 7.5% /
//! 1.3% of captured `dstn1` inputs respectively (1-ULP class), which
//! bit-identity acceptance cannot absorb. These transcriptions pin the
//! exact published algorithm glibc ships (the ARM optimized-routines
//! versions), making faithful mode platform-independent rather than
//! "whatever the host libm does". `sqrtf` needs no pinning (IEEE
//! correctly-rounded everywhere); f64 `pow`/`exp` stay on the `libm`
//! crate, which matched glibc bit-for-bit across the full `dstg`
//! replay.
//!
//! Multiply-add contraction: the running glibc's x86-64 ifunc variants
//! are FMA-compiled; `mul_add` is used here at each site GCC contracts,
//! and the choice is verified empirically against the capture (see
//! tap_identity tests).
//!
//! License note for review: algorithm and constants originate in ARM
//! optimized-routines (MIT); the same code is carried in glibc under
//! LGPL. This transcription attributes the MIT upstream. Flagged for
//! Stage R1 license review.
//!
//! Domain note: these are faithful-path functions for `dstn1`'s
//! argument domain (`rn1 ∈ (0,1)` exclusive from `randn`;
//! `|arg| < 2π + ε` for cosine). Inputs outside the domains the
//! generator can produce panic rather than replicating glibc's
//! special-case surface — fail-closed per the coding standard.

// ---------- logf (glibc sysdeps/ieee754/flt-32/e_logf.c) ----------

const LOGF_OFF: u32 = 0x3f33_0000;

/// `__logf_data.tab` — (invc, logc) pairs, 16 entries.
/// Hex-float originals in comments; stored as exact IEEE-754 bits.
const LOGF_TAB: [(u64, u64); 16] = [
    (0x3FF6_61EC_79F8_F3BE, 0xBFD5_7BF7_808C_AADE), // 0x1.661ec79f8f3bep+0, -0x1.57bf7808caadep-2
    (0x3FF5_71ED_4AAF_883D, 0xBFD2_BEF0_A7C0_6DDB), // 0x1.571ed4aaf883dp+0, -0x1.2bef0a7c06ddbp-2
    (0x3FF4_9539_F0F0_10B0, 0xBFD0_1EAE_7F51_3A67), // 0x1.49539f0f010bp+0,  -0x1.01eae7f513a67p-2
    (0x3FF3_C995_B0B8_0385, 0xBFCB_31D8_A682_24E9), // 0x1.3c995b0b80385p+0, -0x1.b31d8a68224e9p-3
    (0x3FF3_0D19_0C88_64A5, 0xBFC6_574F_0AC0_7758), // 0x1.30d190c8864a5p+0, -0x1.6574f0ac07758p-3
    (0x3FF2_5E22_7B0B_8EA0, 0xBFC1_AA2B_C79C_8100), // 0x1.25e227b0b8eap+0,  -0x1.1aa2bc79c81p-3
    (0x3FF1_BB4A_4A1A_343F, 0xBFBA_4E76_CE8C_0E5E), // 0x1.1bb4a4a1a343fp+0, -0x1.a4e76ce8c0e5ep-4
    (0x3FF1_2358_F08A_E5BA, 0xBFB1_973C_5A61_1CCC), // 0x1.12358f08ae5bap+0, -0x1.1973c5a611cccp-4
    (0x3FF0_953F_4199_00A7, 0xBFA2_52F4_38E1_0C1E), // 0x1.0953f419900a7p+0, -0x1.252f438e10c1ep-5
    (0x3FF0_0000_0000_0000, 0x0000_0000_0000_0000), // 0x1p+0, 0x0p+0
    (0x3FEE_608C_FD9A_47AC, 0x3FAA_A5AA_5DF2_5984), // 0x1.e608cfd9a47acp-1, 0x1.aa5aa5df25984p-5
    (0x3FEC_A4B3_1F02_6AA0, 0x3FBC_5E53_AA36_2EB4), // 0x1.ca4b31f026aap-1,  0x1.c5e53aa362eb4p-4
    (0x3FEB_2036_576A_FCE6, 0x3FC5_26E5_7720_DB08), // 0x1.b2036576afce6p-1, 0x1.526e57720db08p-3
    (0x3FE9_C2D1_63A1_AA2D, 0x3FCB_C286_0D22_4770), // 0x1.9c2d163a1aa2dp-1, 0x1.bc2860d22477p-3
    (0x3FE8_86E6_0378_41ED, 0x3FD1_058B_C8A0_7EE1), // 0x1.886e6037841edp-1, 0x1.1058bc8a07ee1p-2
    (0x3FE7_67DC_F553_4862, 0x3FD4_0430_57B6_EE09), // 0x1.767dcf5534862p-1, 0x1.4043057b6ee09p-2
];

/// `ln2 = 0x1.62e42fefa39efp-1`.
const LOGF_LN2: u64 = 0x3FE6_2E42_FEFA_39EF;

/// `poly = { -0x1.00ea348b88334p-2, 0x1.5575b0be00b6ap-2, -0x1.ffffef20a4123p-2 }`.
const LOGF_POLY: [u64; 3] = [
    0xBFD0_0EA3_48B8_8334,
    0x3FD5_575B_0BE0_0B6A,
    0xBFDF_FFFE_F20A_4123,
];

/// Faithful `logf` — glibc/ARM single-precision log.
///
/// # Panics
/// On inputs outside the positive-normal domain (the generator cannot
/// produce them; fail-closed rather than replicating special cases).
pub fn logf_pinned(x: f32) -> f32 {
    let ix = x.to_bits();
    if ix == 0x3f80_0000 {
        return 0.0; // WANT_ROUNDING shortcut: log(1) = +0
    }
    assert!(
        ix.wrapping_sub(0x0080_0000) < 0x7f80_0000 - 0x0080_0000,
        "logf_pinned: input outside positive-normal faithful domain"
    );
    let tmp = ix.wrapping_sub(LOGF_OFF);
    let i = ((tmp >> 19) % 16) as usize; // 23 - LOGF_TABLE_BITS(4)
    let k = (tmp as i32) >> 23;
    let iz = ix.wrapping_sub(tmp & (0x1ff << 23));
    let invc = f64::from_bits(LOGF_TAB[i].0);
    let logc = f64::from_bits(LOGF_TAB[i].1);
    let z = f32::from_bits(iz) as f64;

    // r = z * invc - 1;  y0 = logc + k * Ln2  (FMA-contracted as built)
    let r = z.mul_add(invc, -1.0);
    let y0 = (k as f64).mul_add(f64::from_bits(LOGF_LN2), logc);

    let r2 = r * r;
    // y = A[1]*r + A[2]; y = A[0]*r2 + y; y = y*r2 + (y0 + r)
    let mut y = f64::from_bits(LOGF_POLY[1]).mul_add(r, f64::from_bits(LOGF_POLY[2]));
    y = f64::from_bits(LOGF_POLY[0]).mul_add(r2, y);
    y = y.mul_add(r2, y0 + r);
    y as f32
}

// ------ cosf (glibc sysdeps/ieee754/flt-32/s_cosf.c + s_sincosf.h) ------

/// One `sincos_t` entry: sign[4], hpi_inv (×2^24), hpi, c0..c4, s1..s3.
struct SinCos {
    sign: [f64; 4],
    hpi_inv: f64,
    hpi: f64,
    c0: f64,
    c1: f64,
    c2: f64,
    c3: f64,
    c4: f64,
    s1: f64,
    s2: f64,
    s3: f64,
}

/// `__sincosf_table` — entry 1 negates the cosine polynomial.
fn sincos_table(second: bool) -> SinCos {
    let neg = if second { -1.0 } else { 1.0 };
    SinCos {
        sign: [1.0, -1.0, -1.0, 1.0],
        hpi_inv: f64::from_bits(0x4164_5F30_6DC9_C883), // 0x1.45F306DC9C883p+23
        hpi: f64::from_bits(0x3FF9_21FB_5444_2D18),     // 0x1.921FB54442D18p0
        c0: neg * f64::from_bits(0x3FF0_0000_0000_0000), // ±0x1p0
        c1: neg * f64::from_bits(0xBFDF_FFFF_FD0C_621C), // ∓0x1.ffffffd0c621cp-2
        c2: neg * f64::from_bits(0x3FA5_5553_E106_8F19), // ±0x1.55553e1068f19p-5
        c3: neg * f64::from_bits(0xBF56_C087_E89A_359D), // ∓0x1.6c087e89a359dp-10
        c4: neg * f64::from_bits(0x3EF9_9343_027B_F8C3), // ±0x1.99343027bf8c3p-16
        s1: f64::from_bits(0xBFC5_5554_5995_A603),      // -0x1.555545995a603p-3
        s2: f64::from_bits(0x3F81_1076_0523_0BC4),      // 0x1.1107605230bc4p-7
        s3: f64::from_bits(0xBF29_94EB_3774_CF24),      // -0x1.994eb3774cf24p-13
    }
}

/// Top 12 bits of the float representation, sign cleared.
#[inline]
fn abstop12(x: f32) -> u32 {
    (x.to_bits() >> 20) & 0x7ff
}

/// `reduce_fast` (non-TOINT path, as glibc x86-64 builds it): modulo
/// into [-π/4, π/4] with the quadrant in the return.
#[inline]
fn reduce_fast(x: f64, p: &SinCos) -> (f64, i32) {
    let r = x * p.hpi_inv;
    let n = ((r as i32).wrapping_add(0x0080_0000)) >> 24;
    (x - (n as f64) * p.hpi, n)
}

/// `sinf_poly`: sine polynomial for even `n`, cosine for odd.
#[inline]
fn sinf_poly(x: f64, x2: f64, p: &SinCos, n: i32) -> f32 {
    if n & 1 == 0 {
        let x3 = x * x2;
        // s1 = s2 + x2*s3; s = x + x3*s1_poly; result = s + x7*s1
        let s1 = p.s3.mul_add(x2, p.s2);
        let x7 = x3 * x2;
        let s = p.s1.mul_add(x3, x);
        s1.mul_add(x7, s) as f32
    } else {
        let x4 = x2 * x2;
        let c2 = p.c4.mul_add(x2, p.c3);
        let c1 = p.c1.mul_add(x2, p.c0);
        let x6 = x4 * x2;
        let c = p.c2.mul_add(x4, c1);
        c2.mul_add(x6, c) as f32
    }
}

/// Faithful `cosf` — glibc/ARM single-precision cosine for the
/// generator's argument domain (`|x| < 120`; `dstn1` supplies
/// `6.283185·rn2 ∈ (0, 2π)`).
///
/// # Panics
/// Outside `|x| < 120` (the `reduce_large` branch is not needed by any
/// generator path and is deliberately not carried).
pub fn cosf_pinned(y: f32) -> f32 {
    let x = y as f64;
    let p = sincos_table(false);
    let at = abstop12(y);
    if at < abstop12(f32::from_bits(0x3F49_0FDB)) {
        // |y| < π/4
        if at < abstop12(f32::from_bits(0x3980_0000)) {
            return 1.0; // |y| < 2^-12
        }
        sinf_poly(x, x * x, &p, 1)
    } else {
        assert!(
            at < abstop12(120.0f32),
            "cosf_pinned: |x| >= 120 outside faithful domain"
        );
        let (xr, n) = reduce_fast(x, &p);
        let s = p.sign[(n & 3) as usize];
        let p = sincos_table(n & 2 != 0);
        sinf_poly(xr * s, xr * xr, &p, n ^ 1)
    }
}
