//! Metrics-v3 precipitation structure, tails, and CLIGEN event descriptors.

use std::collections::BTreeMap;

use crate::quality::aggregation::year_slices;
use crate::quality::estimators::{mean, nearest_rank_quantile, sample_sd};
use crate::quality::groups::corr_pair;
use crate::quality::intake::DailyValue;
use crate::quality::report::{
    Months, PrecipitationStructure, ScalarDistribution, SpellDistribution,
    StormDescriptorDependence, StormDescriptorDistributions, StormDescriptors, Tails,
    ThresholdPrecipitationStructure, TopEvent, YearTails,
};

type WetPredicate = fn(&DailyValue) -> bool;

struct ClassifiedSpellLengths {
    whole: Vec<f64>,
    by_start_month: [Vec<f64>; 12],
}

impl ClassifiedSpellLengths {
    fn new() -> Self {
        Self {
            whole: Vec::new(),
            by_start_month: std::array::from_fn(|_| Vec::new()),
        }
    }

    fn push(&mut self, start_month: usize, length: usize) {
        let value = length as f64;
        self.whole.push(value);
        self.by_start_month[start_month].push(value);
    }
}

/// Group D — per-year tails plus whole-stream structure and descriptors.
#[must_use]
pub(crate) fn compute(rows: &[DailyValue]) -> Tails {
    let max_1_day = rolling_maxima_by_end_year(rows, 1);
    let max_3_day = rolling_maxima_by_end_year(rows, 3);
    let max_5_day = rolling_maxima_by_end_year(rows, 5);
    let per_year: Vec<YearTails> = year_slices(rows)
        .into_iter()
        .map(|slice| {
            year_tails(
                slice.rows,
                slice.complete,
                max_1_day.get(&slice.year).copied(),
                max_3_day.get(&slice.year).copied(),
                max_5_day.get(&slice.year).copied(),
            )
        })
        .collect();
    Tails {
        per_year: per_year.clone(),
        top_events: top_events(rows),
        precipitation_structure: precipitation_structure(rows, &per_year),
        storm_descriptors: storm_descriptors(rows),
    }
}

fn rolling_maxima_by_end_year(rows: &[DailyValue], window: usize) -> BTreeMap<i32, f64> {
    let mut maxima = BTreeMap::new();
    if rows.len() < window {
        return maxima;
    }
    for end in window - 1..rows.len() {
        let total = rows[end + 1 - window..=end]
            .iter()
            .map(|row| row.precip_mm)
            .sum::<f64>();
        maxima
            .entry(rows[end].year)
            .and_modify(|current: &mut f64| *current = current.max(total))
            .or_insert(total);
    }
    maxima
}

fn year_tails(
    rows: &[DailyValue],
    complete_year: bool,
    max_1_day_precip_mm: Option<f64>,
    max_3_day_precip_mm: Option<f64>,
    max_5_day_precip_mm: Option<f64>,
) -> YearTails {
    let mut wet_event_day_count = 0u32;
    let mut max_ratio: Option<f64> = None;
    let mut longest_wet = 0u32;
    let mut longest_dry = 0u32;
    let mut wet_run = 0u32;
    let mut dry_run = 0u32;
    for row in rows {
        if row.is_wet() {
            wet_event_day_count += 1;
            max_ratio = Some(max_ratio.map_or(row.peak_intensity_ratio, |current| {
                current.max(row.peak_intensity_ratio)
            }));
            wet_run += 1;
            dry_run = 0;
        } else {
            dry_run += 1;
            wet_run = 0;
        }
        longest_wet = longest_wet.max(wet_run);
        longest_dry = longest_dry.max(dry_run);
    }
    YearTails {
        year: rows[0].year,
        n_days: rows.len() as u32,
        complete_year,
        max_1_day_precip_mm,
        max_3_day_precip_mm,
        max_5_day_precip_mm,
        wet_event_day_count,
        max_peak_intensity_ratio: max_ratio,
        longest_wet_spell_days: longest_wet,
        longest_dry_spell_days: longest_dry,
    }
}

fn top_events(rows: &[DailyValue]) -> Vec<TopEvent> {
    let mut wet: Vec<(usize, &DailyValue)> = rows
        .iter()
        .enumerate()
        .filter(|(_, row)| row.is_wet())
        .collect();
    wet.sort_by(|(index_a, a), (index_b, b)| {
        b.precip_mm
            .partial_cmp(&a.precip_mm)
            .expect("intake guarantees finite values")
            .then_with(|| a.date_key().cmp(&b.date_key()))
            .then_with(|| index_a.cmp(index_b))
    });
    wet.iter()
        .take(5)
        .enumerate()
        .map(|(rank, (row_index, row))| TopEvent {
            rank: rank as u32 + 1,
            year: row.year,
            month: row.month,
            day: row.day,
            row_index: *row_index as u64 + 1,
            precip_mm: row.precip_mm,
            duration_h: row.duration_h,
            time_to_peak_fraction: row.time_to_peak,
            peak_intensity_ratio: row.peak_intensity_ratio,
        })
        .collect()
}

fn precipitation_structure(rows: &[DailyValue], per_year: &[YearTails]) -> PrecipitationStructure {
    PrecipitationStructure {
        trace_positive: threshold_structure(rows, per_year, DailyValue::is_wet),
        r1mm: threshold_structure(rows, per_year, DailyValue::is_r1mm),
    }
}

