use std::error::Error as _;
use std::fs::{self, File};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

use arrow_schema::DataType;
use cligen::modes::DailyRow;
use cligen::parquet_output::{
    cli_parquet_schema_v1, read_cli_parquet_v1, write_cli_parquet_v1, ParquetArtifactV1,
    ParquetOutputError, CLI_PARQUET_SCHEMA_ID, PARQUET_CREATED_BY, PARQUET_MAX_ROW_GROUP_ROWS,
};
use cligen::provenance::{
    ActualOutputV1, ArtifactIdentityV1, ArtifactProvenanceV1, CoverageV1, DateV1,
    EffectiveObservedV1, EffectiveOutputV1, EffectiveRunspecV1, EffectiveStationV1, FitIdentityV1,
    GenerationModeV1, GenerationProfileV1, GenerationProvenanceV1, InterpolationV1,
    ObservedInputV1, QcPolicyV1, RngSchemeV1, SchemaIdentityV1, StationCollectionIdentityV1,
    StationModelV1, StationProvenanceV1, StationSelectorV1,
};
use cligen::typed_output::{
    validate_climate_rows_v1, ClimateIdentityV1, ClimateRowV1, TypedOutputError,
};
use parquet::arrow::ArrowWriter;
use parquet::basic::{Compression, Encoding};
use parquet::file::reader::{FileReader, SerializedFileReader};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const HASH_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const HASH_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

#[test]
fn daily_projection_exactly_widens_f32_and_preserves_signed_zero() {
    let source = DailyRow {
        jd: 1,
        mo: 1,
        iyear: 1,
        xr: -0.0,
        dur: f32::from_bits(1),
        tpr: f32::MAX,
        xmav: f32::MIN_POSITIVE,
        tmxg: -12.25,
        tmng: 0.0,
        radg: 1.5,
        wv: -2.75,
        th: 359.75,
        tdp: -0.0,
    };
    let row = ClimateRowV1::try_from_daily(&identity(), 1, &source).unwrap();
    let widened = [
        row.precip_mm,
        row.duration_h,
        row.time_to_peak_fraction,
        row.peak_intensity_ratio,
        row.tmax_c,
        row.tmin_c,
        row.solar_langley_day,
        row.wind_velocity_m_s,
        row.wind_direction_deg,
        row.tdew_c,
    ];
    let original = [
        source.xr,
        source.dur,
        source.tpr,
        source.xmav,
        source.tmxg,
        source.tmng,
        source.radg,
        source.wv,
        source.th,
        source.tdp,
    ];
    for (actual, expected) in widened.into_iter().zip(original) {
        assert_eq!((actual as f32).to_bits(), expected.to_bits());
    }
    assert_eq!(row.precip_mm.to_bits(), (-0.0f64).to_bits());
    assert_eq!(row.tdew_c.to_bits(), (-0.0f64).to_bits());
}

#[test]
fn typed_and_parquet_errors_render_and_expose_sources() {
    let typed = [
        TypedOutputError::EmptyRows,
        TypedOutputError::InvalidIdentity("bad hash".to_owned()),
        TypedOutputError::InvalidDayIndex(0),
        TypedOutputError::NonContiguousIndex {
            expected: 2,
            actual: 3,
        },
        TypedOutputError::IdentityMismatch(2),
        TypedOutputError::InvalidDate {
            year: 1,
            month: 2,
            day: 30,
        },
        TypedOutputError::NonContiguousDate(2),
        TypedOutputError::NonFinite { name: "precip_mm" },
    ];
    for error in typed {
        assert!(!error.to_string().is_empty());
    }

    let errors = [
        ParquetOutputError::Collision(PathBuf::from("collision")),
        ParquetOutputError::InvalidArtifact("artifact".to_owned()),
        ParquetOutputError::InvalidDestination(PathBuf::from("destination")),
        ParquetOutputError::Schema("schema".to_owned()),
        ParquetOutputError::Typed(TypedOutputError::EmptyRows),
        ParquetOutputError::Io(std::io::Error::other("io")),
        ParquetOutputError::Arrow(arrow_schema::ArrowError::SchemaError("arrow".to_owned())),
        ParquetOutputError::Parquet(parquet::errors::ParquetError::General("parquet".to_owned())),
    ];
    for (index, error) in errors.iter().enumerate() {
        assert!(!error.to_string().is_empty());
        assert_eq!(error.source().is_some(), index >= 4);
    }
}

