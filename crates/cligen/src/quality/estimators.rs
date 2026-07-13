//! Pinned deterministic estimators (SPEC-QUALITY-REPORT §Determinism).
//!
//! All accumulation is f64 in row order; sample statistics use the
//! n−1 convention; skew is the adjusted Fisher–Pearson estimator
//! g1·√(n(n−1))/(n−2) with n ≥ 3 else null; Spearman uses
//! average-rank ties. Undefined results (empty samples, zero
//! variance, zero denominators) are `None`, never NaN — the report
//! serializer treats `None` as JSON `null` and never emits a
//! non-finite number.

/// Sample mean; `None` on an empty sample.
#[must_use]
pub fn mean(values: &[f64]) -> Option<f64> {
    if values.is_empty() {
        return None;
    }
    let sum: f64 = values.iter().sum();
    finite(sum / values.len() as f64)
}

/// n−1 sample standard deviation; `None` when n < 2.
#[must_use]
pub fn sample_sd(values: &[f64]) -> Option<f64> {
    let n = values.len();
    if n < 2 {
        return None;
    }
    let m = mean(values)?;
    let ss: f64 = values.iter().map(|value| (value - m) * (value - m)).sum();
    finite((ss / (n as f64 - 1.0)).sqrt())
}

/// n−1 sample covariance; `None` when paired n < 2.
///
/// # Panics
///
/// Debug builds panic when the paired slices differ in length.
#[must_use]
pub fn sample_covariance(xs: &[f64], ys: &[f64]) -> Option<f64> {
    debug_assert_eq!(xs.len(), ys.len(), "sample covariance: paired samples");
    if xs.len() < 2 {
        return None;
    }
    let mx = mean(xs)?;
    let my = mean(ys)?;
    let sum = xs
        .iter()
        .zip(ys)
        .map(|(x, y)| (x - mx) * (y - my))
        .sum::<f64>();
    finite(sum / (xs.len() as f64 - 1.0))
}

/// Coefficient of variation `sd / mean`; `None` when either input is
/// `None` or the mean is zero. The sign follows the mean.
#[must_use]
pub fn cv(mean: Option<f64>, sd: Option<f64>) -> Option<f64> {
    let (m, s) = (mean?, sd?);
    if m == 0.0 {
        return None;
    }
    finite(s / m)
}

/// Adjusted Fisher–Pearson skewness g1·√(n(n−1))/(n−2); `None` when
/// n < 3 or the sample variance is zero.
#[must_use]
pub fn adjusted_skew(values: &[f64]) -> Option<f64> {
    let n = values.len();
    if n < 3 {
        return None;
    }
    let m = mean(values)?;
    let nf = n as f64;
    let mut m2 = 0.0f64;
    let mut m3 = 0.0f64;
    for value in values {
        let d = value - m;
        m2 += d * d;
        m3 += d * d * d;
    }
    m2 /= nf;
    m3 /= nf;
    if m2 == 0.0 {
        return None;
    }
    // m2^1.5 as m2·√m2 (C-R1-002): multiply and sqrt are both
    // IEEE-754 correctly rounded, so the report is byte-reproducible
    // across platforms; `f64::powf` is not a pinned surface.
    let g1 = m3 / (m2 * m2.sqrt());
    finite(g1 * (nf * (nf - 1.0)).sqrt() / (nf - 2.0))
}

