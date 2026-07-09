#![forbid(unsafe_code)]

use std::ffi::OsString;
use std::process;

use cligen::cli_diff::{diff_cli_files, CliDiff};

fn main() {
    process::exit(run(std::env::args_os().skip(1)));
}

fn run(args: impl IntoIterator<Item = OsString>) -> i32 {
    let Some((expected, actual)) = parse_args(args) else {
        eprintln!("usage: cligen-cli-diff <expected.cli> <actual.cli>");
        return 2;
    };

    compare_paths(&expected, &actual)
}

fn parse_args(args: impl IntoIterator<Item = OsString>) -> Option<(OsString, OsString)> {
    let mut args = args.into_iter();
    let expected = args.next()?;
    let actual = args.next()?;
    if args.next().is_none() {
        Some((expected, actual))
    } else {
        None
    }
}

fn compare_paths(expected: &OsString, actual: &OsString) -> i32 {
    match diff_cli_files(expected, actual) {
        Ok(CliDiff::Identical { daily_records }) => {
            println!("identical: {daily_records} daily records");
            0
        }
        Ok(CliDiff::Divergent(divergence)) => {
            println!("{divergence}");
            1
        }
        Err(error) => {
            eprintln!("{error}");
            2
        }
    }
}
