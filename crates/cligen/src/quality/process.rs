//! Run-scoped, observation-only accumulation for quality-report group P.

use crate::acm::AcmState;

use super::report::{
    AcceptanceStatistics, CapGiveUp, CounterfactualMetrics, Months, ParameterCounterfactual,
    ParameterRetries, ProcessMetrics,
};

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
    /// `qc_filter: off` diagnostic state + verdict counts; empty under
    /// `faithful` (SPEC-QUALITY-REPORT rev 5, metrics_version 2).
    pub(crate) diagnostic: DiagnosticQc,
    counterfactual_batches: [[u64; 12]; 9],
    counterfactual_rejects: [[u64; 12]; 9],
}

/// The would-have-been QC accumulators for `qc_filter: off` — a
/// parallel copy of the source's cumulative QC state (`chicnt`,
/// `g_dsum`/`g_ssum`, `g_dimi`/`g_dimp`) plus a private ACM scratch,
/// so diagnostic evaluation never touches generation state.
#[derive(Debug, Clone)]
pub struct DiagnosticQc {
    pub(crate) chicnt: [[[i32; 20]; 12]; 9],
    pub(crate) g_dsum: [[f64; 12]; 9],
    pub(crate) g_ssum: [[f64; 12]; 9],
    pub(crate) g_dimi: [i32; 12],
    pub(crate) g_dimp: [i32; 12],
    pub(crate) acm: AcmState,
}

impl Default for DiagnosticQc {
    fn default() -> Self {
        DiagnosticQc {
            chicnt: [[[0; 20]; 12]; 9],
            g_dsum: [[0.0; 12]; 9],
            g_ssum: [[0.0; 12]; 9],
            g_dimi: [0; 12],
            g_dimp: [0; 12],
            acm: AcmState::default(),
        }
    }
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

    pub(crate) fn record_counterfactual(&mut self, parameter: usize, month: usize, reject: bool) {
        self.counterfactual_batches[parameter][month] += 1;
        if reject {
            self.counterfactual_rejects[parameter][month] += 1;
        }
    }

    /// Freeze counters into the metrics-version-2 report shape.
    #[must_use]
    pub fn into_metrics(self, qc_filter: Option<String>) -> ProcessMetrics {
        let retries = (0..9)
            .map(|parameter| ParameterRetries {
                parameter: (parameter + 1) as u32,
                rejected_attempts: months(self.rejected_attempts[parameter]),
                accepted_batches: months(self.accepted_batches[parameter]),
            })
            .collect();
        let batches: u64 = self.counterfactual_batches.iter().flatten().copied().sum();
        let counterfactual = (batches > 0).then(|| CounterfactualMetrics {
            batches,
            would_reject: self.counterfactual_rejects.iter().flatten().copied().sum(),
            by_parameter: (0..9)
                .map(|parameter| ParameterCounterfactual {
                    parameter: (parameter + 1) as u32,
                    batches: months(self.counterfactual_batches[parameter]),
                    would_reject: months(self.counterfactual_rejects[parameter]),
                })
                .collect(),
        });
        ProcessMetrics {
            qc_filter,
            retries,
            acceptance_statistics: self.acceptance_statistics,
            cap_give_ups: self.cap_give_ups,
            counterfactual,
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