/// Pearson product-moment correlation; `None` when n < 2 or either
/// sample has zero variance.
///
/// # Panics
///
/// Debug builds panic when the paired slices differ in length.
#[must_use]
pub fn pearson(xs: &[f64], ys: &[f64]) -> Option<f64> {
    debug_assert_eq!(xs.len(), ys.len(), "pearson: paired samples");
    let n = xs.len();
    if n < 2 {
        return None;
    }
    let mx = mean(xs)?;
    let my = mean(ys)?;
    let mut sxy = 0.0f64;
    let mut sxx = 0.0f64;
    let mut syy = 0.0f64;
    for (x, y) in xs.iter().zip(ys) {
        let dx = x - mx;
        let dy = y - my;
        sxy += dx * dy;
        sxx += dx * dx;
        syy += dy * dy;
    }
    if sxx == 0.0 || syy == 0.0 {
        return None;
    }
    // Roundoff can place a mathematically exact ±1 correlation one ulp
    // outside its closed domain for small samples. Metrics v3 publishes the
    // mathematical coefficient and its schema therefore clamps that final
    // rounding residue only; the accumulated estimator is unchanged.
    finite((sxy / (sxx * syy).sqrt()).clamp(-1.0, 1.0))
}

/// Spearman rank correlation with average-rank ties: Pearson over the
/// average ranks. `None` when n < 2 or either rank vector is constant.
///
/// # Panics
///
/// Debug builds panic when the paired slices differ in length.
#[must_use]
pub fn spearman(xs: &[f64], ys: &[f64]) -> Option<f64> {
    debug_assert_eq!(xs.len(), ys.len(), "spearman: paired samples");
    if xs.len() < 2 {
        return None;
    }
    pearson(&average_ranks(xs), &average_ranks(ys))
}

/// Average ranks (1-based); tied values share the mean of the ranks
/// they span. Input values are finite by intake contract.
#[must_use]
pub fn average_ranks(values: &[f64]) -> Vec<f64> {
    let mut order: Vec<usize> = (0..values.len()).collect();
    order.sort_by(|&a, &b| {
        values[a]
            .partial_cmp(&values[b])
            .expect("intake guarantees finite values")
    });
    let mut ranks = vec![0.0f64; values.len()];
    let mut start = 0;
    while start < order.len() {
        let mut end = start;
        while end + 1 < order.len() && values[order[end + 1]] == values[order[start]] {
            end += 1;
        }
        // Ranks start+1 ..= end+1 average to (start + end)/2 + 1.
        let tied_rank = (start + end) as f64 / 2.0 + 1.0;
        for &index in &order[start..=end] {
            ranks[index] = tied_rank;
        }
        start = end + 1;
    }
    ranks
}

/// Empirical inverse-CDF (nearest-rank) quantile. For `0 < p <= 1`,
/// return sorted element `ceil(p*n)-1`; `None` for empty input or an
/// out-of-domain probability.
#[must_use]
pub fn nearest_rank_quantile(values: &[f64], probability: f64) -> Option<f64> {
    if values.is_empty() || !(0.0 < probability && probability <= 1.0) {
        return None;
    }
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| {
        a.partial_cmp(b)
            .expect("quality intake and metric builders guarantee finite values")
    });
    let rank = libm::ceil(probability * sorted.len() as f64) as usize;
    Some(sorted[rank.saturating_sub(1)])
}

/// Fraction of nonzero two-sided periodogram power at Fourier periods of at
/// least four observations (SPEC-QUALITY-REPORT metrics v3).
///
/// The input is demeaned. Positive bins `1..=floor(n/2)` receive weight two,
/// except the even-length Nyquist bin, whose mirror is itself and receives
/// weight one. `None` is returned for fewer than four observations or zero
/// total nonzero-frequency power.
#[must_use]
pub fn low_frequency_power_fraction(values: &[f64]) -> Option<f64> {
    let n = values.len();
    if n < 4 {
        return None;
    }
    let center = mean(values)?;
    let mut low_power = 0.0f64;
    let mut total_power = 0.0f64;
    for frequency in 1..=n / 2 {
        let (real, imaginary) = dft_bin(values, center, frequency);
        let raw_power = real * real + imaginary * imaginary;
        let nyquist = n.is_multiple_of(2) && frequency == n / 2;
        let weighted_power = raw_power * if nyquist { 1.0 } else { 2.0 };
        total_power += weighted_power;
        if n as f64 / frequency as f64 >= 4.0 {
            low_power += weighted_power;
        }
    }
    if total_power == 0.0 {
        return None;
    }
    finite(low_power / total_power)
}

