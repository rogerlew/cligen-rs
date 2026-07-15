//! Deterministic revision-1 `.cli.parquet` writer and conformance readback.
//!
//! The physical policy is pinned by `SPEC-CLI-PARQUET`. This module consumes
//! already generated [`crate::typed_output::ClimateRowV1`] values and has no
//! storm-generation responsibilities.

use std::collections::HashMap;
use std::error::Error;
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::path::{Path, PathBuf};
use std::sync::Arc;

use arrow_array::{Array, ArrayRef, Float64Array, Int32Array, Int8Array, RecordBatch, StringArray};
use arrow_schema::{DataType, Field, Schema, SchemaRef};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use parquet::arrow::ArrowWriter;
use parquet::basic::{Compression, Encoding, ZstdLevel};
use parquet::file::metadata::{ColumnChunkMetaData, KeyValue, ParquetMetaData, RowGroupMetaData};
use parquet::file::properties::{EnabledStatistics, WriterProperties, WriterVersion};
use parquet::schema::types::ColumnPath;

use crate::provenance::{
    ArtifactIdentityV1, ArtifactProvenanceV1, CoverageV1, GenerationProfileV1, StationModelV1,
};
use crate::typed_output::{
    validate_climate_rows_v1, ClimateIdentityV1, ClimateRowV1, TypedOutputError,
};

pub const CLI_PARQUET_SCHEMA_ID: &str = "org.openwepp.cligen.cli.parquet";
pub const CLI_PARQUET_SCHEMA_VERSION: &str = "1";
pub const PARQUET_CREATED_BY: &str = "cligen-rs parquet-writer-v1";
pub const PARQUET_WRITER_ID: &str = "arrow-rs-parquet/59.1.0";
pub const PARQUET_MAX_ROW_GROUP_ROWS: usize = 65_536;

/// Typed provenance input for one revision-1 Parquet artifact.
#[derive(Debug, Clone, Copy)]
pub struct ParquetArtifactV1<'a> {
    pub provenance: &'a ArtifactProvenanceV1,
}

impl ParquetArtifactV1<'_> {
    fn identity(self) -> ClimateIdentityV1 {
        ClimateIdentityV1 {
            run_id: self.provenance.effective_runspec_sha256.clone(),
            generation_profile: generation_profile(self.provenance).to_owned(),
            station_parameter_set_sha256: self.provenance.station.parameter_set_sha256.clone(),
        }
    }

    fn validate(self) -> Result<ClimateIdentityV1, ParquetOutputError> {
        self.provenance
            .validate()
            .map_err(|source| ParquetOutputError::InvalidArtifact(source.to_string()))?;
        if self.provenance.artifact != ArtifactIdentityV1::cli_parquet() {
            return Err(ParquetOutputError::InvalidArtifact(
                "provenance artifact must be SPEC-CLI-PARQUET revision 1".to_owned(),
            ));
        }
        if matches!(self.provenance.actual.coverage, CoverageV1::SingleEvent) {
            return Err(ParquetOutputError::InvalidArtifact(
                "single-event Parquet is not supported in revision 1".to_owned(),
            ));
        }
        let identity = self.identity();
        identity.validate()?;
        Ok(identity)
    }

    fn validate_for_write(self) -> Result<ClimateIdentityV1, ParquetOutputError> {
        let identity = self.validate()?;
        if self.provenance.producer.version != env!("CARGO_PKG_VERSION") {
            return Err(ParquetOutputError::InvalidArtifact(
                "producer.version does not match the current writer build".to_owned(),
            ));
        }
        Ok(identity)
    }
}