#[test]
fn row_validation_rejects_gaps_nonfinite_and_identity_drift() {
    let mut rows = two_rows();
    rows[1].day_of_month = 3;
    assert_eq!(
        validate_climate_rows_v1(&rows, &identity()).unwrap_err(),
        TypedOutputError::NonContiguousDate(2)
    );

    let mut rows = two_rows();
    rows[1].precip_mm = f64::NAN;
    assert_eq!(
        validate_climate_rows_v1(&rows, &identity()).unwrap_err(),
        TypedOutputError::NonFinite { name: "precip_mm" }
    );

    let mut rows = two_rows();
    rows[1].precip_mm = std::f64::consts::PI;
    assert_eq!(
        validate_climate_rows_v1(&rows, &identity()).unwrap_err(),
        TypedOutputError::NotExactF32 { name: "precip_mm" }
    );
    rows[1].precip_mm = f64::MAX;
    assert_eq!(
        validate_climate_rows_v1(&rows, &identity()).unwrap_err(),
        TypedOutputError::NotExactF32 { name: "precip_mm" }
    );

    let mut rows = two_rows();
    rows[1].run_id = "c".repeat(64);
    assert_eq!(
        validate_climate_rows_v1(&rows, &identity()).unwrap_err(),
        TypedOutputError::IdentityMismatch(2)
    );

    let mut malformed_identity = identity();
    malformed_identity.run_id = "A".repeat(64);
    assert!(matches!(
        malformed_identity.validate(),
        Err(TypedOutputError::InvalidIdentity(_))
    ));
    let mut rows = two_rows();
    rows[1].sim_day_index = 3;
    assert_eq!(
        validate_climate_rows_v1(&rows, &identity()).unwrap_err(),
        TypedOutputError::NonContiguousIndex {
            expected: 2,
            actual: 3
        }
    );
    assert_eq!(
        validate_climate_rows_v1(&[], &identity()).unwrap_err(),
        TypedOutputError::EmptyRows
    );
}

#[test]
fn typed_dates_follow_proleptic_gregorian_year_one_and_leap_rules() {
    let base = two_rows().remove(0);
    for dates in [
        vec![(1, 2, 28), (1, 3, 1)],
        vec![(4, 2, 28), (4, 2, 29), (4, 3, 1)],
        vec![(100, 2, 28), (100, 3, 1)],
        vec![(400, 2, 28), (400, 2, 29), (400, 3, 1)],
    ] {
        let rows = dates
            .into_iter()
            .enumerate()
            .map(|(offset, (year, month, day))| {
                let mut row = base.clone();
                row.sim_day_index = i32::try_from(offset + 1).unwrap();
                (row.year, row.month, row.day_of_month) = (year, month, day);
                row
            })
            .collect::<Vec<_>>();
        validate_climate_rows_v1(&rows, &identity()).unwrap();
    }
}

#[test]
fn published_schema_has_exact_order_types_nullability_and_field_metadata() {
    let schema = cli_parquet_schema_v1();
    let manifest: serde_json::Value = serde_json::from_str(include_str!(
        "../../../docs/specifications/cli-parquet-v1.fields.json"
    ))
    .unwrap();
    assert_eq!(manifest["output_schema"], CLI_PARQUET_SCHEMA_ID);
    assert_eq!(manifest["output_schema_version"], 1);
    let manifest_fields = manifest["fields"].as_array().unwrap();
    assert_eq!(schema.fields().len(), 17);
    assert_eq!(manifest_fields.len(), schema.fields().len());
    assert_eq!(
        schema
            .fields()
            .iter()
            .map(|field| field.name().as_str())
            .collect::<Vec<_>>(),
        [
            "run_id",
            "generation_profile",
            "station_parameter_set_sha256",
            "sim_day_index",
            "year",
            "month",
            "day_of_month",
            "precip_mm",
            "duration_h",
            "time_to_peak_fraction",
            "peak_intensity_ratio",
            "tmax_c",
            "tmin_c",
            "solar_langley_day",
            "wind_velocity_m_s",
            "wind_direction_deg",
            "tdew_c",
        ]
    );
    let expected_types = [
        DataType::Utf8,
        DataType::Utf8,
        DataType::Utf8,
        DataType::Int32,
        DataType::Int32,
        DataType::Int8,
        DataType::Int8,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
        DataType::Float64,
    ];
    for (field, expected_type) in schema.fields().iter().zip(expected_types) {
        assert_eq!(field.data_type(), &expected_type);
        assert!(!field.is_nullable());
        assert_eq!(field.metadata().len(), 2);
        assert!(field.metadata().contains_key("units"));
        assert!(field.metadata().contains_key("description"));
        assert!(!field.metadata()["description"].is_empty());
    }
    for (field, published) in schema.fields().iter().zip(manifest_fields) {
        assert_eq!(published["name"].as_str().unwrap(), field.name());
        assert_eq!(
            published["nullable"].as_bool().unwrap(),
            field.is_nullable()
        );
        assert_eq!(
            published["units"].as_str().unwrap(),
            field.metadata()["units"]
        );
        assert_eq!(
            published["description"].as_str().unwrap(),
            field.metadata()["description"]
        );
        let arrow_type = match field.data_type() {
            DataType::Utf8 => "utf8",
            DataType::Int32 => "int32",
            DataType::Int8 => "int8",
            DataType::Float64 => "float64",
            other => panic!("unexpected output type {other:?}"),
        };
        assert_eq!(published["arrow_type"].as_str().unwrap(), arrow_type);
    }
    assert_eq!(schema.metadata().len(), 2);
    assert_eq!(
        schema.metadata()["cligen.output_schema"],
        CLI_PARQUET_SCHEMA_ID
    );
    assert_eq!(schema.metadata()["cligen.output_schema_version"], "1");
}

