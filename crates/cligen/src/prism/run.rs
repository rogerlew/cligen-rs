//! Artifact-producing orchestration for the stochastic-plus-PRISM mode.

use std::fs;
use std::path::{Path, PathBuf};

use serde::Serialize;

use super::{grid, localize, Distribution, PrismError, EMBEDDED_METHOD};

/// Required scientific request.
#[derive(Debug, Clone, Serialize)]
pub struct PrismRunRequest {
    pub longitude: f64,
    pub latitude: f64,
    pub years: i32,
    pub output_dir: PathBuf,
}

/// Optional scientific extensions for a PRISM run.
#[derive(Debug, Clone, Default)]
pub struct PrismRunOptions {
    pub degenerate_occurrence_repair: localize::DegenerateOccurrenceRepair,
    pub station_source: localize::StationSource,
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
    requested_selection_method_id: String,
    effective_selection_method_id: String,
    requested_station_id: Option<String>,
    requested_par_path: Option<PathBuf>,
    target_elevation_m: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    degenerate_occurrence_repair_method_id: Option<String>,
}

/// Build a complete provenance-bearing artifact directory and run the
/// unchanged faithful generator. The destination must not already exist.
pub fn execute(
    distribution: &Distribution,
    cache_root: &Path,
    request: &PrismRunRequest,
) -> Result<(), PrismError> {
    execute_with_options(
        distribution,
        cache_root,
        request,
        PrismRunOptions::default(),
    )
    .map(|_| ())
}

/// Execute with an explicitly declared preprocessing extension profile.
pub fn execute_with_options(
    distribution: &Distribution,
    cache_root: &Path,
    request: &PrismRunRequest,
    options: PrismRunOptions,
) -> Result<Vec<localize::OccurrenceRepairReceipt>, PrismError> {
    validate_request(request)?;
    let staging = prepare_output_staging(request)?;
    let staged_request = PrismRunRequest {
        longitude: request.longitude,
        latitude: request.latitude,
        years: request.years,
        output_dir: staging.clone(),
    };
    let result =
        execute_in(distribution, cache_root, &staged_request, options).and_then(|repairs| {
            publish_output(&staging, &request.output_dir)?;
            Ok(repairs)
        });
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
    options: PrismRunOptions,
) -> Result<Vec<localize::OccurrenceRepairReceipt>, PrismError> {
    let normals = grid::query(
        distribution,
        cache_root,
        request.longitude,
        request.latitude,
    )?;
    if options.degenerate_occurrence_repair == localize::DegenerateOccurrenceRepair::Disabled {
        execute_ordinary(
            distribution,
            cache_root,
            request,
            &normals,
            options.station_source,
        )
    } else {
        execute_repaired(
            distribution,
            cache_root,
            request,
            &normals,
            options.station_source,
            options.degenerate_occurrence_repair,
        )
    }
}

fn execute_ordinary(
    distribution: &Distribution,
    cache_root: &Path,
    request: &PrismRunRequest,
    normals: &grid::NormalsReceipt,
    station_source: localize::StationSource,
) -> Result<Vec<localize::OccurrenceRepairReceipt>, PrismError> {
    let localized = localize::localize_from(cache_root, normals, station_source)?;
    emit_run(
        distribution,
        request,
        normals,
        &localized.selection,
        &localized.source_bytes,
        &localized.localized_bytes,
        &localized.localization,
        &localized.localization.profile_id,
        None,
    )?;
    Ok(Vec::new())
}

fn execute_repaired(
    distribution: &Distribution,
    cache_root: &Path,
    request: &PrismRunRequest,
    normals: &grid::NormalsReceipt,
    station_source: localize::StationSource,
    repair: localize::DegenerateOccurrenceRepair,
) -> Result<Vec<localize::OccurrenceRepairReceipt>, PrismError> {
    let localized =
        localize::localize_from_with_repair(cache_root, normals, station_source, repair)?;
    emit_run(
        distribution,
        request,
        normals,
        &localized.selection,
        &localized.source_bytes,
        &localized.localized_bytes,
        &localized.localization,
        &localized.localization.profile_id,
        Some(
            &localized
                .localization
                .degenerate_occurrence_repair_method_id,
        ),
    )?;
    Ok(localized.localization.occurrence_repairs)
}

#[allow(clippy::too_many_arguments)]
fn emit_run(
    distribution: &Distribution,
    request: &PrismRunRequest,
    normals: &grid::NormalsReceipt,
    selection: &localize::SelectionReceipt,
    source_bytes: &[u8],
    localized_bytes: &[u8],
    localization: &impl Serialize,
    profile_id: &str,
    repair_method_id: Option<&str>,
) -> Result<(), PrismError> {
    write_receipt_artifacts(
        request,
        normals,
        selection,
        localization,
        profile_id,
        repair_method_id,
    )?;
    write_station_artifacts(request, source_bytes, localized_bytes)?;
    execute_faithful(request, selection, repair_method_id)?;
    write_artifact_manifest(
        distribution,
        &request.output_dir,
        &selection.cligen_binary_sha256,
        profile_id,
    )
}

