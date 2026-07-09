//! Pinned transcendentals for faithful mode.
//!
//! Origin-Class: ARM-optimized-routines
//!   (MIT OR Apache-2.0 WITH LLVM-exception)
//! Copyright: 2017-2025 Arm Limited (`logf`, `cosf`, `exp` families)
//! Migration-Method: algorithm transcription, behavior-verified against
//!   the reference build's runtime (glibc 2.39, x86-64 FMA ifunc
//!   variants) over the full tap capture — 26,402,148 dstn1 records,
//!   plus Stage C direct ACM vectors, zero divergence required
//! Precision-Map: `logf`/`cosf` use f64 internals with f32 boundaries;
//!   `exp` is binary64 throughout (as upstream)
//! Faithful-Acceptance: fixtures/taps/*/n1-sample.tap + full-stream
//!   `#[ignore]` test; fixtures/taps/stage-c-vectors.tap for `exp`
//!
//! Why this module exists (ADR-0001 §4 anticipated it): the reference
//! binary links glibc's `logf`/`cosf`. The `libm` crate's f32
//! implementations (older musl lineage) diverge from glibc on 7.5% /
//! 1.3% of captured `dstn1` inputs respectively (1-ULP class), which
//! bit-identity acceptance cannot absorb. These transcriptions pin the
//! exact published algorithm glibc ships (the ARM optimized-routines
//! versions), making faithful mode platform-independent rather than
//! "whatever the host libm does". `sqrtf` needs no pinning (IEEE
//! correctly-rounded everywhere). f64 `pow` and the `dstg`-domain `exp`
//! stay on the `libm` crate, which matched the reference through the full
//! `dstg` replay. ACM's wider `exp` input surface exposed a one-ULP mismatch
//! at `exp(-10)`, so that path uses the pinned scalar ARM implementation.
//!
//! Multiply-add contraction: the running glibc's x86-64 ifunc variants
//! are FMA-compiled; `mul_add` is used here at each site GCC contracts,
//! and the choice is verified empirically against the capture (see
//! tap_identity tests).
//!
//! License provenance was resolved in Stage R1 against the ARM upstream,
//! not the LGPL glibc carrier. Exact upstream commit/file hashes and the
//! complete upstream dual license are recorded in the package artifacts.
//!
//! Domain note: `logf_pinned`/`cosf_pinned` cover `dstn1`'s argument
//! domain (`rn1 ∈ (0,1)` exclusive from `randn`; `|arg| < 2π + ε` for
//! cosine) and fail closed outside it. `exp_pinned` retains the upstream
//! scalar implementation's finite, infinity, and NaN handling because ACM
//! reaches a broader binary64 surface.

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

// ---------- exp (ARM optimized-routines math/exp.c, N=128) ----------