/// Logical Arrow schema for SPEC-CLI-PARQUET revision 1.
pub fn cli_parquet_schema_v1() -> Schema {
    Schema::new_with_metadata(
        vec![
            field("run_id", DataType::Utf8, "1", "effective-runspec SHA-256"),
            field(
                "generation_profile",
                DataType::Utf8,
                "1",
                "declared profile ID",
            ),
            field(
                "station_parameter_set_sha256",
                DataType::Utf8,
                "1",
                "syntax-independent station-model content identity",
            ),
            field(
                "sim_day_index",
                DataType::Int32,
                "day",
                "one-based contiguous row index",
            ),
            field(
                "year",
                DataType::Int32,
                "year",
                "CLIGEN/WEPP output year; year 1 is valid",
            ),
            field("month", DataType::Int8, "month", "calendar month 1–12"),
            field("day_of_month", DataType::Int8, "day", "valid day in month"),
            field(
                "precip_mm",
                DataType::Float64,
                "mm",
                "total daily precipitation",
            ),
            field(
                "duration_h",
                DataType::Float64,
                "h",
                "parametric storm duration; source value on dry days",
            ),
            field(
                "time_to_peak_fraction",
                DataType::Float64,
                "1",
                "time-to-peak / duration; source value on dry days",
            ),
            field(
                "peak_intensity_ratio",
                DataType::Float64,
                "1",
                "peak / mean rainfall intensity; source value on dry days",
            ),
            field(
                "tmax_c",
                DataType::Float64,
                "degree_Celsius",
                "daily maximum air temperature",
            ),
            field(
                "tmin_c",
                DataType::Float64,
                "degree_Celsius",
                "daily minimum air temperature",
            ),
            field(
                "solar_langley_day",
                DataType::Float64,
                "langley/day",
                "daily solar radiation",
            ),
            field(
                "wind_velocity_m_s",
                DataType::Float64,
                "m/s",
                "daily wind velocity",
            ),
            field(
                "wind_direction_deg",
                DataType::Float64,
                "degree",
                "clockwise from north",
            ),
            field(
                "tdew_c",
                DataType::Float64,
                "degree_Celsius",
                "daily dew-point temperature",
            ),
        ],
        HashMap::from([
            (
                "cligen.output_schema".to_owned(),
                CLI_PARQUET_SCHEMA_ID.to_owned(),
            ),
            (
                "cligen.output_schema_version".to_owned(),
                CLI_PARQUET_SCHEMA_VERSION.to_owned(),
            ),
        ]),
    )
}

/// Write and atomically publish a SPEC-CLI-PARQUET revision-1 file.
///
/// The fixed staging path must be absent. Unless `overwrite` is true, the final
/// path must also be absent. The staging file is created in the final path's
/// directory, closed successfully, and renamed only after every row group has
/// been flushed.
///
/// # Errors
/// Returns [`ParquetOutputError`] for a collision, malformed artifact/row,
/// filesystem error, Arrow schema error, or Parquet encoder failure. On any
/// pre-rename failure, no final file is exposed.
pub fn write_cli_parquet_v1(
    path: &Path,
    artifact: ParquetArtifactV1<'_>,
    rows: &[ClimateRowV1],
    overwrite: bool,
) -> Result<(), ParquetOutputError> {
    validate_destination(path)?;
    let identity = artifact.validate_for_write()?;
    validate_climate_rows_v1(rows, &identity)?;
    validate_span(artifact, rows)?;
    let provenance_bytes = artifact
        .provenance
        .to_compact_json_bytes()
        .map_err(|source| ParquetOutputError::InvalidArtifact(source.to_string()))?;
    let provenance_json = std::str::from_utf8(&provenance_bytes).map_err(|source| {
        ParquetOutputError::InvalidArtifact(format!("canonical provenance was not UTF-8: {source}"))
    })?;
    if !overwrite && path.try_exists()? {
        return Err(ParquetOutputError::Collision(path.to_path_buf()));
    }
    let staging = staging_path(path)?;
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&staging)
        .map_err(|source| {
            if source.kind() == std::io::ErrorKind::AlreadyExists {
                ParquetOutputError::Collision(staging.clone())
            } else {
                ParquetOutputError::Io(source)
            }
        })?;
    if let Err(error) = write_staging(file, artifact, provenance_json, rows) {
        let _ = fs::remove_file(&staging);
        return Err(error);
    }
    if let Err(error) = publish_staging(&staging, path, overwrite) {
        let _ = fs::remove_file(&staging);
        return Err(error);
    }
    Ok(())
}