#[test]
fn parquet_readback_preserves_rows_metadata_and_pinned_physical_policy() {
    let dir = temp_dir("readback");
    let path = dir.join("weather.cli.parquet");
    let rows = two_rows();
    write_test_parquet(&path, &rows, false).unwrap();

    let readback = read_cli_parquet_v1(&path).unwrap();
    assert_eq!(readback.rows, rows);
    assert_eq!(readback.rows[0].precip_mm.to_bits(), (-0.0f64).to_bits());
    assert_eq!(readback.rows[0].tmin_c.to_bits(), (-0.0f64).to_bits());
    assert_eq!(
        (readback.rows[0].duration_h as f32).to_bits(),
        f32::from_bits(1).to_bits()
    );
    assert_eq!(
        (readback.rows[0].time_to_peak_fraction as f32).to_bits(),
        f32::MAX.to_bits()
    );
    assert_eq!(readback.row_group_rows, [2]);
    assert_eq!(readback.created_by.as_deref(), Some(PARQUET_CREATED_BY));
    assert_eq!(readback.writer_version, 2);
    assert_eq!(
        readback
            .footer_metadata
            .iter()
            .filter(|(key, _)| key.starts_with("cligen."))
            .map(|(key, _)| key.as_str())
            .collect::<Vec<_>>(),
        expected_footer_keys()
    );
    let persisted = SerializedFileReader::new(File::open(&path).unwrap()).unwrap();
    let columns = persisted.metadata().row_group(0).columns();
    assert!(columns
        .iter()
        .all(|column| column.compression() == Compression::ZSTD(Default::default())));
    assert!(columns.iter().all(|column| column.statistics().is_some()));
    for (index, column) in columns.iter().enumerate() {
        let dictionary = column
            .encodings()
            .any(|encoding| encoding == Encoding::RLE_DICTIONARY);
        assert_eq!(dictionary, index < 3, "column {index}");
    }
    drop(persisted);
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn repeat_writes_are_byte_identical_under_the_exact_pin() {
    let dir = temp_dir("repeat");
    let first = dir.join("first.cli.parquet");
    let second = dir.join("second.cli.parquet");
    let rows = two_rows();
    write_test_parquet(&first, &rows, false).unwrap();
    write_test_parquet(&second, &rows, false).unwrap();
    assert_eq!(fs::read(first).unwrap(), fs::read(second).unwrap());
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn row_groups_are_one_fixed_size_batch_plus_the_remainder() {
    let dir = temp_dir("groups");
    let path = dir.join("groups.cli.parquet");
    let rows = many_rows(PARQUET_MAX_ROW_GROUP_ROWS + 1);
    write_test_parquet(&path, &rows, false).unwrap();
    assert_eq!(
        read_cli_parquet_v1(&path).unwrap().row_group_rows,
        [PARQUET_MAX_ROW_GROUP_ROWS as i64, 1]
    );
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn conformance_readback_rejects_schema_only_external_parquet() {
    let dir = temp_dir("external-invalid");
    let path = dir.join("invalid.cli.parquet");
    let writer = ArrowWriter::try_new(
        File::create(&path).unwrap(),
        Arc::new(cli_parquet_schema_v1()),
        None,
    )
    .unwrap();
    writer.close().unwrap();
    assert!(matches!(
        read_cli_parquet_v1(&path),
        Err(ParquetOutputError::Schema(_))
    ));
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn no_overwrite_publication_is_atomic_against_a_late_collision() {
    let dir = temp_dir("publish-race");
    let path = dir.join("weather.cli.parquet");
    let staging = dir.join(".weather.cli.parquet.cligen-stage");
    let collision_path = path.clone();
    let adversary = std::thread::spawn(move || {
        while !staging.exists() {
            std::thread::yield_now();
        }
        fs::write(collision_path, b"late collision").unwrap();
    });
    let rows = many_rows(PARQUET_MAX_ROW_GROUP_ROWS);
    let result = write_test_parquet(&path, &rows, false);
    adversary.join().unwrap();
    assert!(matches!(result, Err(ParquetOutputError::Collision(_))));
    assert_eq!(fs::read(&path).unwrap(), b"late collision");
    assert!(!dir.join(".weather.cli.parquet.cligen-stage").exists());
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn failures_and_collisions_never_publish_a_partial_final_file() {
    let dir = temp_dir("failures");
    let path = dir.join("weather.cli.parquet");
    let mut invalid = two_rows();
    invalid[0].duration_h = f64::INFINITY;
    assert!(matches!(
        write_test_parquet(&path, &invalid, false),
        Err(ParquetOutputError::Typed(TypedOutputError::NonFinite {
            name: "duration_h"
        }))
    ));
    assert!(!path.exists());

    let rows = two_rows();
    let mut wrong_span = provenance_for_rows(&rows);
    wrong_span.actual.emitted_day_count = 3;
    assert!(matches!(
        write_cli_parquet_v1(
            &path,
            ParquetArtifactV1 {
                provenance: &wrong_span
            },
            &rows,
            false
        ),
        Err(ParquetOutputError::InvalidArtifact(_))
    ));
    assert!(!path.exists());

    let mut wrong_writer = provenance_for_rows(&rows);
    wrong_writer.producer.version = "0.0.0".to_owned();
    assert!(matches!(
        write_cli_parquet_v1(
            &path,
            ParquetArtifactV1 {
                provenance: &wrong_writer
            },
            &rows,
            false
        ),
        Err(ParquetOutputError::InvalidArtifact(_))
    ));
    assert!(!path.exists());

    fs::write(&path, b"existing").unwrap();
    assert!(matches!(
        write_test_parquet(&path, &two_rows(), false),
        Err(ParquetOutputError::Collision(_))
    ));
    assert_eq!(fs::read(&path).unwrap(), b"existing");

    write_test_parquet(&path, &two_rows(), true).unwrap();
    assert_eq!(read_cli_parquet_v1(&path).unwrap().rows, two_rows());

    fs::remove_file(&path).unwrap();
    let staging = dir.join(".weather.cli.parquet.cligen-stage");
    fs::write(&staging, b"stale").unwrap();
    assert!(matches!(
        write_test_parquet(&path, &two_rows(), true),
        Err(ParquetOutputError::Collision(ref collision)) if collision == &staging
    ));
    assert!(!path.exists());
    assert_eq!(fs::read(staging).unwrap(), b"stale");
    fs::remove_dir_all(dir).unwrap();
}

fn identity() -> ClimateIdentityV1 {
    let runspec = effective_runspec();
    ClimateIdentityV1 {
        run_id: runspec.sha256().unwrap(),
        generation_profile: "faithful_5_32_3".to_owned(),
        station_parameter_set_sha256: HASH_B.to_owned(),
    }
}

fn write_test_parquet(
    path: &std::path::Path,
    rows: &[ClimateRowV1],
    overwrite: bool,
) -> Result<(), ParquetOutputError> {
    let provenance = provenance_for_rows(rows);
    write_cli_parquet_v1(
        path,
        ParquetArtifactV1 {
            provenance: &provenance,
        },
        rows,
        overwrite,
    )
}

fn provenance_for_rows(rows: &[ClimateRowV1]) -> ArtifactProvenanceV1 {
    let first = rows.first().unwrap();
    let last = rows.last().unwrap();
    let runspec = effective_runspec();
    ArtifactProvenanceV1::new(
        StationProvenanceV1 {
            input_schema: SchemaIdentityV1::legacy_station(),
            input_sha256: HASH_A.to_owned(),
            model: StationModelV1::FixedMonthly5323,
            parameter_set_sha256: HASH_B.to_owned(),
            fit: FitIdentityV1::unreported(),
            collection: StationCollectionIdentityV1::unreported(),
            legacy_source_sha256: HASH_A.to_owned(),
        },
        GenerationProvenanceV1 {
            profile: GenerationProfileV1::Faithful5323,
            qc_policy: Some(QcPolicyV1::Faithful),
            mode: GenerationModeV1::Observed,
            interpolation: InterpolationV1::None,
            rng_scheme: RngSchemeV1::CligenRandn5323,
            burn_per_stream: 0,
        },
        runspec,
        Some(ObservedInputV1 {
            schema: SchemaIdentityV1::legacy_observed(),
            input_sha256: HASH_B.to_owned(),
        }),
        ActualOutputV1 {
            emitted_day_count: rows.len() as u64,
            first_date: Some(DateV1 {
                year: first.year,
                month: first.month as u8,
                day: first.day_of_month as u8,
            }),
            last_date: Some(DateV1 {
                year: last.year,
                month: last.month as u8,
                day: last.day_of_month as u8,
            }),
            coverage: CoverageV1::ObservedSourceEnd,
        },
        ArtifactIdentityV1::cli_parquet(),
    )
    .unwrap()
}

fn effective_runspec() -> EffectiveRunspecV1 {
    EffectiveRunspecV1 {
        cligen_runspec: 1,
        station: EffectiveStationV1 {
            selector: StationSelectorV1::LegacyPar,
            lexical_path: "stations/test.par".to_owned(),
            input_sha256: HASH_A.to_owned(),
        },
        mode: GenerationModeV1::Observed,
        begin_year: Some(1),
        years: Some(1_000),
        interpolation: InterpolationV1::None,
        burn: 0,
        generation_profile: GenerationProfileV1::Faithful5323,
        qc_filter: Some(QcPolicyV1::Faithful),
        observed: Some(EffectiveObservedV1 {
            lexical_path: "inputs/test.prn".to_owned(),
            input_sha256: HASH_B.to_owned(),
        }),
        storm: None,
        output: EffectiveOutputV1 {
            cli_lexical_path: "out/test.cli".to_owned(),
            parquet_lexical_path: Some("out/test.cli.parquet".to_owned()),
            quality: false,
            overwrite: false,
            command_echo: "-itest.par".to_owned(),
        },
    }
}

fn two_rows() -> Vec<ClimateRowV1> {
    [1, 2]
        .into_iter()
        .map(|day| {
            ClimateRowV1::try_from_daily(
                &identity(),
                day,
                &DailyRow {
                    jd: day,
                    mo: 1,
                    iyear: 1,
                    xr: if day == 1 { -0.0 } else { 2.5 },
                    dur: if day == 1 { f32::from_bits(1) } else { 1.25 },
                    tpr: if day == 1 { f32::MAX } else { 0.5 },
                    xmav: 3.0,
                    tmxg: 20.0,
                    tmng: -0.0,
                    radg: 300.0,
                    wv: 4.5,
                    th: 180.0,
                    tdp: 5.0,
                },
            )
            .unwrap()
        })
        .collect()
}

fn many_rows(count: usize) -> Vec<ClimateRowV1> {
    let template = two_rows().remove(0);
    let mut date = (1, 1i8, 1i8);
    (1..=count)
        .map(|index| {
            let mut row = template.clone();
            row.sim_day_index = i32::try_from(index).unwrap();
            (row.year, row.month, row.day_of_month) = date;
            date = test_next_date(date);
            row
        })
        .collect()
}

fn test_next_date((year, month, day): (i32, i8, i8)) -> (i32, i8, i8) {
    let mut days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if year % 400 == 0 || (year % 4 == 0 && year % 100 != 0) {
        days[1] = 29;
    }
    if i32::from(day) < days[(month - 1) as usize] {
        (year, month, day + 1)
    } else if month < 12 {
        (year, month + 1, 1)
    } else {
        (year + 1, 1, 1)
    }
}

fn expected_footer_keys() -> Vec<&'static str> {
    vec![
        "cligen.output_schema",
        "cligen.output_schema_version",
        "cligen.provenance_schema_version",
        "cligen.station_input_schema",
        "cligen.station_model",
        "cligen.generation_profile",
        "cligen.calendar",
        "cligen.precipitation_representation",
        "cligen.coverage",
        "cligen.writer.name",
        "cligen.writer.version",
        "cligen.writer.parquet",
        "cligen.provenance",
    ]
}

fn temp_dir(label: &str) -> PathBuf {
    let sequence = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
    let path = std::env::temp_dir().join(format!(
        "cligen-parquet-{label}-{}-{sequence}",
        std::process::id()
    ));
    if path.exists() {
        fs::remove_dir_all(&path).unwrap();
    }
    fs::create_dir(&path).unwrap();
    path
}
