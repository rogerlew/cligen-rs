use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use clap::{Parser, Subcommand};

use cligen::par::ParFile;
use cligen::quality::compute_report;
use cligen::runspec::load_runspec_file;
use cligen::station::StationDocumentV1;
use cligen::stations::query::{list, nearest, NearestQuery};
use cligen::stations::sync::{sync_collection, SyncOutcome};
use cligen::stations::{cache_root_from_env, Manifests};

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
    /// Validate the document, enforce overwrite policy, and write `.cli`, its
    /// mandatory provenance companion, optional Parquet, and enabled quality output.
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
    /// Station collections: list, location query, and explicit payload sync
    /// (SPEC-STATION-DB). Only `sync` ever touches the network.
    Stations {
        #[command(subcommand)]
        command: StationsCommand,
    },
}

#[derive(Debug, Subcommand)]
enum StationsCommand {
    /// Show every collection with its version, sync state, and station count.
    List {
        /// Restrict to one collection.
        collection: Option<String>,
    },
    /// Nearest stations to a point (haversine over the shipped catalog).
    Nearest {
        /// Latitude in degrees (negative = south).
        #[arg(long, allow_hyphen_values = true)]
        lat: f64,
        /// Longitude in degrees as the catalog states it (negative = west).
        #[arg(long, allow_hyphen_values = true)]
        lon: f64,
        /// Result count.
        #[arg(short = 'n', long, default_value_t = 5)]
        count: usize,
        /// Search one collection instead of all synced collections.
        #[arg(long)]
        collection: Option<String>,
        /// Keep only stations with at least this many record years.
        #[arg(long)]
        min_years: Option<f64>,
        /// Emit JSON rows instead of the table.
        #[arg(long)]
        json: bool,
    },
    /// Fetch, hash-verify, and cache collection payloads (all by default).
    Sync {
        /// Collections to sync.
        collections: Vec<String>,
        /// Air-gap source directory holding `<name>-<version>.tar.gz`
        /// archives instead of the network.
        #[arg(long)]
        from: Option<PathBuf>,
        /// Re-fetch a collection that is already cached.
        #[arg(long)]
        force: bool,
    },
    /// Convert one legacy `.par` into deterministic modern station JSON.
    Convert {
        /// Legacy CLIGEN 5.32.3 station parameter file.
        par: PathBuf,
        /// Destination `*.station.json` document.
        document: PathBuf,
        /// Replace an existing destination instead of failing closed.
        #[arg(long)]
        overwrite: bool,
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
        Command::Stations { command } => stations(command),
    };
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("cligen: {error}");
            ExitCode::FAILURE
        }
    }
}

fn stations(command: StationsCommand) -> Result<(), String> {
    match command {
        StationsCommand::Convert {
            par,
            document,
            overwrite,
        } => stations_convert(&par, &document, overwrite),
        StationsCommand::List { collection } => {
            let (manifests, cache_root) = station_collection_context()?;
            stations_list(&manifests, &cache_root, collection)
        }
        StationsCommand::Nearest {
            lat,
            lon,
            count,
            collection,
            min_years,
            json,
        } => {
            let (manifests, cache_root) = station_collection_context()?;
            stations_nearest(
                &manifests,
                &cache_root,
                NearestQuery {
                    latitude: lat,
                    longitude: lon,
                    count,
                    collection,
                    min_years,
                },
                json,
            )
        }
        StationsCommand::Sync {
            collections,
            from,
            force,
        } => {
            let (manifests, cache_root) = station_collection_context()?;
            stations_sync(
                &manifests,
                &cache_root,
                &collections,
                from.as_deref(),
                force,
            )
        }
    }
}

fn station_collection_context() -> Result<(Manifests, PathBuf), String> {
    let manifests = Manifests::embedded();
    let cache_root = cache_root_from_env().map_err(|error| error.to_string())?;
    Ok((manifests, cache_root))
}

fn stations_list(
    manifests: &Manifests,
    cache_root: &Path,
    collection: Option<String>,
) -> Result<(), String> {
    let mut rows = list(manifests, cache_root).map_err(|error| error.to_string())?;
    if let Some(name) = &collection {
        manifests.get(name).map_err(|error| error.to_string())?;
        rows.retain(|row| &row.name == name);
    }
    for row in rows {
        let state = if row.synced {
            format!("synced ({} stations)", row.stations.unwrap_or(0))
        } else {
            "not synced".to_owned()
        };
        println!(
            "{:<10} {:<8} {:<24} {}",
            row.name, row.version, state, row.description
        );
    }
    Ok(())
}

fn stations_nearest(
    manifests: &Manifests,
    cache_root: &Path,
    query: NearestQuery,
    json: bool,
) -> Result<(), String> {
    let rows = nearest(manifests, cache_root, &query).map_err(|error| error.to_string())?;
    if json {
        let text = serde_json::to_string_pretty(&rows).map_err(|error| error.to_string())?;
        println!("{text}");
        return Ok(());
    }
    for row in rows {
        println!(
            "{:<10} {:<28} {:>9.4} {:>9.4} {:>5} yr {:>10.2} km  {}",
            row.collection,
            row.id,
            row.latitude,
            row.longitude,
            row.years,
            row.distance_km,
            row.path.display()
        );
    }
    Ok(())
}

fn stations_sync(
    manifests: &Manifests,
    cache_root: &Path,
    collections: &[String],
    from: Option<&Path>,
    force: bool,
) -> Result<(), String> {
    let selected: Vec<&str> = if collections.is_empty() {
        manifests
            .collections
            .iter()
            .map(|collection| collection.name.as_str())
            .collect()
    } else {
        collections.iter().map(String::as_str).collect()
    };
    for name in selected {
        let collection = manifests.get(name).map_err(|error| error.to_string())?;
        let outcome = sync_collection(collection, cache_root, from, force)
            .map_err(|error| error.to_string())?;
        match outcome {
            SyncOutcome::Synced => println!(
                "{name} {}: synced into {}",
                collection.version,
                collection.cache_dir(cache_root).display()
            ),
            SyncOutcome::AlreadySynced => {
                println!("{name} {}: already synced", collection.version);
            }
        }
    }
    Ok(())
}

fn stations_convert(par: &Path, document: &Path, overwrite: bool) -> Result<(), String> {
    let par_bytes = std::fs::read(par)
        .map_err(|error| format!("cannot read legacy station {}: {error}", par.display()))?;
    let parsed = ParFile::parse(&par_bytes).map_err(|error| error.to_string())?;
    let station = StationDocumentV1::from_legacy_par(&parsed).map_err(|error| error.to_string())?;
    let bytes = station.to_json_bytes().map_err(|error| error.to_string())?;
    let mut options = std::fs::OpenOptions::new();
    options.write(true);
    if overwrite {
        options.create(true).truncate(true);
    } else {
        options.create_new(true);
    }
    let mut output = options.open(document).map_err(|error| {
        format!(
            "cannot create station document {}: {error}",
            document.display()
        )
    })?;
    output.write_all(&bytes).map_err(|error| {
        format!(
            "cannot write station document {}: {error}",
            document.display()
        )
    })?;
    println!("{}", document.display());
    Ok(())
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