/// Read a revision-1 file through arrow-rs and validate its logical schema.
///
/// This helper is intended for conformance checks and downstream adapters; it
/// returns footer metadata and physical row-group sizes alongside typed rows.
///
/// # Errors
/// Returns [`ParquetOutputError`] for I/O/Parquet failures, schema drift, or
/// an unexpected Arrow array type.
pub fn read_cli_parquet_v1(path: &Path) -> Result<ParquetReadbackV1, ParquetOutputError> {
    let builder = ParquetRecordBatchReaderBuilder::try_new(File::open(path)?)?;
    let schema = builder.schema().clone();
    let expected_schema = cli_parquet_schema_v1();
    if schema.fields() != expected_schema.fields()
        || schema
            .metadata()
            .get("cligen.output_schema")
            .map(String::as_str)
            != Some(CLI_PARQUET_SCHEMA_ID)
        || schema
            .metadata()
            .get("cligen.output_schema_version")
            .map(String::as_str)
            != Some(CLI_PARQUET_SCHEMA_VERSION)
    {
        return Err(ParquetOutputError::Schema(
            "logical schema differs from SPEC-CLI-PARQUET revision 1".to_owned(),
        ));
    }
    let file_metadata = builder.metadata().file_metadata();
    let footer_metadata = file_metadata
        .key_value_metadata()
        .map_or(&[][..], Vec::as_slice)
        .iter()
        .map(|item| (item.key.clone(), item.value.clone()))
        .collect::<Vec<_>>();
    let provenance_json = required_footer_value(&footer_metadata, "cligen.provenance")?;
    let provenance = ArtifactProvenanceV1::parse_json(provenance_json.as_bytes())
        .map_err(|source| ParquetOutputError::InvalidArtifact(source.to_string()))?;
    let canonical_json = String::from_utf8(
        provenance
            .to_compact_json_bytes()
            .map_err(|source| ParquetOutputError::InvalidArtifact(source.to_string()))?,
    )
    .map_err(|source| {
        ParquetOutputError::InvalidArtifact(format!("canonical provenance was not UTF-8: {source}"))
    })?;
    if provenance_json != canonical_json {
        return Err(ParquetOutputError::InvalidArtifact(
            "cligen.provenance is not canonical compact JSON".to_owned(),
        ));
    }
    let writer = validate_footer(&footer_metadata, &provenance, &canonical_json)?;
    if writer == PARQUET_WRITER_ID {
        validate_physical_policy(builder.metadata())?;
    }
    let row_group_rows = builder
        .metadata()
        .row_groups()
        .iter()
        .map(|group| group.num_rows())
        .collect();
    let created_by = file_metadata.created_by().map(str::to_owned);
    let writer_version = file_metadata.version();
    let reader = builder.build()?;
    let mut rows = Vec::new();
    for batch in reader {
        rows.extend(rows_from_batch(&batch?)?);
    }
    let artifact = ParquetArtifactV1 {
        provenance: &provenance,
    };
    let identity = artifact.validate()?;
    validate_climate_rows_v1(&rows, &identity)?;
    validate_span(artifact, &rows)?;
    Ok(ParquetReadbackV1 {
        schema,
        rows,
        provenance,
        footer_metadata,
        row_group_rows,
        created_by,
        writer_version,
    })
}

/// Values and physical diagnostics returned by [`read_cli_parquet_v1`].
#[derive(Debug)]
pub struct ParquetReadbackV1 {
    pub schema: SchemaRef,
    pub rows: Vec<ClimateRowV1>,
    pub provenance: ArtifactProvenanceV1,
    pub footer_metadata: Vec<(String, Option<String>)>,
    pub row_group_rows: Vec<i64>,
    pub created_by: Option<String>,
    pub writer_version: i32,
}

/// Revision-1 Parquet output failure.
#[derive(Debug)]
pub enum ParquetOutputError {
    Collision(PathBuf),
    InvalidArtifact(String),
    InvalidDestination(PathBuf),
    Schema(String),
    Typed(TypedOutputError),
    Io(std::io::Error),
    Arrow(arrow_schema::ArrowError),
    Parquet(parquet::errors::ParquetError),
}

impl fmt::Display for ParquetOutputError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Collision(path) => write!(f, "output path collision: {}", path.display()),
            Self::InvalidArtifact(message) => write!(f, "invalid Parquet artifact: {message}"),
            Self::InvalidDestination(path) => {
                write!(f, "invalid .cli.parquet destination: {}", path.display())
            }
            Self::Schema(message) => write!(f, "invalid Parquet schema: {message}"),
            Self::Typed(source) => write!(f, "invalid typed climate rows: {source}"),
            Self::Io(source) => write!(f, "Parquet I/O failed: {source}"),
            Self::Arrow(source) => write!(f, "Arrow operation failed: {source}"),
            Self::Parquet(source) => write!(f, "Parquet operation failed: {source}"),
        }
    }
}

