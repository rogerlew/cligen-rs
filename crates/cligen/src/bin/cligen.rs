use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};

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
    /// Validate the document, enforce overwrite policy, and write the `.cli` output.
    Run { input: PathBuf },
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match cli.command {
        Command::Validate { input } => load_runspec_file(&input).map(|_| ()),
        Command::Run { input } => {
            load_runspec_file(&input).and_then(|run| run.generate_and_write())
        }
    };
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("cligen: {error}");
            ExitCode::FAILURE
        }
    }
}
