//! Run-scoped, observation-only accumulation for quality-report group P.

use super::report::{AcceptanceStatistics, CapGiveUp, Months, ParameterRetries, ProcessMetrics};

/// Mutable generation observer owned by `modes::GenState`.
///
/// Values recorded here never feed a generation decision. The fixed arrays
/// preserve parameter/month and stream order without map iteration.
#[derive(Debug, Clone, Default)]
pub struct ProcessCounters {
    rejected_attempts: [[u64; 12]; 9],
    accepted_batches: [[u64; 12]; 9],
    acceptance_statistics: Vec<AcceptanceStatistics>,
    cap_give_ups: Vec<CapGiveUp>,
    pub(crate) v7_recovery_count: u64,
    pub(crate) tdew_rangecheck_count: u64,
    pub(crate) randn_draws: [u64; 10],
}

impl ProcessCounters {
    pub(crate) fn record_rejection(&mut self, parameter: usize, month: usize) {
        self.rejected_attempts[parameter][month] += 1;
    }

    pub(crate) fn record_acceptance(
        &mut self,
        parameter: usize,
        month: usize,
        year: i32,
        levels: Option<(i32, f32, f32)>,
    ) {
        self.accepted_batches[parameter][month] += 1;
        let (ks_level, mean_level, variance_level) = match levels {
            Some((ks, mean, variance)) => {
                (Some(ks), applicable_level(mean), applicable_level(variance))
            }
            None => (None, None, None),
        };
        self.acceptance_statistics.push(AcceptanceStatistics {
            parameter: (parameter + 1) as u32,
            month: (month + 1) as u32,
            year,
            ks_level,
            mean_level,
            variance_level,
        });
    }

    pub(crate) fn record_cap_give_up(&mut self, parameter: usize, month: usize, year: i32) {
        self.cap_give_ups.push(CapGiveUp {
            parameter: (parameter + 1) as u32,
            month: (month + 1) as u32,
            year,
        });
    }

    /// Freeze counters into the metrics-version-1 report shape.
    #[must_use]
    pub fn into_metrics(self, qc_filter: Option<String>) -> ProcessMetrics {
        let retries = (0..9)
            .map(|parameter| ParameterRetries {
                parameter: (parameter + 1) as u32,
                rejected_attempts: months(self.rejected_attempts[parameter]),
                accepted_batches: months(self.accepted_batches[parameter]),
            })
            .collect();
        ProcessMetrics {
            qc_filter,
            retries,
            acceptance_statistics: self.acceptance_statistics,
            cap_give_ups: self.cap_give_ups,
            v7_recovery_count: self.v7_recovery_count,
            tdew_rangecheck_count: self.tdew_rangecheck_count,
            randn_draws: self.randn_draws,
        }
    }
}

fn applicable_level(level: f32) -> Option<f32> {
    (level >= 0.0).then_some(level)
}

fn months(values: [u64; 12]) -> Months<u64> {
    Months::from_fn(|month| values[month])
}