impl Error for ParquetOutputError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Typed(source) => Some(source),
            Self::Io(source) => Some(source),
            Self::Arrow(source) => Some(source),
            Self::Parquet(source) => Some(source),
            Self::Collision(_)
            | Self::InvalidArtifact(_)
            | Self::InvalidDestination(_)
            | Self::Schema(_) => None,
        }
    }
}

impl From<TypedOutputError> for ParquetOutputError {
    fn from(source: TypedOutputError) -> Self {
        Self::Typed(source)
    }
}

impl From<std::io::Error> for ParquetOutputError {
    fn from(source: std::io::Error) -> Self {
        Self::Io(source)
    }
}

impl From<arrow_schema::ArrowError> for ParquetOutputError {
    fn from(source: arrow_schema::ArrowError) -> Self {
        Self::Arrow(source)
    }
}

impl From<parquet::errors::ParquetError> for ParquetOutputError {
    fn from(source: parquet::errors::ParquetError) -> Self {
        Self::Parquet(source)
    }
}

fn field(name: &str, data_type: DataType, units: &str, description: &str) -> Field {
    Field::new(name, data_type, false).with_metadata(HashMap::from([
        ("units".to_owned(), units.to_owned()),
        ("description".to_owned(), description.to_owned()),
    ]))
}

fn station_input_schema(provenance: &ArtifactProvenanceV1) -> String {
    format!(
        "{}/{}",
        provenance.station.input_schema.id, provenance.station.input_schema.version
    )
}

fn station_model(provenance: &ArtifactProvenanceV1) -> &'static str {
    match provenance.station.model {
        StationModelV1::FixedMonthly5323 => "fixed_monthly_5_32_3",
        StationModelV1::A8cIntegratedDailyV1 => "a8c_integrated_daily_v1",
    }
}

fn generation_profile(provenance: &ArtifactProvenanceV1) -> &'static str {
    match provenance.generation.profile {
        GenerationProfileV1::Faithful5323 => "faithful_5_32_3",
        GenerationProfileV1::FastBatchV0 => "fast_batch_v0",
        GenerationProfileV1::A8cRoutedDailyV1 => "a8c_routed_daily_v1",
    }
}

fn coverage(provenance: &ArtifactProvenanceV1) -> Result<&'static str, ParquetOutputError> {
    match provenance.actual.coverage {
        CoverageV1::CompleteRun => Ok("complete_run"),
        CoverageV1::ObservedSourceEnd => Ok("observed_source_end"),
        CoverageV1::SingleEvent => Err(ParquetOutputError::InvalidArtifact(
            "single-event Parquet is not supported in revision 1".to_owned(),
        )),
    }
}

fn required_footer_value(
    metadata: &[(String, Option<String>)],
    key: &str,
) -> Result<String, ParquetOutputError> {
    let values = metadata
        .iter()
        .filter(|(candidate, _)| candidate == key)
        .collect::<Vec<_>>();
    if values.len() != 1 {
        return Err(ParquetOutputError::Schema(format!(
            "footer must contain exactly one {key}"
        )));
    }
    values[0].1.clone().ok_or_else(|| {
        ParquetOutputError::Schema(format!("footer key {key} must carry a string value"))
    })
}

fn validate_footer(
    metadata: &[(String, Option<String>)],
    provenance: &ArtifactProvenanceV1,
    canonical_json: &str,
) -> Result<String, ParquetOutputError> {
    let writer = required_footer_value(metadata, "cligen.writer.parquet")?;
    if writer.is_empty() {
        return Err(ParquetOutputError::Schema(
            "cligen.writer.parquet must be non-empty".to_owned(),
        ));
    }
    let expected = [
        ("cligen.output_schema", CLI_PARQUET_SCHEMA_ID.to_owned()),
        (
            "cligen.output_schema_version",
            CLI_PARQUET_SCHEMA_VERSION.to_owned(),
        ),
        ("cligen.provenance_schema_version", "1".to_owned()),
        (
            "cligen.station_input_schema",
            station_input_schema(provenance),
        ),
        ("cligen.station_model", station_model(provenance).to_owned()),
        (
            "cligen.generation_profile",
            generation_profile(provenance).to_owned(),
        ),
        ("cligen.calendar", "proleptic_gregorian".to_owned()),
        (
            "cligen.precipitation_representation",
            "parametric".to_owned(),
        ),
        ("cligen.coverage", coverage(provenance)?.to_owned()),
        ("cligen.writer.name", "cligen-rs".to_owned()),
        ("cligen.writer.version", provenance.producer.version.clone()),
        ("cligen.writer.parquet", writer.clone()),
        ("cligen.provenance", canonical_json.to_owned()),
    ];
    let actual = metadata
        .iter()
        .filter(|(key, _)| key.starts_with("cligen."))
        .collect::<Vec<_>>();
    if actual.len() != expected.len()
        || actual.iter().zip(expected.iter()).any(
            |((actual_key, actual_value), (expected_key, expected_value))| {
                actual_key != expected_key || actual_value.as_deref() != Some(expected_value)
            },
        )
    {
        return Err(ParquetOutputError::Schema(
            "ordered cligen footer metadata differs from revision 1".to_owned(),
        ));
    }
    Ok(writer)
}

