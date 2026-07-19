//! Artifact-producing orchestration for the stochastic-plus-PRISM mode.

use std::fs;
use std::path::{Path, PathBuf};

use serde::Serialize;

use super::{grid, localize, Distribution, PrismError, EMBEDDED_METHOD, PROFILE_ID};

/// Required scientific request.
#[derive(Debug, Clone, Serialize)]
pub struct PrismRunRequest {
    pub longitude: f64,
    pub latitude: f64,
    pub years: i32,
    pub output_dir: PathBuf,
}

#[derive(Debug, Serialize)]
struct ArtifactIdentity {
    path: String,
    bytes: u64,
    sha256: String,
}

#[derive(Debug, Serialize)]
struct ArtifactManifest {
    schema_version: u32,
    profile_id: String,
    distribution: Distribution,
    executable: ArtifactIdentity,
    artifacts: Vec<ArtifactIdentity>,
}

#[derive(Debug, Serialize)]
struct ScientificRequest {
    longitude: f64,
    latitude: f64,
    years: i32,
}

/// Build a complete provenance-bearing artifact directory and run the
/// unchanged faithful generator. The destination must not already exist.
pub fn execute(
    distribution: &Distribution,
    cache_root: &Path,
    request: &PrismRunRequest,
) -> Result<(), PrismError> {
    validate_request(request)?;
    let staging = prepare_output_staging(request)?;
    let staged_request = PrismRunRequest {
        longitude: request.longitude,
        latitude: request.latitude,
        years: request.years,
        output_dir: staging.clone(),
    };
    let result = execute_in(distribution, cache_root, &staged_request)
        .and_then(|()| publish_output(&staging, &request.output_dir));
    if result.is_err() {
        let _ = fs::remove_dir_all(&staging);
    }
    result
}

fn prepare_output_staging(request: &PrismRunRequest) -> Result<PathBuf, PrismError> {
    let mut staging_name = request.output_dir.as_os_str().to_owned();
    staging_name.push(format!(".tmp-{}", std::process::id()));
    let staging = PathBuf::from(staging_name);
    if staging.exists() {
        return Err(PrismError::Output(format!(
            "staging path already exists: {}",
            staging.display()
        )));
    }
    fs::create_dir(&staging).map_err(|source| {
        PrismError::Output(format!(
            "cannot create staging directory {}: {source}",
            staging.display()
        ))
    })?;
    Ok(staging)
}

fn publish_output(staging: &Path, target: &Path) -> Result<(), PrismError> {
    fs::rename(staging, target).map_err(|source| {
        PrismError::Output(format!(
            "cannot publish {} as {}: {source}",
            staging.display(),
            target.display()
        ))
    })
}

fn validate_request(request: &PrismRunRequest) -> Result<(), PrismError> {
    if request.years <= 0 {
        return Err(PrismError::InvalidRequest(
            "years must be a positive integer".to_owned(),
        ));
    }
    if request.output_dir.as_os_str().is_empty() || request.output_dir.exists() {
        return Err(PrismError::InvalidRequest(
            "output_dir must name a new directory".to_owned(),
        ));
    }
    Ok(())
}

fn execute_in(
    distribution: &Distribution,
    cache_root: &Path,
    request: &PrismRunRequest,
) -> Result<(), PrismError> {
    let normals = grid::query(
        distribution,
        cache_root,
        request.longitude,
        request.latitude,
    )?;
    let localized = localize::localize(cache_root, &normals)?;
    emit_run(distribution, request, &normals, &localized)
}

fn emit_run(
    distribution: &Distribution,
    request: &PrismRunRequest,
    normals: &grid::NormalsReceipt,
    localized: &localize::LocalizedPar,
) -> Result<(), PrismError> {
    write_receipt_artifacts(request, normals, localized)?;
    write_station_artifacts(request, localized)?;
    execute_faithful(request)?;
    write_artifact_manifest(distribution, &request.output_dir)
}

fn write_receipt_artifacts(
    request: &PrismRunRequest,
    normals: &grid::NormalsReceipt,
    localized: &localize::LocalizedPar,
) -> Result<(), PrismError> {
    write_json(
        &request.output_dir.join("request.json"),
        &ScientificRequest {
            longitude: request.longitude,
            latitude: request.latitude,
            years: request.years,
        },
    )?;
    write_json(&request.output_dir.join("prism-normals.json"), &normals)?;
    write_json(
        &request.output_dir.join("station-selection.json"),
        &localized.selection,
    )?;
    write_json(
        &request.output_dir.join("localization.json"),
        &localized.localization,
    )?;
    write_method_artifact(&request.output_dir)
}

fn write_method_artifact(output_dir: &Path) -> Result<(), PrismError> {
    serde_json::from_str::<serde_json::Value>(EMBEDDED_METHOD)
        .map_err(|error| PrismError::Output(format!("embedded PRISM method record: {error}")))?;
    fs::write(output_dir.join("method.json"), EMBEDDED_METHOD)
        .map_err(|source| super::io_error("write PRISM method artifact", source))
}