// `__exp_data.tab`, N=128. Each pair is (tail bits, adjusted scale bits).
// ARM optimized-routines commit captured for Stage C provenance; constants
// are the exact published hex values, stored as integers because Rust has no
// stable hexadecimal-float literal syntax.
const EXP_TAB: [u64; 256] = [
    0x0,
    0x3ff0000000000000,
    0x3c9b3b4f1a88bf6e,
    0x3feff63da9fb3335,
    0xbc7160139cd8dc5d,
    0x3fefec9a3e778061,
    0xbc905e7a108766d1,
    0x3fefe315e86e7f85,
    0x3c8cd2523567f613,
    0x3fefd9b0d3158574,
    0xbc8bce8023f98efa,
    0x3fefd06b29ddf6de,
    0x3c60f74e61e6c861,
    0x3fefc74518759bc8,
    0x3c90a3e45b33f399,
    0x3fefbe3ecac6f383,
    0x3c979aa65d837b6d,
    0x3fefb5586cf9890f,
    0x3c8eb51a92fdeffc,
    0x3fefac922b7247f7,
    0x3c3ebe3d702f9cd1,
    0x3fefa3ec32d3d1a2,
    0xbc6a033489906e0b,
    0x3fef9b66affed31b,
    0xbc9556522a2fbd0e,
    0x3fef9301d0125b51,
    0xbc5080ef8c4eea55,
    0x3fef8abdc06c31cc,
    0xbc91c923b9d5f416,
    0x3fef829aaea92de0,
    0x3c80d3e3e95c55af,
    0x3fef7a98c8a58e51,
    0xbc801b15eaa59348,
    0x3fef72b83c7d517b,
    0xbc8f1ff055de323d,
    0x3fef6af9388c8dea,
    0x3c8b898c3f1353bf,
    0x3fef635beb6fcb75,
    0xbc96d99c7611eb26,
    0x3fef5be084045cd4,
    0x3c9aecf73e3a2f60,
    0x3fef54873168b9aa,
    0xbc8fe782cb86389d,
    0x3fef4d5022fcd91d,
    0x3c8a6f4144a6c38d,
    0x3fef463b88628cd6,
    0x3c807a05b0e4047d,
    0x3fef3f49917ddc96,
    0x3c968efde3a8a894,
    0x3fef387a6e756238,
    0x3c875e18f274487d,
    0x3fef31ce4fb2a63f,
    0x3c80472b981fe7f2,
    0x3fef2b4565e27cdd,
    0xbc96b87b3f71085e,
    0x3fef24dfe1f56381,
    0x3c82f7e16d09ab31,
    0x3fef1e9df51fdee1,
    0xbc3d219b1a6fbffa,
    0x3fef187fd0dad990,
    0x3c8b3782720c0ab4,
    0x3fef1285a6e4030b,
    0x3c6e149289cecb8f,
    0x3fef0cafa93e2f56,
    0x3c834d754db0abb6,
    0x3fef06fe0a31b715,
    0x3c864201e2ac744c,
    0x3fef0170fc4cd831,
    0x3c8fdd395dd3f84a,
    0x3feefc08b26416ff,
    0xbc86a3803b8e5b04,
    0x3feef6c55f929ff1,
    0xbc924aedcc4b5068,
    0x3feef1a7373aa9cb,
    0xbc9907f81b512d8e,
    0x3feeecae6d05d866,
    0xbc71d1e83e9436d2,
    0x3feee7db34e59ff7,
    0xbc991919b3ce1b15,
    0x3feee32dc313a8e5,
    0x3c859f48a72a4c6d,
    0x3feedea64c123422,
    0xbc9312607a28698a,
    0x3feeda4504ac801c,
    0xbc58a78f4817895b,
    0x3feed60a21f72e2a,
    0xbc7c2c9b67499a1b,
    0x3feed1f5d950a897,
    0x3c4363ed60c2ac11,
    0x3feece086061892d,
    0x3c9666093b0664ef,
    0x3feeca41ed1d0057,
    0x3c6ecce1daa10379,
    0x3feec6a2b5c13cd0,
    0x3c93ff8e3f0f1230,
    0x3feec32af0d7d3de,
    0x3c7690cebb7aafb0,
    0x3feebfdad5362a27,
    0x3c931dbdeb54e077,
    0x3feebcb299fddd0d,
    0xbc8f94340071a38e,
    0x3feeb9b2769d2ca7,
    0xbc87deccdc93a349,
    0x3feeb6daa2cf6642,
    0xbc78dec6bd0f385f,
    0x3feeb42b569d4f82,
    0xbc861246ec7b5cf6,
    0x3feeb1a4ca5d920f,
    0x3c93350518fdd78e,
    0x3feeaf4736b527da,
    0x3c7b98b72f8a9b05,
    0x3feead12d497c7fd,
    0x3c9063e1e21c5409,
    0x3feeab07dd485429,
    0x3c34c7855019c6ea,
    0x3feea9268a5946b7,
    0x3c9432e62b64c035,
    0x3feea76f15ad2148,
    0xbc8ce44a6199769f,
    0x3feea5e1b976dc09,
    0xbc8c33c53bef4da8,
    0x3feea47eb03a5585,
    0xbc845378892be9ae,
    0x3feea34634ccc320,
    0xbc93cedd78565858,
    0x3feea23882552225,
    0x3c5710aa807e1964,
    0x3feea155d44ca973,
    0xbc93b3efbf5e2228,
    0x3feea09e667f3bcd,
    0xbc6a12ad8734b982,
    0x3feea012750bdabf,
    0xbc6367efb86da9ee,
    0x3fee9fb23c651a2f,
    0xbc80dc3d54e08851,
    0x3fee9f7df9519484,
    0xbc781f647e5a3ecf,
    0x3fee9f75e8ec5f74,
    0xbc86ee4ac08b7db0,
    0x3fee9f9a48a58174,
    0xbc8619321e55e68a,
    0x3fee9feb564267c9,
    0x3c909ccb5e09d4d3,
    0x3feea0694fde5d3f,
    0xbc7b32dcb94da51d,
    0x3feea11473eb0187,
    0x3c94ecfd5467c06b,
    0x3feea1ed0130c132,
    0x3c65ebe1abd66c55,
    0x3feea2f336cf4e62,
    0xbc88a1c52fb3cf42,
    0x3feea427543e1a12,
    0xbc9369b6f13b3734,
    0x3feea589994cce13,
    0xbc805e843a19ff1e,
    0x3feea71a4623c7ad,
    0xbc94d450d872576e,
    0x3feea8d99b4492ed,
    0x3c90ad675b0e8a00,
    0x3feeaac7d98a6699,
    0x3c8db72fc1f0eab4,
    0x3feeace5422aa0db,
    0xbc65b6609cc5e7ff,
    0x3feeaf3216b5448c,
    0x3c7bf68359f35f44,
    0x3feeb1ae99157736,
    0xbc93091fa71e3d83,
    0x3feeb45b0b91ffc6,
    0xbc5da9b88b6c1e29,
    0x3feeb737b0cdc5e5,
    0xbc6c23f97c90b959,
    0x3feeba44cbc8520f,
    0xbc92434322f4f9aa,
    0x3feebd829fde4e50,
    0xbc85ca6cd7668e4b,
    0x3feec0f170ca07ba,
    0x3c71affc2b91ce27,
    0x3feec49182a3f090,
    0x3c6dd235e10a73bb,
    0x3feec86319e32323,
    0xbc87c50422622263,
    0x3feecc667b5de565,
    0x3c8b1c86e3e231d5,
    0x3feed09bec4a2d33,
    0xbc91bbd1d3bcbb15,
    0x3feed503b23e255d,
    0x3c90cc319cee31d2,
    0x3feed99e1330b358,
    0x3c8469846e735ab3,
    0x3feede6b5579fdbf,
    0xbc82dfcd978e9db4,
    0x3feee36bbfd3f37a,
    0x3c8c1a7792cb3387,
    0x3feee89f995ad3ad,
    0xbc907b8f4ad1d9fa,
    0x3feeee07298db666,
    0xbc55c3d956dcaeba,
    0x3feef3a2b84f15fb,
    0xbc90a40e3da6f640,
    0x3feef9728de5593a,
    0xbc68d6f438ad9334,
    0x3feeff76f2fb5e47,
    0xbc91eee26b588a35,
    0x3fef05b030a1064a,
    0x3c74ffd70a5fddcd,
    0x3fef0c1e904bc1d2,
    0xbc91bdfbfa9298ac,
    0x3fef12c25bd71e09,
    0x3c736eae30af0cb3,
    0x3fef199bdd85529c,
    0x3c8ee3325c9ffd94,
    0x3fef20ab5fffd07a,
    0x3c84e08fd10959ac,
    0x3fef27f12e57d14b,
    0x3c63cdaf384e1a67,
    0x3fef2f6d9406e7b5,
    0x3c676b2c6c921968,
    0x3fef3720dcef9069,
    0xbc808a1883ccb5d2,
    0x3fef3f0b555dc3fa,
    0xbc8fad5d3ffffa6f,
    0x3fef472d4a07897c,
    0xbc900dae3875a949,
    0x3fef4f87080d89f2,
    0x3c74a385a63d07a7,
    0x3fef5818dcfba487,
    0xbc82919e2040220f,
    0x3fef60e316c98398,
    0x3c8e5a50d5c192ac,
    0x3fef69e603db3285,
    0x3c843a59ac016b4b,
    0x3fef7321f301b460,
    0xbc82d52107b43e1f,
    0x3fef7c97337b9b5f,
    0xbc892ab93b470dc9,
    0x3fef864614f5a129,
    0x3c74b604603a88d3,
    0x3fef902ee78b3ff6,
    0x3c83c5ec519d7271,
    0x3fef9a51fbc74c83,
    0xbc8ff7128fd391f0,
    0x3fefa4afa2a490da,
    0xbc8dae98e223747d,
    0x3fefaf482d8e67f1,
    0x3c8ec3bc41aa2008,
    0x3fefba1bee615a27,
    0x3c842b94c3a9eb32,
    0x3fefc52b376bba97,
    0x3c8a64a931d185ee,
    0x3fefd0765b6e4540,
    0xbc8e37bae43be3ed,
    0x3fefdbfdad9cbe14,
    0x3c77893b4d91cd9d,
    0x3fefe7c1819e90d8,
    0x3c5305c14160cc89,
    0x3feff3c22b8f71f1,
];