fn validate_physical_policy(metadata: &ParquetMetaData) -> Result<(), ParquetOutputError> {
    let file = metadata.file_metadata();
    if file.version() != 2 || file.created_by() != Some(PARQUET_CREATED_BY) {
        return Err(ParquetOutputError::Schema(
            "Parquet version or created_by differs from writer-v1 policy".to_owned(),
        ));
    }
    if metadata.row_groups().is_empty() {
        return Err(ParquetOutputError::Schema(
            "Parquet file has no row groups".to_owned(),
        ));
    }
    for (group_index, group) in metadata.row_groups().iter().enumerate() {
        let is_last = group_index + 1 == metadata.num_row_groups();
        validate_row_group_policy(group, is_last)?;
    }
    Ok(())
}

fn validate_row_group_policy(
    group: &RowGroupMetaData,
    is_last: bool,
) -> Result<(), ParquetOutputError> {
    let rows = usize::try_from(group.num_rows()).map_err(|_| {
        ParquetOutputError::Schema("negative or overflowing row-group size".to_owned())
    })?;
    if rows == 0
        || rows > PARQUET_MAX_ROW_GROUP_ROWS
        || (!is_last && rows != PARQUET_MAX_ROW_GROUP_ROWS)
    {
        return Err(ParquetOutputError::Schema(
            "row groups do not follow the fixed 65,536-row policy".to_owned(),
        ));
    }
    if group.num_columns() != 17 {
        return Err(ParquetOutputError::Schema(
            "row group does not contain the 17 revision-1 columns".to_owned(),
        ));
    }
    for (column_index, column) in group.columns().iter().enumerate() {
        validate_column_policy(column, column_index)?;
    }
    Ok(())
}

fn validate_column_policy(
    column: &ColumnChunkMetaData,
    column_index: usize,
) -> Result<(), ParquetOutputError> {
    let dictionary = column
        .encodings()
        .any(|encoding| encoding == Encoding::RLE_DICTIONARY);
    if column.compression() != Compression::ZSTD(Default::default())
        || column.statistics().is_none()
        || dictionary != (column_index < 3)
    {
        return Err(ParquetOutputError::Schema(format!(
            "column {column_index} violates compression/statistics/dictionary policy"
        )));
    }
    Ok(())
}

fn validate_span(
    artifact: ParquetArtifactV1<'_>,
    rows: &[ClimateRowV1],
) -> Result<(), ParquetOutputError> {
    let count = u64::try_from(rows.len()).map_err(|_| {
        ParquetOutputError::InvalidArtifact("row count does not fit provenance u64".to_owned())
    })?;
    let first = rows
        .first()
        .map(|row| (row.year, row.month as u8, row.day_of_month as u8));
    let last = rows
        .last()
        .map(|row| (row.year, row.month as u8, row.day_of_month as u8));
    let actual = &artifact.provenance.actual;
    let expected_first = actual
        .first_date
        .map(|date| (date.year, date.month, date.day));
    let expected_last = actual
        .last_date
        .map(|date| (date.year, date.month, date.day));
    if count != actual.emitted_day_count || first != expected_first || last != expected_last {
        return Err(ParquetOutputError::InvalidArtifact(
            "row count/date span does not agree with provenance".to_owned(),
        ));
    }
    Ok(())
}

fn validate_destination(path: &Path) -> Result<(), ParquetOutputError> {
    if !path
        .file_name()
        .and_then(|name| name.to_str())
        .is_some_and(|name| name.ends_with(".cli.parquet"))
    {
        return Err(ParquetOutputError::InvalidDestination(path.to_path_buf()));
    }
    Ok(())
}