fn write_station_artifacts(
    request: &PrismRunRequest,
    localized: &localize::LocalizedPar,
) -> Result<(), PrismError> {
    fs::write(
        request.output_dir.join("source-station.par"),
        &localized.source_bytes,
    )
    .map_err(|source| super::io_error("write source station artifact", source))?;
    fs::write(
        request.output_dir.join("localized.par"),
        &localized.localized_bytes,
    )
    .map_err(|source| super::io_error("write localized station artifact", source))
}

fn execute_faithful(request: &PrismRunRequest) -> Result<(), PrismError> {
    let runspec = runspec_yaml(request.years);
    let runspec_path = request.output_dir.join("inp.yaml");
    fs::write(&runspec_path, runspec)
        .map_err(|source| super::io_error("write PRISM runspec", source))?;
    crate::runspec::load_runspec_file(&runspec_path)
        .and_then(|prepared| prepared.generate_and_write())
        .map_err(|error| PrismError::Output(error.to_string()))
}

fn runspec_yaml(years: i32) -> String {
    format!(
        "cligen_runspec: 1\nstation:\n  par: localized.par\nmode: continuous\nsimulation:\n  begin_year: 1\n  years: {years}\n  interpolation: none\nrng:\n  burn: 0\ngeneration_profile: faithful_5_32_3\nqc_filter: faithful\noutput:\n  cli: climate.cli\n  quality: true\n  overwrite: false\n  command_echo: cligen prism run\n"
    )
}

fn write_json(path: &Path, value: &impl Serialize) -> Result<(), PrismError> {
    let mut bytes =
        serde_json::to_vec_pretty(value).map_err(|error| PrismError::Output(error.to_string()))?;
    bytes.push(b'\n');
    fs::write(path, bytes)
        .map_err(|source| super::io_error(format!("write {}", path.display()), source))
}

fn write_artifact_manifest(
    distribution: &Distribution,
    output_dir: &Path,
) -> Result<(), PrismError> {
    let artifacts = artifact_identities(output_dir)?;
    let executable_path = std::env::current_exe()
        .map_err(|source| super::io_error("resolve current executable", source))?;
    let executable = file_identity(
        &executable_path,
        executable_path.parent().unwrap_or(Path::new(".")),
    )?;
    write_json(
        &output_dir.join("artifact-manifest.json"),
        &ArtifactManifest {
            schema_version: 1,
            profile_id: PROFILE_ID.to_owned(),
            distribution: distribution.clone(),
            executable,
            artifacts,
        },
    )
}

fn artifact_identities(output_dir: &Path) -> Result<Vec<ArtifactIdentity>, PrismError> {
    let mut paths: Vec<PathBuf> = fs::read_dir(output_dir)
        .map_err(|source| super::io_error("list PRISM artifacts", source))?
        .map(|entry| entry.map(|value| value.path()))
        .collect::<Result<_, _>>()
        .map_err(|source| super::io_error("read PRISM artifact entry", source))?;
    paths.retain(|path| {
        path.is_file()
            && path.file_name().and_then(|name| name.to_str()) != Some("artifact-manifest.json")
    });
    paths.sort();
    paths
        .iter()
        .map(|path| file_identity(path, output_dir))
        .collect()
}

fn file_identity(path: &Path, relative_to: &Path) -> Result<ArtifactIdentity, PrismError> {
    let metadata = fs::metadata(path)
        .map_err(|source| super::io_error(format!("stat {}", path.display()), source))?;
    let lexical = path
        .strip_prefix(relative_to)
        .unwrap_or(path)
        .to_string_lossy()
        .into_owned();
    Ok(ArtifactIdentity {
        path: lexical,
        bytes: metadata.len(),
        sha256: super::sha256_file(path)?,
    })
}

#[cfg(test)]
mod tests {
    use std::fs;

    use super::{runspec_yaml, write_method_artifact, EMBEDDED_METHOD};

    #[test]
    fn generated_runspec_is_accepted_shape() {
        let parsed = crate::runspec::RunspecDocument::parse(&runspec_yaml(30)).unwrap();
        parsed.validate().unwrap();
    }

    #[test]
    fn method_record_names_origin_and_limitations() {
        let record: serde_json::Value = serde_json::from_str(EMBEDDED_METHOD).unwrap();
        assert_eq!(record["schema_version"], 1);
        assert_eq!(record["method_id"], "stochastic_prism_localized_par_v1");
        assert!(record["origin"].as_str().unwrap().starts_with("FSWEPP"));
        let limitations = record["limitations"].as_array().unwrap();
        assert_eq!(limitations.len(), 9);
        assert!(limitations
            .iter()
            .any(|value| value["id"] == "comparison_not_quality_certification"));
    }

    #[test]
    fn method_artifact_is_the_exact_embedded_record() {
        let root = std::env::temp_dir().join(format!(
            "cligen-prism-method-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        fs::create_dir(&root).unwrap();
        write_method_artifact(&root).unwrap();
        assert_eq!(
            fs::read_to_string(root.join("method.json")).unwrap(),
            EMBEDDED_METHOD
        );
        fs::remove_dir_all(root).unwrap();
    }
}
