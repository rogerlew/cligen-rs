//! Batch-independent metrics-v3 estimator bridge for reproducible corpus builds.
//!
//! The process accepts one finite JSON array of f64 values on stdin and emits
//! the metrics-v3 low-frequency power fraction (number or `null`) on stdout.

use std::io::{self, Read as _};
use std::process::ExitCode;

fn run() -> Result<(), String> {
    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .map_err(|error| format!("read estimator input: {error}"))?;
    let values: Vec<f64> =
        serde_json::from_str(&input).map_err(|error| format!("parse estimator input: {error}"))?;
    if values.iter().any(|value| !value.is_finite()) {
        return Err("estimator input contains a non-finite value".to_owned());
    }
    let result = cligen::quality::estimators::low_frequency_power_fraction(&values);
    println!(
        "{}",
        serde_json::to_string(&result)
            .map_err(|error| format!("serialize estimator output: {error}"))?
    );
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("cligen-quality-estimator: {error}");
            ExitCode::FAILURE
        }
    }
}