pub(crate) fn staging_path(path: &Path) -> Result<PathBuf, ParquetOutputError> {
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| ParquetOutputError::InvalidDestination(path.to_path_buf()))?;
    Ok(path.with_file_name(format!(".{name}.cligen-stage")))
}

fn publish_staging(
    staging: &Path,
    destination: &Path,
    overwrite: bool,
) -> Result<(), ParquetOutputError> {
    if overwrite {
        return fs::rename(staging, destination).map_err(ParquetOutputError::Io);
    }
    publish_staging_no_replace(staging, destination)
}

#[cfg(any(target_vendor = "apple", target_os = "linux", target_os = "redox"))]
fn publish_staging_no_replace(
    staging: &Path,
    destination: &Path,
) -> Result<(), ParquetOutputError> {
    use rustix::fs::{renameat_with, RenameFlags, CWD};

    renameat_with(CWD, staging, CWD, destination, RenameFlags::NOREPLACE).map_err(|source| {
        if source == rustix::io::Errno::EXIST {
            ParquetOutputError::Collision(destination.to_path_buf())
        } else {
            ParquetOutputError::Io(source.into())
        }
    })
}

#[cfg(not(any(target_vendor = "apple", target_os = "linux", target_os = "redox")))]
fn publish_staging_no_replace(
    staging: &Path,
    destination: &Path,
) -> Result<(), ParquetOutputError> {
    fs::hard_link(staging, destination).map_err(|source| {
        if source.kind() == std::io::ErrorKind::AlreadyExists {
            ParquetOutputError::Collision(destination.to_path_buf())
        } else {
            ParquetOutputError::Io(source)
        }
    })?;
    fs::remove_file(staging).map_err(ParquetOutputError::Io)
}

fn write_staging(
    file: File,
    artifact: ParquetArtifactV1<'_>,
    provenance_json: &str,
    rows: &[ClimateRowV1],
) -> Result<(), ParquetOutputError> {
    let schema = Arc::new(cli_parquet_schema_v1());
    let properties = writer_properties(artifact, provenance_json)?;
    let mut writer = ArrowWriter::try_new(file, schema.clone(), Some(properties))?;
    for chunk in rows.chunks(PARQUET_MAX_ROW_GROUP_ROWS) {
        writer.write(&record_batch(schema.clone(), chunk)?)?;
        writer.flush()?;
    }
    writer.close()?;
    Ok(())
}

fn writer_properties(
    artifact: ParquetArtifactV1<'_>,
    provenance_json: &str,
) -> Result<WriterProperties, ParquetOutputError> {
    let zstd = ZstdLevel::try_new(3).map_err(|source| {
        ParquetOutputError::InvalidArtifact(format!("invalid pinned ZSTD level: {source}"))
    })?;
    let metadata = vec![
        key_value("cligen.output_schema", CLI_PARQUET_SCHEMA_ID),
        key_value("cligen.output_schema_version", CLI_PARQUET_SCHEMA_VERSION),
        key_value("cligen.provenance_schema_version", "1"),
        key_value(
            "cligen.station_input_schema",
            &station_input_schema(artifact.provenance),
        ),
        key_value("cligen.station_model", station_model(artifact.provenance)),
        key_value(
            "cligen.generation_profile",
            generation_profile(artifact.provenance),
        ),
        key_value("cligen.calendar", "proleptic_gregorian"),
        key_value("cligen.precipitation_representation", "parametric"),
        key_value("cligen.coverage", coverage(artifact.provenance)?),
        key_value("cligen.writer.name", "cligen-rs"),
        key_value("cligen.writer.version", env!("CARGO_PKG_VERSION")),
        key_value("cligen.writer.parquet", PARQUET_WRITER_ID),
        key_value("cligen.provenance", provenance_json),
    ];
    Ok(WriterProperties::builder()
        .set_writer_version(WriterVersion::PARQUET_2_0)
        .set_compression(Compression::ZSTD(zstd))
        .set_created_by(PARQUET_CREATED_BY.to_owned())
        .set_max_row_group_row_count(Some(PARQUET_MAX_ROW_GROUP_ROWS))
        .set_statistics_enabled(EnabledStatistics::Chunk)
        .set_dictionary_enabled(false)
        .set_column_dictionary_enabled(ColumnPath::from("run_id"), true)
        .set_column_dictionary_enabled(ColumnPath::from("generation_profile"), true)
        .set_column_dictionary_enabled(ColumnPath::from("station_parameter_set_sha256"), true)
        .set_key_value_metadata(Some(metadata))
        .build())
}

