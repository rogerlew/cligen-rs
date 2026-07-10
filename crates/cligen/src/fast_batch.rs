//! Experimental, declared monthly-random-batch backends.
//!
//! This extension owns the sole non-faithful branch at the existing monthly
//! batch seam. It never changes the source-authority `ranset` implementation:
//! `faithful_5_32_3` delegates to it unchanged, while `fast_batch_v0` fills
//! the same `Crandom3State.ranary` matrix and deliberately omits its QC/retry
//! protocol.

use crate::acm::AcmState;
use crate::cbk4::Cbk4State;
use crate::cbk7::Cbk7State;
use crate::crandom3::{Crandom3State, NRELEM, NRPARM};
use crate::profile::GenerationProfile;
use crate::quality::process::ProcessCounters;
use crate::rng::{ranset, RansetState};

/// Versioned owner for the monthly random-array refill seam.
///
/// # Errors
///
/// The faithful branch retains `ranset`'s fail-closed preconditions. The
/// fast branch rejects a month outside the source's 1-based range.
#[derive(Debug, Clone)]
pub enum MonthlyBatchBackend {
    /// Source-authority `ranset`, including its SAVE state and QC retries.
    Faithful(RansetState),
    /// Explicitly divergent four-lane uniform-batch producer.
    FastBatchV0(FastBatchState),
}

impl MonthlyBatchBackend {
    /// Construct the selected backend after the faithful burn and warm draws.
    pub fn from_profile(profile: GenerationProfile, seeds: &Cbk7State) -> Self {
        match profile {
            GenerationProfile::Faithful5323 => Self::Faithful(RansetState::default()),
            GenerationProfile::FastBatchV0 => Self::FastBatchV0(FastBatchState::from_seeds(seeds)),
        }
    }

    /// Refill the monthly `ranary` matrix at the source's existing boundary.
    #[allow(clippy::too_many_arguments)]
    pub fn refill(
        &mut self,
        ntd: i32,
        iyear: i32,
        bk4: &Cbk4State,
        seeds: &mut Cbk7State,
        acm: &mut AcmState,
        cr: &mut Crandom3State,
        process: &mut ProcessCounters,
    ) {
        match self {
            Self::Faithful(state) => ranset(ntd, iyear, bk4, seeds, state, acm, cr, process),
            Self::FastBatchV0(state) => state.refill(cr),
        }
    }
}

/// Four independent lanes of the `fast_batch_v0` SplitMix64 producer.
///
/// The lanes are filled in lockstep, four values at a time. This is a safe,
/// portable batch layout rather than a claim about a particular ISA's SIMD
/// code generation. Its `v0` identifier pins both the seed derivation and
/// the 24-bit open-interval f32 mapping.
///
/// # Numerics
///
/// Each output is `(top_24_bits + 0.5) / 2^24`, so it is representable as an
/// f32 strictly inside `(0, 1)`. This is an extension algorithm, not a
/// faithful transcription of the source RNG.
#[derive(Debug, Clone)]
pub struct FastBatchState {
    lanes: [u64; 4],
}

impl FastBatchState {
    /// Derive the profile's master lanes from post-burn, post-warm source
    /// seed state. The fast profile deliberately does not advance those
    /// source streams during monthly refills.
    pub fn from_seeds(seeds: &Cbk7State) -> Self {
        let seed_words = [
            seeds.k1.0,
            seeds.k2.0,
            seeds.k3.0,
            seeds.k4.0,
            seeds.k5.0,
            seeds.k6.0,
            seeds.k7.0,
            seeds.k8.0,
            seeds.k9.0,
            seeds.k10.0,
        ];
        let mut material = 0x6A09_E667_F3BC_C909u64;
        for stream in seed_words {
            for word in stream {
                material ^= word as u32 as u64;
                material = splitmix64(material);
            }
        }
        let lanes = std::array::from_fn(|lane| {
            material = material.wrapping_add((lane as u64) + 1);
            splitmix64(material)
        });
        Self { lanes }
    }

    /// Fill all source-visible matrix slots with strictly open-interval
    /// uniforms, leaving the faithful QC accumulators untouched.
    ///
    /// # Panics
    ///
    /// Panics when `cr.mox` is outside the 1-based source month range.
    pub fn refill(&mut self, cr: &mut Crandom3State) {
        assert!(
            (1..=12).contains(&cr.mox),
            "fast_batch_v0: mox must be in 1..=12"
        );
        for parameter in 0..NRPARM {
            for element in (0..NRELEM).step_by(4) {
                let values = self.next_four();
                for (lane, value) in values.into_iter().enumerate() {
                    if element + lane < NRELEM {
                        cr.ranary[parameter][element + lane] = value;
                    }
                }
            }
        }
    }

    fn next_four(&mut self) -> [f32; 4] {
        std::array::from_fn(|lane| {
            self.lanes[lane] = self.lanes[lane].wrapping_add(0x9E37_79B9_7F4A_7C15);
            open_f32(splitmix64(self.lanes[lane]))
        })
    }
}

fn splitmix64(mut value: u64) -> u64 {
    value = (value ^ (value >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    value ^ (value >> 31)
}

fn open_f32(value: u64) -> f32 {
    let mantissa = (value >> 40) as f32;
    (mantissa + 0.5) * (1.0 / 16_777_216.0)
}

#[cfg(test)]
mod tests {
    use super::FastBatchState;
    use crate::cbk7::Cbk7State;
    use crate::crandom3::Crandom3State;

    #[test]
    fn fast_batch_v0_is_repeatable_open_interval_and_does_not_touch_qc() {
        let seeds = Cbk7State::default();
        let mut first = FastBatchState::from_seeds(&seeds);
        let mut second = FastBatchState::from_seeds(&seeds);
        let mut first_cr = Crandom3State {
            mox: 1,
            ..Crandom3State::default()
        };
        let mut second_cr = Crandom3State {
            mox: 1,
            ..Crandom3State::default()
        };

        first.refill(&mut first_cr);
        second.refill(&mut second_cr);

        assert_eq!(first_cr.ranary, second_cr.ranary);
        assert!(first_cr
            .ranary
            .iter()
            .flatten()
            .all(|value| *value > 0.0 && *value < 1.0));
        assert_eq!(first_cr.chicnt, Crandom3State::default().chicnt);
        assert_eq!(first_cr.g_dsum, Crandom3State::default().g_dsum);
        assert_eq!(first_cr.g_ssum, Crandom3State::default().g_ssum);
    }
}