fn write_receipt_artifacts(
    request: &PrismRunRequest,
    normals: &grid::NormalsReceipt,
    selection: &localize::SelectionReceipt,
    localization: &impl Serialize,
    profile_id: &str,
    repair_method_id: Option<&str>,
) -> Result<(), PrismError> {
    write_json(
        &request.output_dir.join("request.json"),
        &ScientificRequest {
            longitude: request.longitude,
            latitude: request.latitude,
            years: request.years,
            requested_selection_method_id: selection.requested_selection_method_id.clone(),
            effective_selection_method_id: selection.effective_selection_method_id.clone(),
            requested_station_id: selection.requested_station_id.clone(),
            requested_par_path: selection.requested_par_path.clone(),
            target_elevation_m: selection.target_elevation_m,
            degenerate_occurrence_repair_method_id: repair_method_id.map(str::to_owned),
        },
    )?;
    write_json(&request.output_dir.join("prism-normals.json"), &normals)?;
    write_json(
        &request.output_dir.join("station-selection.json"),
        selection,
    )?;
    write_json(&request.output_dir.join("localization.json"), localization)?;
    write_method_artifact(&request.output_dir, profile_id, repair_method_id, selection)
}

fn write_method_artifact(
    output_dir: &Path,
    profile_id: &str,
    repair_method_id: Option<&str>,
    selection: &localize::SelectionReceipt,
) -> Result<(), PrismError> {
    let mut method = serde_json::from_str::<serde_json::Value>(EMBEDDED_METHOD)
        .map_err(|error| PrismError::Output(format!("embedded PRISM method record: {error}")))?;
    let bytes = {
        let object = method
            .as_object_mut()
            .expect("embedded method is an object");
        object.insert("schema_version".to_owned(), 3.into());
        object.insert(
            "base_method_id".to_owned(),
            serde_json::Value::String("stochastic_prism_localized_par_v1".to_owned()),
        );
        object.insert(
            "method_id".to_owned(),
            serde_json::Value::String(profile_id.to_owned()),
        );
        object.insert(
            "station_selection".to_owned(),
            serde_json::json!({
                "requested_method_id": selection.requested_selection_method_id,
                "effective_method_id": selection.effective_selection_method_id,
                "fallback_applied": selection.fallback_applied,
                "contract": "SPEC-A12R4-STATION-SOURCE-CLI revision 1"
            }),
        );
        if let Some(method_id) = repair_method_id {
            object.insert(
                "active_extension".to_owned(),
                serde_json::json!({
                    "method_id": method_id,
                    "contract": "SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION revision 2",
                    "persistence_assumption": "independent_days_pww_equals_pwd_equals_q"
                }),
            );
        }
        let mut bytes = serde_json::to_vec_pretty(&method)
            .map_err(|error| PrismError::Output(format!("serialize PRISM method: {error}")))?;
        bytes.push(b'\n');
        bytes
    };
    fs::write(output_dir.join("method.json"), bytes)
        .map_err(|source| super::io_error("write PRISM method artifact", source))
}

fn write_station_artifacts(
    request: &PrismRunRequest,
    source_bytes: &[u8],
    localized_bytes: &[u8],
) -> Result<(), PrismError> {
    fs::write(request.output_dir.join("source-station.par"), source_bytes)
        .map_err(|source| super::io_error("write source station artifact", source))?;
    fs::write(request.output_dir.join("localized.par"), localized_bytes)
        .map_err(|source| super::io_error("write localized station artifact", source))
}

fn execute_faithful(
    request: &PrismRunRequest,
    selection: &localize::SelectionReceipt,
    repair_method_id: Option<&str>,
) -> Result<(), PrismError> {
    let runspec = runspec_yaml(
        request.years,
        &selection.effective_selection_method_id,
        repair_method_id,
    );
    let runspec_path = request.output_dir.join("inp.yaml");
    fs::write(&runspec_path, runspec)
        .map_err(|source| super::io_error("write PRISM runspec", source))?;
    crate::runspec::load_runspec_file(&runspec_path)
        .and_then(|prepared| prepared.generate_and_write())
        .map_err(|error| PrismError::Output(error.to_string()))
}

