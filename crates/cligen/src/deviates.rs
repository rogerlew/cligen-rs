//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/cligen.f:1789-1816 (dstn1),
//!   1651-1788 (dstg)
//! Precision-Map: REAL*4 except dstg's `fu`/`xx` locals
//!   (double precision, cligen.f:1696); mixed expressions widen exactly
//!   at the source's promotion points (see `dstg` body comments)
//! Faithful-Acceptance: dstn1 — per-record tap vectors
//!   (fixtures/taps/*/n1-sample.tap); dstg — sequential per-fixture
//!   replay (fixtures/taps/*/dg.tap) with per-record k7/iarrct
//!   assertions
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `rn1`,`rn2`,`rn` | `rn1,rn2,rn` | uniform deviates from `randn` | — |
//! | `dstn1` | `dstn1` | standard normal deviate, clamped ±10 | σ |
//! | `ai` | `ai` | month's max x-value for the gamma draw | — |
//! | `xn1` | `xn1` | gamma shape constant (Yu 1999: 6.28) | — |
//! | `xx` | `xx` | x-deviate scaled to `ai` (f64 island) | — |
//! | `fu` | `fu` | gamma pdf value at `xx` (f64 island) | — |
//! | `array` | `array(30)` | SAVE'd batch of QC-checked uniforms | — |
//! | `iarrct` | `iarrct` | SAVE'd cursor into `array` (30 = empty) | — |
//! | `itryct` | `itryct` | uniform-batch attempts this call | count |
//! | `itryc2` | `itryc2` | gamma-deviate attempts this call | count |

use crate::crandom3::Crandom3State;
use crate::qc::ks_tst;
use crate::quality::process::ProcessCounters;
use crate::rng::{randn_observed, SeedState};

/// Standard normal deviate from two uniforms — faithful `dstn1`
/// (`cligen.f:1789-1816`).
///
/// # Numerics
/// `sqrt(-2 ln rn1) · cos(2π rn2)` in f32 (source constant `6.283185`),
/// clamped to ±10. `logf`/`cosf` route through the pinned glibc/ARM
/// implementations (`crate::libm_pinned` — fixture evidence forced the
/// choice; the `libm` crate's f32 versions diverge from the reference
/// runtime); `sqrtf` is IEEE-exact and stays on `libm`.
// `6.283185` is the source's literal (cligen.f:1807), not an
// approximation to "fix"; the sequential range checks mirror
// cligen.f:1809-1810. Both suppressions are faithful-shape, per the
// coding standard.
#[allow(clippy::approx_constant, clippy::manual_clamp)]
pub fn dstn1(rn1: f32, rn2: f32) -> f32 {
    let mut d = libm::sqrtf(-2.0 * crate::libm_pinned::logf_pinned(rn1))
        * crate::libm_pinned::cosf_pinned(6.283185 * rn2);
    if d < -10.0 {
        d = -10.0;
    }
    if d > 10.0 {
        d = 10.0;
    }
    d
}

/// `dstg`'s SAVE state (`cligen.f:1710-1711`): the QC-checked uniform
/// batch and its cursor. `data iarrct/30/` means "empty" at program
/// start; `array` is Fortran-uninitialized (static zeros) and is fully
/// written before first read.
#[derive(Debug, Clone)]
pub struct DstgState {
    pub array: [f32; 30],
    pub iarrct: usize,
}

impl Default for DstgState {
    fn default() -> Self {
        DstgState {
            array: [0.0; 30],
            iarrct: 30,
        }
    }
}

/// Gamma deviate by rejection sampling — faithful `dstg`
/// (`cligen.f:1651-1788`). Drives the `alpha_0.5` peak-intensity ratio.
///
/// Returns the accepted uniform `rn1` (the source returns the deviate
/// pre-scaling; callers apply `ai`).
///
/// # Numerics
/// Uniform batches of 30 are drawn from `k7` and K-S-tested on
/// `chicnt` row 10 (`dstg`'s private channel); a failed test decrements
/// only the first 20 bins (`cligen.f:1748-1751` — a source quirk,
/// replicated) and redraws, consuming further `k7` draws — the
/// QC-regeneration coupling. Acceptance math follows the source's
/// promotion points exactly: `xx = dble(rn1*ai)` (f32 multiply, then
/// widen); `fu = xx**dble(xn1) * exp(dble(xn1)*(1d0 - xx))` in f64
/// (`libm::pow`/`libm::exp`); the rejection test widens `rn` to f64.
/// Both 10,000-try escapes print the source's warnings and accept.
// `6.28` is the source's Bofu Yu constant (cligen.f:1691), not TAU.
#[allow(clippy::approx_constant)]
pub fn dstg(
    ai: f32,
    k7: &mut SeedState,
    sv: &mut DstgState,
    cr: &mut Crandom3State,
    process: &mut ProcessCounters,
) -> f32 {
    let xn1: f32 = 6.28; // data xn1/6.28/ (Bofu Yu, 1999-07-04)
    let mox = cr.mox as usize;
    debug_assert!((1..=12).contains(&cr.mox), "dstg: mox out of range");
    let mut itryct = 0i32;
    let mut itryc2 = 0i32;

    loop {
        // Label 10: refill the QC-checked uniform batch if exhausted.
        if sv.iarrct == 30 {
            loop {
                // Label 21.
                itryct += 1;
                for i in 0..30 {
                    sv.array[i] = randn_observed(k7, 6, process);
                    let ichi = (sv.array[i] * 20.0) as i32 + 1;
                    cr.chicnt[9][mox - 1][(ichi - 1) as usize] += 1;
                }
                let level1 = ks_tst(10, cr);
                if level1 == 0 {
                    sv.iarrct = 0;
                    break;
                }
                if itryct == 10000 {
                    // cligen.f:1743-1746 — accept after 10,000 tries.
                    println!("Uniform could not succeed in 10,000 tries.");
                    println!("Precipitation Intensities are suspect.");
                    sv.iarrct = 0;
                    break;
                }
                // Source quirk (cligen.f:1748-1751): only the first 20
                // of the 30 rejected values are removed from the bins.
                for i in 0..20 {
                    let ichi = (sv.array[i] * 20.0) as i32 + 1;
                    cr.chicnt[9][mox - 1][(ichi - 1) as usize] -= 1;
                }
            }
        }

        // Grab the next two uniforms from the batch.
        sv.iarrct += 1;
        let rn1 = sv.array[sv.iarrct - 1];
        sv.iarrct += 1;
        let rn = sv.array[sv.iarrct - 1];
        itryc2 += 1;

        // xx = rn1*ai in f32, THEN widened (cligen.f:1768).
        let xx: f64 = (rn1 * ai) as f64;
        // fu = xx**xn1 * exp(xn1*(1.0-xx)), all-f64 with xn1 widened
        // exactly (cligen.f:1771).
        let fu: f64 = libm::pow(xx, xn1 as f64) * libm::exp((xn1 as f64) * (1.0f64 - xx));

        if fu < rn as f64 {
            // Rejected (cligen.f:1773-1782).
            itryc2 += 1;
            if itryc2 == 10000 {
                println!("Gamma could not succeed in 10,000 tries.");
                println!("Precipitation Intensities are suspect.");
                return rn1;
            }
            continue;
        }
        return rn1;
    }
}
