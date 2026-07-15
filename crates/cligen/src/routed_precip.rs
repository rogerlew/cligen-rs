//! A8c explicit routed daily-precipitation extension.
//!
//! This module owns only extension state. Faithful precipitation remains in
//! `daily::gen_precip`; the fallback enum variant delegates to it unchanged.

use crate::cbk7::Cbk7State;
use crate::station::{A8cDailyPrecipitation, DailyPrecipitationRoute};

const KNOT_PROBABILITIES: [f64; 11] = [
    0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.0,
];
const SPLITMIX_INCREMENT: u64 = 0x9E37_79B9_7F4A_7C15;

#[derive(Debug, Clone)]
pub(crate) enum DailyPrecipitationBackend {
    Faithful,
    LegacyDailyFallback,
    Integrated(Box<IntegratedDailyState>),
}

impl DailyPrecipitationBackend {
    pub(crate) fn from_route(route: Option<&A8cDailyPrecipitation>, seeds: &Cbk7State) -> Self {
        match route.map(|value| value.route) {
            None => Self::Faithful,
            Some(DailyPrecipitationRoute::LegacyDailyFallback) => Self::LegacyDailyFallback,
            Some(DailyPrecipitationRoute::IntegratedDaily) => Self::Integrated(Box::new(
                IntegratedDailyState::new(route.expect("integrated route is present"), seeds),
            )),
        }
    }

    pub(crate) fn uses_legacy_daily(&self) -> bool {
        matches!(self, Self::Faithful | Self::LegacyDailyFallback)
    }

    pub(crate) fn generate_integrated(&mut self, month: usize, wet_mean_in: f32) -> f32 {
        match self {
            Self::Integrated(state) => state.generate(month, wet_mean_in),
            Self::Faithful | Self::LegacyDailyFallback => {
                unreachable!("legacy routes delegate to daily::gen_precip")
            }
        }
    }
}

#[derive(Debug, Clone)]
struct MonthRuntime {
    occurrence: [f64; 4],
    amount_dispersion: f64,
    rho: f64,
    knots_mm: [f64; 11],
    normalization: f64,
}

#[derive(Debug, Clone)]
pub(crate) struct IntegratedDailyState {
    months: [MonthRuntime; 12],
    occurrence_stream: SplitMix64Stream,
    amount_stream: SplitMix64Stream,
    older_wet: bool,
    previous_wet: bool,
    amount_latent: Option<f64>,
    occurrence_draws: u64,
    amount_draws: u64,
}

impl IntegratedDailyState {
    fn new(coefficients: &A8cDailyPrecipitation, seeds: &Cbk7State) -> Self {
        let months = std::array::from_fn(|month| {
            let source = &coefficients.months[month];
            let season = &coefficients.seasons[season_index(month)];
            MonthRuntime {
                occurrence: source.occurrence_probabilities,
                amount_dispersion: source.amount_dispersion,
                rho: season.gaussian_copula_rho,
                knots_mm: season.log_quantile_knots_mm,
                normalization: quantile_normalization(
                    &season.log_quantile_knots_mm,
                    source.amount_dispersion,
                ),
            }
        });
        let material = seed_material(seeds);
        Self {
            months,
            occurrence_stream: SplitMix64Stream::new(splitmix64(material ^ 0xA8C0_CC01_0000_0001)),
            amount_stream: SplitMix64Stream::new(splitmix64(material ^ 0xA8C0_AA02_0000_0002)),
            older_wet: false,
            previous_wet: false,
            amount_latent: None,
            occurrence_draws: 0,
            amount_draws: 0,
        }
    }

    fn generate(&mut self, month: usize, wet_mean_in: f32) -> f32 {
        let occurrence_uniform = self.occurrence_stream.next_open_f64();
        let amount_normal = inverse_standard_normal(self.amount_stream.next_open_f64());
        self.occurrence_draws += 1;
        self.amount_draws += 1;

        let runtime = &self.months[month];
        let history = usize::from(self.older_wet) * 2 + usize::from(self.previous_wet);
        let wet = occurrence_uniform <= runtime.occurrence[history];
        let amount = if wet {
            let latent = correlated_latent(self.amount_latent, amount_normal, runtime.rho);
            self.amount_latent = Some(latent);
            wet_amount_in(runtime, wet_mean_in, latent)
        } else {
            self.amount_latent = None;
            0.0
        };
        self.older_wet = self.previous_wet;
        self.previous_wet = wet;
        amount
    }

