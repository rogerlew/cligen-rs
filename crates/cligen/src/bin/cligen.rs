use std::io::Write;
use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};

use cligen::quality::compute_report;
use cligen::runspec::load_runspec_file;

#[derive(Debug, Parser)]
#[command(
    name = "cligen",
    about = "Run a schema-versioned CLIGEN inp.yaml document"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Parse, validate, resolve, and open declared inputs without generating output.
    Validate { input: PathBuf },
    /// Validate the document, enforce overwrite policy, and write the `.cli` output
    /// (plus the `.cli.quality.json` sidecar unless `output.quality: false`).
    Run { input: PathBuf },
    /// Compute a post-hoc quality report over any WEPP-format `.cli` and write it
    /// to stdout. `identity.provenance` and group P are null (SPEC-QUALITY-REPORT).
    Quality {
        /// The `.cli` file to measure.
        cli: PathBuf,
        /// The station `.par` the file was generated against (group A targets).
        #[arg(long)]
        par: PathBuf,
    },
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match cli.command {
        Command::Validate { input } => load_runspec_file(&input)
            .map(|_| ())
            .map_err(|error| error.to_string()),
        Command::Run { input } => load_runspec_file(&input)
            .and_then(|run| run.generate_and_write())
            .map_err(|error| error.to_string()),
        Command::Quality { cli, par } => post_hoc_quality(&cli, &par),
    };
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("cligen: {error}");
            ExitCode::FAILURE
        }
    }
}

fn post_hoc_quality(cli: &PathBuf, par: &PathBuf) -> Result<(), String> {
    let cli_text = std::fs::read_to_string(cli)
        .map_err(|error| format!("cannot read {}: {error}", cli.display()))?;
    let par_bytes =
        std::fs::read(par).map_err(|error| format!("cannot read {}: {error}", par.display()))?;
    let report =
        compute_report(&cli_text, &par_bytes, None, None).map_err(|error| error.to_string())?;
    let bytes = report.to_json_bytes().map_err(|error| error.to_string())?;
    std::io::stdout()
        .write_all(&bytes)
        .map_err(|error| format!("cannot write report to stdout: {error}"))
}