fn runspec_yaml(years: i32, selection_method_id: &str, repair_method_id: Option<&str>) -> String {
    let command_echo = match repair_method_id {
        Some(_) => format!(
            "cligen prism run (selection_method_id={selection_method_id}, repair=independent-prism-v1)"
        ),
        None => format!("cligen prism run (selection_method_id={selection_method_id})"),
    };
    format!(
        "cligen_runspec: 1\nstation:\n  par: localized.par\nmode: continuous\nsimulation:\n  begin_year: 1\n  years: {years}\n  interpolation: none\nrng:\n  burn: 0\ngeneration_profile: faithful_5_32_3\nqc_filter: faithful\noutput:\n  cli: climate.cli\n  quality: true\n  overwrite: false\n  command_echo: '{command_echo}'\n"
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
    expected_executable_sha256: &str,
    profile_id: &str,
) -> Result<(), PrismError> {
    let artifacts = artifact_identities(output_dir)?;
    let executable_path = std::env::current_exe()
        .map_err(|source| super::io_error("resolve current executable", source))?;
    let executable = file_identity(
        &executable_path,
        executable_path.parent().unwrap_or(Path::new(".")),
    )?;
    if executable.sha256 != expected_executable_sha256 {
        return Err(PrismError::Output(
            "executing cligen binary changed while producing the run".to_owned(),
        ));
    }
    write_json(
        &output_dir.join("artifact-manifest.json"),
        &ArtifactManifest {
            schema_version: 1,
            profile_id: profile_id.to_owned(),
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
    use std::{fs, path::PathBuf};

    use super::{runspec_yaml, write_method_artifact, EMBEDDED_METHOD};

    fn selection() -> crate::prism::localize::SelectionReceipt {
        crate::prism::localize::SelectionReceipt {
            schema_version: 3,
            profile_id: crate::prism::PROFILE_ID.to_owned(),
            requested_selection_method_id: "closest_localizable_v1".to_owned(),
            effective_selection_method_id: "closest_localizable_v1".to_owned(),
            selection_method_id: "closest_localizable_v1".to_owned(),
            fallback_applied: false,
            requested_station_id: None,
            requested_par_path: None,
            resolved_par_path: None,
            target_elevation_m: None,
            collection_name: Some("us-2015".to_owned()),
            collection_version: Some("2026.07".to_owned()),
            collection_archive_sha256: Some("0".repeat(64)),
            selected_station_id: "test.par".to_owned(),
            selected_source_identity: "registered:us-2015@2026.07:test.par".to_owned(),
            selected_source_par_path: PathBuf::from("test.par"),
            selected_source_par_sha256: "1".repeat(64),
            cligen_binary_sha256: "2".repeat(64),
            candidates: Vec::new(),
            candidate_rejections: Vec::new(),
        }
    }

    #[test]
    fn generated_runspec_is_accepted_shape() {
        let parsed = crate::runspec::RunspecDocument::parse(&runspec_yaml(
            30,
            "closest_localizable_v1",
            None,
        ))
        .unwrap();
        parsed.validate().unwrap();
    }

    #[test]
    fn repair_runspec_binds_extension_in_climate_command_provenance() {
        let yaml = runspec_yaml(
            1,
            "closest_localizable_v1",
            Some("degenerate_occurrence_independent_prism_v1"),
        );
        assert!(yaml.contains("selection_method_id=closest_localizable_v1"));
        assert!(yaml.contains("repair=independent-prism-v1"));
        let parsed = crate::runspec::RunspecDocument::parse(&yaml).unwrap();
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
    fn method_artifact_declares_station_selection() {
        let root = std::env::temp_dir().join(format!(
            "cligen-prism-method-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        fs::create_dir(&root).unwrap();
        write_method_artifact(&root, crate::prism::PROFILE_ID, None, &selection()).unwrap();
        let record: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join("method.json")).unwrap()).unwrap();
        assert_eq!(record["schema_version"], 3);
        assert_eq!(
            record["station_selection"]["effective_method_id"],
            "closest_localizable_v1"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn extension_method_artifact_declares_base_and_assumption() {
        let root = std::env::temp_dir().join(format!(
            "cligen-prism-extension-method-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        fs::create_dir(&root).unwrap();
        write_method_artifact(
            &root,
            "stochastic_prism_localized_par_v2_degenerate_occurrence_independent_v1",
            Some("degenerate_occurrence_independent_prism_v1"),
            &selection(),
        )
        .unwrap();
        let record: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join("method.json")).unwrap()).unwrap();
        assert_eq!(record["schema_version"], 3);
        assert_eq!(
            record["base_method_id"],
            "stochastic_prism_localized_par_v1"
        );
        assert_eq!(
            record["active_extension"]["persistence_assumption"],
            "independent_days_pww_equals_pwd_equals_q"
        );
        fs::remove_dir_all(root).unwrap();
    }
}
