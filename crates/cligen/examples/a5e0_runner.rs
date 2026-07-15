//! Package-local executable wrapper for the A5e0 research API.

use std::path::{Path, PathBuf};
use std::process::ExitCode;

use clap::Parser;
use cligen::a5e0::{A5e0Arm, A5e0RunInputs};

#[derive(Debug, Parser)]
#[command(name = "a5e0-runner")]
struct Args {
    #[arg(long)]
    par: PathBuf,
    #[arg(long)]
    coefficients: PathBuf,
    #[arg(long)]
    station: String,
    #[arg(long)]
    arm: String,
    #[arg(long)]
    replicate: u8,
    #[arg(long)]
    years: i32,
    #[arg(long)]
    cli: PathBuf,
    #[arg(long)]
    diagnostics: PathBuf,
}

fn main() -> ExitCode {
    match execute(Args::parse()) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("a5e0-runner: {error}");
            ExitCode::FAILURE
        }
    }
}

fn execute(args: Args) -> Result<(), String> {
    let par_bytes = std::fs::read(&args.par)
        .map_err(|error| format!("cannot read {}: {error}", args.par.display()))?;
    let coefficient_bytes = std::fs::read(&args.coefficients)
        .map_err(|error| format!("cannot read {}: {error}", args.coefficients.display()))?;
    let arm = A5e0Arm::parse(&args.arm).map_err(|error| error.to_string())?;
    let output = cligen::a5e0::run(&A5e0RunInputs {
        par_bytes: &par_bytes,
        coefficient_bytes: &coefficient_bytes,
        station_id: &args.station,
        arm,
        replicate: args.replicate,
        years: args.years,
    })
    .map_err(|error| error.to_string())?;
    prepare_parent(&args.cli)?;
    prepare_parent(&args.diagnostics)?;
    std::fs::write(&args.cli, output.cli)
        .map_err(|error| format!("cannot write {}: {error}", args.cli.display()))?;
    std::fs::write(
        &args.diagnostics,
        output
            .diagnostics
            .to_json_bytes()
            .map_err(|error| error.to_string())?,
    )
    .map_err(|error| format!("cannot write {}: {error}", args.diagnostics.display()))?;
    Ok(())
}

fn prepare_parent(path: &Path) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|error| format!("cannot create {}: {error}", parent.display()))?;
    }
    Ok(())
}