fn dft_bin(values: &[f64], center: f64, frequency: usize) -> (f64, f64) {
    let scale = std::f64::consts::TAU * frequency as f64 / values.len() as f64;
    let mut real = 0.0f64;
    let mut imaginary = 0.0f64;
    for (index, value) in values.iter().enumerate() {
        let angle = scale * index as f64;
        let centered = value - center;
        real += centered * libm::cos(angle);
        imaginary -= centered * libm::sin(angle);
    }
    (real, imaginary)
}

/// Map a non-finite result to `None` so JSON emission never sees NaN
/// or infinities.
#[must_use]
pub fn finite(value: f64) -> Option<f64> {
    value.is_finite().then_some(value)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sample_sd_uses_n_minus_1() {
        // Var([1,2,3,4]) with n−1 = 5/3.
        let sd = sample_sd(&[1.0, 2.0, 3.0, 4.0]).unwrap();
        assert!((sd - (5.0f64 / 3.0).sqrt()).abs() < 1e-15);
    }

    #[test]
    fn adjusted_skew_matches_reference_value() {
        // Hand-derived: mean 4, m2 = 10, m3 = 36, g1 = 3.6/√10,
        // G1 = g1·√20/3 = 1.6970562748477141 (matches
        // scipy.stats.skew(..., bias=False)).
        let skew = adjusted_skew(&[1.0, 2.0, 3.0, 4.0, 10.0]).unwrap();
        assert!((skew - 1.697_056_274_847_714).abs() < 1e-12, "{skew}");
    }

    #[test]
    fn adjusted_skew_null_below_three_or_constant() {
        assert_eq!(adjusted_skew(&[1.0, 2.0]), None);
        assert_eq!(adjusted_skew(&[2.0, 2.0, 2.0]), None);
    }

    #[test]
    fn average_ranks_share_tied_means() {
        assert_eq!(
            average_ranks(&[10.0, 20.0, 20.0, 30.0]),
            vec![1.0, 2.5, 2.5, 4.0]
        );
    }

    #[test]
    fn spearman_is_sign_correct_and_tie_stable() {
        let xs = [1.0, 2.0, 3.0, 4.0, 5.0];
        let ys = [2.0, 4.0, 6.0, 8.0, 10.0];
        assert!((spearman(&xs, &ys).unwrap() - 1.0).abs() < 1e-15);
        let zs = [5.0, 4.0, 3.0, 2.0, 1.0];
        assert!((spearman(&xs, &zs).unwrap() + 1.0).abs() < 1e-15);
    }

    #[test]
    fn degenerate_correlations_are_null() {
        assert_eq!(pearson(&[1.0, 1.0], &[1.0, 2.0]), None);
        assert_eq!(spearman(&[3.0, 3.0, 3.0], &[1.0, 2.0, 3.0]), None);
        assert_eq!(pearson(&[1.0], &[1.0]), None);
    }

    #[test]
    fn covariance_and_nearest_rank_are_pinned() {
        assert_eq!(
            sample_covariance(&[1.0, 2.0, 3.0], &[2.0, 4.0, 8.0]),
            Some(3.0)
        );
        let values = [9.0, 1.0, 5.0, 3.0];
        assert_eq!(nearest_rank_quantile(&values, 0.5), Some(3.0));
        assert_eq!(nearest_rank_quantile(&values, 0.95), Some(9.0));
        assert_eq!(nearest_rank_quantile(&values, 0.0), None);
    }

    #[test]
    fn low_frequency_fraction_separates_slow_and_nyquist_cycles() {
        let slow = [1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0];
        let alternating = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0];
        assert!((low_frequency_power_fraction(&slow).unwrap() - 1.0).abs() < 1e-12);
        assert!(low_frequency_power_fraction(&alternating).unwrap().abs() < 1e-12);
        assert_eq!(low_frequency_power_fraction(&[1.0, 1.0, 1.0, 1.0]), None);
    }
}