fn key_value(key: &str, value: &str) -> KeyValue {
    KeyValue {
        key: key.to_owned(),
        value: Some(value.to_owned()),
    }
}

fn record_batch(
    schema: SchemaRef,
    rows: &[ClimateRowV1],
) -> Result<RecordBatch, ParquetOutputError> {
    let columns: Vec<ArrayRef> = vec![
        Arc::new(StringArray::from_iter_values(
            rows.iter().map(|row| row.run_id.as_str()),
        )),
        Arc::new(StringArray::from_iter_values(
            rows.iter().map(|row| row.generation_profile.as_str()),
        )),
        Arc::new(StringArray::from_iter_values(
            rows.iter()
                .map(|row| row.station_parameter_set_sha256.as_str()),
        )),
        Arc::new(Int32Array::from_iter_values(
            rows.iter().map(|row| row.sim_day_index),
        )),
        Arc::new(Int32Array::from_iter_values(
            rows.iter().map(|row| row.year),
        )),
        Arc::new(Int8Array::from_iter_values(
            rows.iter().map(|row| row.month),
        )),
        Arc::new(Int8Array::from_iter_values(
            rows.iter().map(|row| row.day_of_month),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.precip_mm),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.duration_h),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.time_to_peak_fraction),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.peak_intensity_ratio),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.tmax_c),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.tmin_c),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.solar_langley_day),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.wind_velocity_m_s),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.wind_direction_deg),
        )),
        Arc::new(Float64Array::from_iter_values(
            rows.iter().map(|row| row.tdew_c),
        )),
    ];
    Ok(RecordBatch::try_new(schema, columns)?)
}

fn rows_from_batch(batch: &RecordBatch) -> Result<Vec<ClimateRowV1>, ParquetOutputError> {
    let run_id = strings(batch, 0)?;
    let generation_profile = strings(batch, 1)?;
    let parameter_sha = strings(batch, 2)?;
    let sim_day_index = int32(batch, 3)?;
    let year = int32(batch, 4)?;
    let month = int8(batch, 5)?;
    let day = int8(batch, 6)?;
    let floats: Vec<&Float64Array> = (7..17)
        .map(|index| float64(batch, index))
        .collect::<Result<_, _>>()?;
    let mut rows = Vec::with_capacity(batch.num_rows());
    for index in 0..batch.num_rows() {
        rows.push(ClimateRowV1 {
            run_id: run_id.value(index).to_owned(),
            generation_profile: generation_profile.value(index).to_owned(),
            station_parameter_set_sha256: parameter_sha.value(index).to_owned(),
            sim_day_index: sim_day_index.value(index),
            year: year.value(index),
            month: month.value(index),
            day_of_month: day.value(index),
            precip_mm: floats[0].value(index),
            duration_h: floats[1].value(index),
            time_to_peak_fraction: floats[2].value(index),
            peak_intensity_ratio: floats[3].value(index),
            tmax_c: floats[4].value(index),
            tmin_c: floats[5].value(index),
            solar_langley_day: floats[6].value(index),
            wind_velocity_m_s: floats[7].value(index),
            wind_direction_deg: floats[8].value(index),
            tdew_c: floats[9].value(index),
        });
    }
    Ok(rows)
}

fn strings(batch: &RecordBatch, index: usize) -> Result<&StringArray, ParquetOutputError> {
    downcast(batch, index, "Utf8")
}

fn int32(batch: &RecordBatch, index: usize) -> Result<&Int32Array, ParquetOutputError> {
    downcast(batch, index, "Int32")
}

fn int8(batch: &RecordBatch, index: usize) -> Result<&Int8Array, ParquetOutputError> {
    downcast(batch, index, "Int8")
}

fn float64(batch: &RecordBatch, index: usize) -> Result<&Float64Array, ParquetOutputError> {
    downcast(batch, index, "Float64")
}

fn downcast<'a, T: Array + 'static>(
    batch: &'a RecordBatch,
    index: usize,
    expected: &str,
) -> Result<&'a T, ParquetOutputError> {
    batch
        .column(index)
        .as_any()
        .downcast_ref::<T>()
        .ok_or_else(|| {
            ParquetOutputError::Schema(format!(
                "column {index} did not decode as expected {expected} array"
            ))
        })
}