// Retain `lo = 1-hi+y+lo` from ARM exp.c's subnormal correction.
#[allow(clippy::assign_op_pattern)]
fn exp_special_case(tmp: f64, mut sbits: u64, ki: u64) -> f64 {
    if ki & 0x8000_0000 == 0 {
        sbits = sbits.wrapping_sub(1009u64 << 52);
        let scale = f64::from_bits(sbits);
        return f64::from_bits(0x7f00_0000_0000_0000) * (scale + scale * tmp);
    }
    sbits = sbits.wrapping_add(1022u64 << 52);
    let scale = f64::from_bits(sbits);
    let mut y = scale + scale * tmp;
    if y < 1.0 {
        let mut lo = scale - y + scale * tmp;
        let hi = 1.0 + y;
        lo = 1.0 - hi + y + lo;
        y = (hi + lo) - 1.0;
        if y == 0.0 {
            y = 0.0;
        }
    }
    f64::MIN_POSITIVE * y
}

/// Faithful binary64 exponential — ARM/glibc scalar algorithm pinned for
/// ACM paths after `libm::exp(-10)` failed the Stage C Fortran vector by one
/// ULP. The generator supplies finite inputs only; IEEE infinities/NaNs are
/// retained for completeness.
pub fn exp_pinned(x: f64) -> f64 {
    const N: u64 = 128;
    let abstop = ((x.to_bits() >> 52) as u32) & 0x7ff;
    if abstop.wrapping_sub(0x3c9) >= 0x408u32.wrapping_sub(0x3c9) {
        if abstop.wrapping_sub(0x3c9) >= 0x8000_0000 {
            return 1.0 + x;
        }
        if abstop >= 0x409 {
            if x == f64::NEG_INFINITY {
                return 0.0;
            }
            if !x.is_finite() {
                return 1.0 + x;
            }
            return if x.is_sign_negative() {
                0.0
            } else {
                f64::INFINITY
            };
        }
    }
    let inv_ln2_n = f64::from_bits(0x3ff7_1547_652b_82fe) * N as f64;
    let shift = f64::from_bits(0x4338_0000_0000_0000);
    let z = inv_ln2_n * x;
    let shifted = z + shift;
    let ki = shifted.to_bits();
    let kd = shifted - shift;
    let r = (x + kd * f64::from_bits(0xbf76_2e42_fefa_0000))
        + kd * f64::from_bits(0xbd0c_f79a_bc9e_3b3a);
    let idx = (2 * (ki % N)) as usize;
    let top = ki << (52 - 7);
    let tail = f64::from_bits(EXP_TAB[idx]);
    let sbits = EXP_TAB[idx + 1].wrapping_add(top);
    let r2 = r * r;
    let c2 = f64::from_bits(0x3fdf_ffff_ffff_fdbd);
    let c3 = f64::from_bits(0x3fc5_5555_5555_543c);
    let c4 = f64::from_bits(0x3fa5_5555_cf17_2b91);
    let c5 = f64::from_bits(0x3f81_1111_67a4_d017);
    let tmp = tail + r + r2 * (c2 + r * c3) + r2 * r2 * (c4 + r * c5);
    if abstop.wrapping_sub(0x3c9) >= 0x408u32.wrapping_sub(0x3c9) {
        return exp_special_case(tmp, sbits, ki);
    }
    let scale = f64::from_bits(sbits);
    scale + scale * tmp
}