    #[cfg(test)]
    fn draw_counts(&self) -> (u64, u64) {
        (self.occurrence_draws, self.amount_draws)
    }
}

#[derive(Debug, Clone, Copy)]
struct SplitMix64Stream {
    state: u64,
}

impl SplitMix64Stream {
    const fn new(state: u64) -> Self {
        Self { state }
    }

    fn next_open_f64(&mut self) -> f64 {
        self.state = self.state.wrapping_add(SPLITMIX_INCREMENT);
        let bits = splitmix64(self.state) >> 11;
        (bits as f64 + 0.5) * (1.0 / 9_007_199_254_740_992.0)
    }
}

fn seed_material(seeds: &Cbk7State) -> u64 {
    let words = [
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
    for stream in words {
        for word in stream {
            material ^= word as u32 as u64;
            material = splitmix64(material);
        }
    }
    material
}

fn splitmix64(mut value: u64) -> u64 {
    value = (value ^ (value >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    value ^ (value >> 31)
}

const fn season_index(month: usize) -> usize {
    match month {
        0 | 1 | 11 => 0,
        2..=4 => 1,
        5..=7 => 2,
        8..=10 => 3,
        _ => unreachable!(),
    }
}

fn correlated_latent(previous: Option<f64>, innovation: f64, rho: f64) -> f64 {
    match previous {
        None => innovation,
        Some(value) => rho * value + libm::sqrt(1.0 - rho * rho) * innovation,
    }
}

fn wet_amount_in(runtime: &MonthRuntime, wet_mean_in: f32, latent: f64) -> f32 {
    let probability = standard_normal_cdf(latent);
    let log_amount = interpolated_log_knot(&runtime.knots_mm, probability);
    let relative = libm::exp(runtime.amount_dispersion * log_amount) / runtime.normalization;
    (wet_mean_in as f64 * relative) as f32
}

fn standard_normal_cdf(value: f64) -> f64 {
    0.5 * (1.0 + libm::erf(value * std::f64::consts::FRAC_1_SQRT_2))
}

fn interpolated_log_knot(knots: &[f64; 11], probability: f64) -> f64 {
    let segment = KNOT_PROBABILITIES
        .windows(2)
        .position(|bounds| probability <= bounds[1])
        .unwrap_or(9);
    let lower_probability = KNOT_PROBABILITIES[segment];
    let width = KNOT_PROBABILITIES[segment + 1] - lower_probability;
    let fraction = (probability - lower_probability) / width;
    let lower = libm::log(knots[segment]);
    let upper = libm::log(knots[segment + 1]);
    lower + fraction * (upper - lower)
}

fn quantile_normalization(knots: &[f64; 11], dispersion: f64) -> f64 {
    (0..10)
        .map(|segment| segment_integral(knots, dispersion, segment))
        .sum()
}

fn segment_integral(knots: &[f64; 11], dispersion: f64, segment: usize) -> f64 {
    let width = KNOT_PROBABILITIES[segment + 1] - KNOT_PROBABILITIES[segment];
    let lower = dispersion * libm::log(knots[segment]);
    let upper = dispersion * libm::log(knots[segment + 1]);
    let delta = upper - lower;
    if delta.abs() < 1.0e-14 {
        width * libm::exp(lower)
    } else {
        width * (libm::exp(upper) - libm::exp(lower)) / delta
    }
}

fn inverse_standard_normal(probability: f64) -> f64 {
    const LOW: f64 = 0.024_25;
    const HIGH: f64 = 1.0 - LOW;
    if probability < LOW {
        inverse_normal_lower(probability)
    } else if probability <= HIGH {
        inverse_normal_center(probability)
    } else {
        -inverse_normal_lower(1.0 - probability)
    }
}

fn inverse_normal_lower(probability: f64) -> f64 {
    const C: [f64; 6] = [
        -7.784_894_002_430_293e-3,
        -3.223_964_580_411_365e-1,
        -2.400_758_277_161_838,
        -2.549_732_539_343_734,
        4.374_664_141_464_968,
        2.938_163_982_698_783,
    ];
    const D: [f64; 4] = [
        7.784_695_709_041_462e-3,
        3.224_671_290_700_398e-1,
        2.445_134_137_142_996,
        3.754_408_661_907_416,
    ];
    let q = libm::sqrt(-2.0 * libm::log(probability));
    polynomial6(q, C) / polynomial4_plus_one(q, D)
}

fn inverse_normal_center(probability: f64) -> f64 {
    const A: [f64; 6] = [
        -3.969_683_028_665_376e1,
        2.209_460_984_245_205e2,
        -2.759_285_104_469_687e2,
        1.383_577_518_672_69e2,
        -3.066_479_806_614_716e1,
        2.506_628_277_459_239,
    ];
    const B: [f64; 5] = [
        -5.447_609_879_822_406e1,
        1.615_858_368_580_409e2,
        -1.556_989_798_598_866e2,
        6.680_131_188_771_972e1,
        -1.328_068_155_288_572e1,
    ];
    let q = probability - 0.5;
    let r = q * q;
    q * polynomial6(r, A) / polynomial5_plus_one(r, B)
}

fn polynomial6(value: f64, coefficients: [f64; 6]) -> f64 {
    coefficients
        .into_iter()
        .fold(0.0, |accumulator, coefficient| {
            accumulator * value + coefficient
        })
}

fn polynomial5_plus_one(value: f64, coefficients: [f64; 5]) -> f64 {
    coefficients
        .into_iter()
        .fold(0.0, |accumulator, coefficient| {
            accumulator * value + coefficient
        })
        * value
        + 1.0
}

fn polynomial4_plus_one(value: f64, coefficients: [f64; 4]) -> f64 {
    coefficients
        .into_iter()
        .fold(0.0, |accumulator, coefficient| {
            accumulator * value + coefficient
        })
        * value
        + 1.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::station::{A8cMonthCoefficients, A8cSeasonCoefficients, DailyPrecipitationRoute};

    fn coefficients() -> A8cDailyPrecipitation {
        A8cDailyPrecipitation {
            route: DailyPrecipitationRoute::IntegratedDaily,
            fit_id: crate::station::A8A_FIT_ID.to_owned(),
            source_analysis_sha256: crate::station::A8A_ANALYSIS_SHA256.to_owned(),
            seasons: ["DJF", "MAM", "JJA", "SON"]
                .into_iter()
                .map(|season| A8cSeasonCoefficients {
                    season: season.to_owned(),
                    log_quantile_knots_mm: [
                        1.0, 1.1, 1.3, 1.6, 2.2, 3.5, 5.0, 7.0, 9.0, 12.0, 15.0,
                    ],
                    gaussian_copula_rho: 0.3,
                })
                .collect(),
            months: (1..=12)
                .map(|month| A8cMonthCoefficients {
                    month,
                    occurrence_probabilities: [0.2, 0.4, 0.3, 0.6],
                    amount_dispersion: 0.8,
                    legacy_amount_dispersion: 1.0,
                })
                .collect(),
        }
    }

    #[test]
    fn integrated_route_is_repeatable_positive_and_fixed_draw_count() {
        let coefficients = coefficients();
        let seeds = Cbk7State::default();
        let mut first = IntegratedDailyState::new(&coefficients, &seeds);
        let mut second = IntegratedDailyState::new(&coefficients, &seeds);
        let first_values: Vec<f32> = (0..400)
            .map(|day| first.generate((day / 31) % 12, 0.3))
            .collect();
        let second_values: Vec<f32> = (0..400)
            .map(|day| second.generate((day / 31) % 12, 0.3))
            .collect();
        assert_eq!(first_values, second_values);
        assert!(first_values
            .iter()
            .all(|value| value.is_finite() && *value >= 0.0));
        assert!(first_values.iter().any(|value| *value > 0.0));
        assert_eq!(first.draw_counts(), (400, 400));
    }

    #[test]
    fn inverse_normal_and_quantile_normalization_pin_extension_numerics() {
        assert!((inverse_standard_normal(0.5)).abs() < 1.0e-15);
        assert!((inverse_standard_normal(0.975) - 1.959_963_986_120_195).abs() < 2.0e-8);
        let knots = [1.0; 11];
        assert_eq!(quantile_normalization(&knots, 0.75), 1.0);
        assert_eq!(interpolated_log_knot(&knots, 0.37), 0.0);
    }
}