fn threshold_structure(
    rows: &[DailyValue],
    per_year: &[YearTails],
    predicate: WetPredicate,
) -> ThresholdPrecipitationStructure {
    let (wet_spells, dry_spells) = spell_distributions(rows, predicate);
    let wet_amounts: Vec<f64> = rows
        .iter()
        .filter(|row| predicate(row))
        .map(|row| row.precip_mm)
        .collect();
    let (previous, next) = adjacent_wet_amounts(rows, predicate);
    let complete: Vec<&YearTails> = per_year.iter().filter(|year| year.complete_year).collect();
    ThresholdPrecipitationStructure {
        wet_spells_days: wet_spells,
        dry_spells_days: dry_spells,
        wet_day_amount_mm: distribution(&wet_amounts),
        adjacent_wet_day_amount: corr_pair(&previous, &next),
        annual_max_1_day_mm: distribution(&annual_maxima(&complete, |year| {
            year.max_1_day_precip_mm
        })),
        annual_max_3_day_mm: distribution(&annual_maxima(&complete, |year| {
            year.max_3_day_precip_mm
        })),
        annual_max_5_day_mm: distribution(&annual_maxima(&complete, |year| {
            year.max_5_day_precip_mm
        })),
    }
}

fn annual_maxima(years: &[&YearTails], value: fn(&YearTails) -> Option<f64>) -> Vec<f64> {
    years.iter().filter_map(|year| value(year)).collect()
}

fn spell_distributions(
    rows: &[DailyValue],
    predicate: WetPredicate,
) -> (SpellDistribution, SpellDistribution) {
    let mut wet = ClassifiedSpellLengths::new();
    let mut dry = ClassifiedSpellLengths::new();
    if rows.is_empty() {
        return (spell_summary(wet), spell_summary(dry));
    }
    let mut current_wet = predicate(&rows[0]);
    let mut start_month = (rows[0].month - 1) as usize;
    let mut length = 1usize;
    for row in &rows[1..] {
        let row_wet = predicate(row);
        if row_wet == current_wet {
            length += 1;
            continue;
        }
        push_spell(&mut wet, &mut dry, current_wet, start_month, length);
        current_wet = row_wet;
        start_month = (row.month - 1) as usize;
        length = 1;
    }
    push_spell(&mut wet, &mut dry, current_wet, start_month, length);
    (spell_summary(wet), spell_summary(dry))
}

fn push_spell(
    wet: &mut ClassifiedSpellLengths,
    dry: &mut ClassifiedSpellLengths,
    is_wet: bool,
    start_month: usize,
    length: usize,
) {
    if is_wet {
        wet.push(start_month, length);
    } else {
        dry.push(start_month, length);
    }
}

fn spell_summary(lengths: ClassifiedSpellLengths) -> SpellDistribution {
    SpellDistribution {
        whole_run: distribution(&lengths.whole),
        by_start_month: Months::from_fn(|month| distribution(&lengths.by_start_month[month])),
    }
}

fn adjacent_wet_amounts(rows: &[DailyValue], predicate: WetPredicate) -> (Vec<f64>, Vec<f64>) {
    let mut previous = Vec::new();
    let mut next = Vec::new();
    for pair in rows.windows(2) {
        if predicate(&pair[0]) && predicate(&pair[1]) {
            previous.push(pair[0].precip_mm);
            next.push(pair[1].precip_mm);
        }
    }
    (previous, next)
}

fn storm_descriptors(rows: &[DailyValue]) -> StormDescriptors {
    let wet_event_days = rows.iter().filter(|row| row.is_wet()).count() as u64;
    let valid: Vec<&DailyValue> = rows
        .iter()
        .filter(|row| valid_descriptor_row(row))
        .collect();
    let depth: Vec<f64> = valid.iter().map(|row| row.precip_mm).collect();
    let duration: Vec<f64> = valid.iter().map(|row| row.duration_h).collect();
    let time_to_peak: Vec<f64> = valid.iter().map(|row| row.time_to_peak).collect();
    let ratio: Vec<f64> = valid.iter().map(|row| row.peak_intensity_ratio).collect();
    StormDescriptors {
        wet_event_days,
        included_event_days: valid.len() as u64,
        excluded_event_days: wet_event_days - valid.len() as u64,
        distributions: StormDescriptorDistributions {
            depth_mm: distribution(&depth),
            duration_h: distribution(&duration),
            time_to_peak_fraction: distribution(&time_to_peak),
            peak_intensity_ratio: distribution(&ratio),
        },
        dependence: descriptor_dependence(&depth, &duration, &time_to_peak, &ratio),
    }
}

fn valid_descriptor_row(row: &DailyValue) -> bool {
    row.is_wet()
        && row.duration_h > 0.0
        && (0.0..=1.0).contains(&row.time_to_peak)
        && row.peak_intensity_ratio >= 0.0
}

fn descriptor_dependence(
    depth: &[f64],
    duration: &[f64],
    time_to_peak: &[f64],
    ratio: &[f64],
) -> StormDescriptorDependence {
    StormDescriptorDependence {
        depth_duration: corr_pair(depth, duration),
        depth_time_to_peak: corr_pair(depth, time_to_peak),
        depth_peak_intensity_ratio: corr_pair(depth, ratio),
        duration_time_to_peak: corr_pair(duration, time_to_peak),
        duration_peak_intensity_ratio: corr_pair(duration, ratio),
        time_to_peak_peak_intensity_ratio: corr_pair(time_to_peak, ratio),
    }
}

fn distribution(values: &[f64]) -> ScalarDistribution {
    ScalarDistribution {
        n: values.len() as u64,
        mean: mean(values),
        sd: sample_sd(values),
        p50: nearest_rank_quantile(values, 0.50),
        p90: nearest_rank_quantile(values, 0.90),
        p95: nearest_rank_quantile(values, 0.95),
        p99: nearest_rank_quantile(values, 0.99),
        max: nearest_rank_quantile(values, 1.0),
    }
}
