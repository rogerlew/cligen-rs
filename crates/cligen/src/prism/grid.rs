//! Strict local PRISM runtime-grid intake and point query.

use std::fs::{self, File};
use std::io::{Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use super::{sha256_file, Distribution, PrismError};

const LAYER_COUNT: usize = 36;
const BYTES_PER_CELL: u64 = (LAYER_COUNT * std::mem::size_of::<f32>()) as u64;
type MonthlyNormals = ([f32; 12], [f32; 12], [f32; 12]);

/// One layer declaration in the query-optimized grid.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Layer {
    pub index: usize,
    pub variable: String,
    pub month: u8,
    pub units: String,
}

/// One payload-relative file identity.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GridFile {
    pub path: String,
    pub bytes: u64,
    pub sha256: String,
}

/// Strict runtime grid contract.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GridManifest {
    pub schema_version: u32,
    pub bundle_id: String,
    pub bundle_version: String,
    pub source_manifest_sha256: String,
    pub width: usize,
    pub height: usize,
    pub crs: String,
    pub transform: [f64; 9],
    pub source_nodata: f32,
    pub layout: String,
    pub byte_order: String,
    pub scalar_type: String,
    pub layers: Vec<Layer>,
    pub validity: String,
    pub valid_cell_count: u64,
    pub normals: GridFile,
    pub validity_mask: GridFile,
}

impl GridManifest {
    /// Read and validate the synced grid manifest against the embedded
    /// distribution.
    pub fn load(root: &Path, distribution: &Distribution) -> Result<Self, PrismError> {
        let path = root.join("grid-manifest.json");
        let bytes = fs::read(&path)
            .map_err(|source| super::io_error(format!("read {}", path.display()), source))?;
        verify_hash(
            "grid-manifest.json",
            &crate::quality::sha256_hex(&bytes),
            &distribution.grid_manifest_sha256,
        )?;
        let value: Self = serde_json::from_slice(&bytes)
            .map_err(|error| PrismError::InvalidGrid(error.to_string()))?;
        value.validate(distribution)?;
        Ok(value)
    }

    fn validate(&self, distribution: &Distribution) -> Result<(), PrismError> {
        if !self.identity_matches(distribution) || !self.shape_matches() || !self.encoding_matches()
        {
            return Err(PrismError::InvalidGrid(
                "grid scalar identity does not match revision 1".to_owned(),
            ));
        }
        validate_transform(self.transform)?;
        validate_layers(&self.layers)?;
        validate_file_contract(
            &self.normals,
            "normals.f32le",
            self.width as u64 * self.height as u64 * BYTES_PER_CELL,
        )?;
        let cells = self.width as u64 * self.height as u64;
        validate_file_contract(&self.validity_mask, "validity-mask.bin", cells.div_ceil(8))
    }

    fn identity_matches(&self, distribution: &Distribution) -> bool {
        self.schema_version == 1
            && self.bundle_id == distribution.bundle_id
            && self.bundle_version == distribution.version
            && self.source_manifest_sha256 == distribution.source_manifest_sha256
    }

    fn shape_matches(&self) -> bool {
        self.width == 1405 && self.height == 621 && self.crs == "EPSG:4269"
    }

    fn encoding_matches(&self) -> bool {
        self.layout == "cell-major"
            && self.byte_order == "little-endian"
            && self.scalar_type == "float32"
            && self.source_nodata == -9999.0
            && self.valid_cell_count > 0
            && self.validity == "one little-endian bit per cell; set iff all 36 layers are valid"
    }

    /// Full content verification performed by sync before cache publication.
    pub fn verify_files(&self, root: &Path) -> Result<(), PrismError> {
        for (label, identity) in [
            ("normals.f32le", &self.normals),
            ("validity-mask.bin", &self.validity_mask),
        ] {
            verify_grid_file(root, label, identity)?;
        }
        Ok(())
    }
}

fn verify_grid_file(root: &Path, label: &str, identity: &GridFile) -> Result<(), PrismError> {
    let path = root.join(&identity.path);
    let actual_bytes = fs::metadata(&path)
        .map_err(|source| super::io_error(format!("stat {}", path.display()), source))?
        .len();
    if actual_bytes != identity.bytes {
        return Err(PrismError::InvalidGrid(format!(
            "{label} size: expected {}, got {actual_bytes}",
            identity.bytes
        )));
    }
    verify_hash(label, &sha256_file(&path)?, &identity.sha256)
}

fn validate_transform(transform: [f64; 9]) -> Result<(), PrismError> {
    let expected = [
        0.041666666667,
        0.0,
        -125.0208333333335,
        0.0,
        -0.041666666667,
        49.9375000000005,
        0.0,
        0.0,
        1.0,
    ];
    if transform == expected {
        Ok(())
    } else {
        Err(PrismError::InvalidGrid(
            "affine transform does not match the registered grid".to_owned(),
        ))
    }
}

fn validate_layers(layers: &[Layer]) -> Result<(), PrismError> {
    if layers.len() != LAYER_COUNT {
        return Err(PrismError::InvalidGrid(
            "grid must contain exactly 36 layers".to_owned(),
        ));
    }
    for (index, layer) in layers.iter().enumerate() {
        let variable_index = index / 12;
        let expected_variable = ["ppt", "tmax", "tmin"][variable_index];
        let expected_units =
            ["millimetres/month", "degrees Celsius", "degrees Celsius"][variable_index];
        if layer.index != index
            || layer.month as usize != index % 12 + 1
            || layer.variable != expected_variable
            || layer.units != expected_units
        {
            return Err(PrismError::InvalidGrid(format!(
                "layer {index} does not match the registered order"
            )));
        }
    }
    Ok(())
}

fn validate_file_contract(file: &GridFile, path: &str, bytes: u64) -> Result<(), PrismError> {
    super::validate_sha256(&format!("{path}.sha256"), &file.sha256)?;
    if file.path == path && file.bytes == bytes {
        Ok(())
    } else {
        Err(PrismError::InvalidGrid(format!(
            "{path} path/size does not match revision 1"
        )))
    }
}

fn verify_hash(label: &str, actual: &str, expected: &str) -> Result<(), PrismError> {
    if actual == expected {
        Ok(())
    } else {
        Err(PrismError::HashMismatch {
            label: label.to_owned(),
            expected: expected.to_owned(),
            actual: actual.to_owned(),
        })
    }
}

/// Raw and converted monthly normals for one registered cell.
#[derive(Debug, Clone, Serialize)]
pub struct NormalsReceipt {
    pub schema_version: u32,
    pub bundle_id: String,
    pub bundle_version: String,
    pub grid_manifest_sha256: String,
    pub source_manifest_sha256: String,
    pub attribution: String,
    pub requested_longitude: f64,
    pub requested_latitude: f64,
    pub row: usize,
    pub column: usize,
    pub cell_center_longitude: f64,
    pub cell_center_latitude: f64,
    pub monthly_ppt_mm: [f32; 12],
    pub monthly_tmax_c: [f32; 12],
    pub monthly_tmin_c: [f32; 12],
    pub monthly_ppt_in: [f64; 12],
    pub monthly_tmax_f: [f64; 12],
    pub monthly_tmin_f: [f64; 12],
}

impl NormalsReceipt {
    /// PRISM precipitation totals converted to inches.
    #[must_use]
    pub fn monthly_ppt_in(&self) -> [f64; 12] {
        self.monthly_ppt_in
    }

    /// PRISM Tmax converted to Fahrenheit.
    #[must_use]
    pub fn monthly_tmax_f(&self) -> [f64; 12] {
        self.monthly_tmax_f
    }

    /// PRISM Tmin converted to Fahrenheit.
    #[must_use]
    pub fn monthly_tmin_f(&self) -> [f64; 12] {
        self.monthly_tmin_f
    }
}

/// Open a synced grid and query one containing cell. No network path is
/// reachable from this function.
pub fn query(
    distribution: &Distribution,
    cache_root: &Path,
    longitude: f64,
    latitude: f64,
) -> Result<NormalsReceipt, PrismError> {
    validate_coordinate(longitude, latitude)?;
    let root = distribution.cache_dir(cache_root);
    super::sync::require_synced(distribution, cache_root)?;
    query_synced(distribution, &root, longitude, latitude)
}

fn query_synced(
    distribution: &Distribution,
    root: &Path,
    longitude: f64,
    latitude: f64,
) -> Result<NormalsReceipt, PrismError> {
    let manifest = GridManifest::load(root, distribution)?;
    let (row, column) = cell_indices(&manifest, longitude, latitude)?;
    let (ppt, tmax, tmin) = read_normals(root, &manifest, row, column)?;
    Ok(build_receipt(
        distribution,
        &manifest,
        longitude,
        latitude,
        row,
        column,
        ppt,
        tmax,
        tmin,
    ))
}

fn read_normals(
    root: &Path,
    manifest: &GridManifest,
    row: usize,
    column: usize,
) -> Result<MonthlyNormals, PrismError> {
    require_valid_cell(
        &root.join(&manifest.validity_mask.path),
        manifest,
        row,
        column,
    )?;
    let values = read_cell(&root.join(&manifest.normals.path), manifest, row, column)?;
    let mut ppt = [0.0_f32; 12];
    let mut tmax = [0.0_f32; 12];
    let mut tmin = [0.0_f32; 12];
    ppt.copy_from_slice(&values[0..12]);
    tmax.copy_from_slice(&values[12..24]);
    tmin.copy_from_slice(&values[24..36]);
    validate_values(&ppt, &tmax, &tmin, manifest.source_nodata)?;
    Ok((ppt, tmax, tmin))
}

#[allow(clippy::too_many_arguments)]
fn build_receipt(
    distribution: &Distribution,
    manifest: &GridManifest,
    longitude: f64,
    latitude: f64,
    row: usize,
    column: usize,
    ppt: [f32; 12],
    tmax: [f32; 12],
    tmin: [f32; 12],
) -> NormalsReceipt {
    let x = manifest.transform[2] + (column as f64 + 0.5) * manifest.transform[0];
    let y = manifest.transform[5] + (row as f64 + 0.5) * manifest.transform[4];
    NormalsReceipt {
        schema_version: 1,
        bundle_id: distribution.bundle_id.clone(),
        bundle_version: distribution.version.clone(),
        grid_manifest_sha256: distribution.grid_manifest_sha256.clone(),
        source_manifest_sha256: distribution.source_manifest_sha256.clone(),
        attribution: distribution.attribution.clone(),
        requested_longitude: longitude,
        requested_latitude: latitude,
        row,
        column,
        cell_center_longitude: x,
        cell_center_latitude: y,
        monthly_ppt_mm: ppt,
        monthly_tmax_c: tmax,
        monthly_tmin_c: tmin,
        monthly_ppt_in: ppt.map(|value| f64::from(value) / 25.4),
        monthly_tmax_f: tmax.map(|value| f64::from(value) * 9.0 / 5.0 + 32.0),
        monthly_tmin_f: tmin.map(|value| f64::from(value) * 9.0 / 5.0 + 32.0),
    }
}

fn validate_coordinate(longitude: f64, latitude: f64) -> Result<(), PrismError> {
    if longitude.is_finite()
        && latitude.is_finite()
        && (-180.0..=180.0).contains(&longitude)
        && (-90.0..=90.0).contains(&latitude)
    {
        Ok(())
    } else {
        Err(PrismError::InvalidCoordinate(
            "longitude must be in [-180,180] and latitude in [-90,90]".to_owned(),
        ))
    }
}

fn cell_indices(
    manifest: &GridManifest,
    longitude: f64,
    latitude: f64,
) -> Result<(usize, usize), PrismError> {
    let column = ((longitude - manifest.transform[2]) / manifest.transform[0]).floor();
    let row = ((latitude - manifest.transform[5]) / manifest.transform[4]).floor();
    if column >= 0.0 && row >= 0.0 && column < manifest.width as f64 && row < manifest.height as f64
    {
        Ok((row as usize, column as usize))
    } else {
        Err(PrismError::InvalidCoordinate(
            "coordinate is outside the registered CONUS grid".to_owned(),
        ))
    }
}

fn cell_number(manifest: &GridManifest, row: usize, column: usize) -> u64 {
    row as u64 * manifest.width as u64 + column as u64
}

fn require_valid_cell(
    path: &Path,
    manifest: &GridManifest,
    row: usize,
    column: usize,
) -> Result<(), PrismError> {
    let cell = cell_number(manifest, row, column);
    let mut input = File::open(path)
        .map_err(|source| super::io_error(format!("open {}", path.display()), source))?;
    input
        .seek(SeekFrom::Start(cell / 8))
        .map_err(|source| super::io_error("seek PRISM validity mask", source))?;
    let mut byte = [0_u8; 1];
    input
        .read_exact(&mut byte)
        .map_err(|source| super::io_error("read PRISM validity mask", source))?;
    if byte[0] & (1 << (cell % 8)) != 0 {
        Ok(())
    } else {
        Err(PrismError::InvalidCoordinate(
            "coordinate resolves to a masked PRISM cell".to_owned(),
        ))
    }
}

fn read_cell(
    path: &Path,
    manifest: &GridManifest,
    row: usize,
    column: usize,
) -> Result<[f32; LAYER_COUNT], PrismError> {
    let offset = cell_number(manifest, row, column) * BYTES_PER_CELL;
    let mut input = File::open(path)
        .map_err(|source| super::io_error(format!("open {}", path.display()), source))?;
    input
        .seek(SeekFrom::Start(offset))
        .map_err(|source| super::io_error("seek PRISM normals", source))?;
    let mut raw = [0_u8; LAYER_COUNT * 4];
    input
        .read_exact(&mut raw)
        .map_err(|source| super::io_error("read PRISM normals", source))?;
    Ok(std::array::from_fn(|index| {
        f32::from_le_bytes(
            raw[index * 4..index * 4 + 4]
                .try_into()
                .expect("four bytes"),
        )
    }))
}

fn validate_values(
    ppt: &[f32; 12],
    tmax: &[f32; 12],
    tmin: &[f32; 12],
    nodata: f32,
) -> Result<(), PrismError> {
    for month in 0..12 {
        let values = [ppt[month], tmax[month], tmin[month]];
        if values
            .iter()
            .any(|value| !value.is_finite() || *value == nodata)
            || ppt[month] < 0.0
            || tmax[month] < tmin[month]
        {
            return Err(PrismError::InvalidGrid(format!(
                "invalid monthly values at month {}",
                month + 1
            )));
        }
    }
    Ok(())
}

/// Paths required by the runtime payload. Used by sync's allow-list.
#[must_use]
pub fn required_runtime_files() -> [&'static str; 6] {
    [
        "ATTRIBUTION.md",
        "BUILD-RECEIPT.json",
        "grid-manifest.json",
        "normals.f32le",
        "source-manifest.json",
        "validity-mask.bin",
    ]
}

/// Resolve a required payload path without accepting a caller-controlled
/// relative shape.
pub(crate) fn required_path(root: &Path, name: &str) -> Result<PathBuf, PrismError> {
    if required_runtime_files().contains(&name) {
        Ok(root.join(name))
    } else {
        Err(PrismError::InvalidGrid(format!(
            "unknown runtime member {name:?}"
        )))
    }
}

#[cfg(test)]
mod tests {
    use super::{cell_indices, validate_layers, GridManifest, Layer};
    use crate::prism::{Distribution, PrismError};

    fn manifest() -> GridManifest {
        let distribution = Distribution::embedded();
        GridManifest {
            schema_version: 1,
            bundle_id: distribution.bundle_id,
            bundle_version: distribution.version,
            source_manifest_sha256: distribution.source_manifest_sha256,
            width: 1405,
            height: 621,
            crs: "EPSG:4269".to_owned(),
            transform: [
                0.041666666667,
                0.0,
                -125.0208333333335,
                0.0,
                -0.041666666667,
                49.9375000000005,
                0.0,
                0.0,
                1.0,
            ],
            source_nodata: -9999.0,
            layout: "cell-major".to_owned(),
            byte_order: "little-endian".to_owned(),
            scalar_type: "float32".to_owned(),
            layers: Vec::new(),
            validity: String::new(),
            valid_cell_count: 1,
            normals: super::GridFile {
                path: "normals.f32le".to_owned(),
                bytes: 125_640_720,
                sha256: "0".repeat(64),
            },
            validity_mask: super::GridFile {
                path: "validity-mask.bin".to_owned(),
                bytes: 109_064,
                sha256: "0".repeat(64),
            },
        }
    }

    #[test]
    fn containing_cell_contract_includes_northwest_and_rejects_east_edge() {
        let value = manifest();
        assert_eq!(
            cell_indices(&value, -125.0208333333335, 49.9375000000005).unwrap(),
            (0, 0)
        );
        let east = value.transform[2] + value.width as f64 * value.transform[0];
        assert!(matches!(
            cell_indices(&value, east, 40.0),
            Err(PrismError::InvalidCoordinate(_))
        ));
    }

    #[test]
    fn layer_contract_rejects_wrong_order() {
        let mut layers: Vec<Layer> = (0..36)
            .map(|index| Layer {
                index,
                variable: ["ppt", "tmax", "tmin"][index / 12].to_owned(),
                month: (index % 12 + 1) as u8,
                units: ["millimetres/month", "degrees Celsius", "degrees Celsius"][index / 12]
                    .to_owned(),
            })
            .collect();
        assert!(validate_layers(&layers).is_ok());
        layers[13].month = 1;
        assert!(validate_layers(&layers).is_err());
    }

    #[test]
    fn revision_one_manifest_validates() {
        let mut value = manifest();
        value.layers = (0..36)
            .map(|index| Layer {
                index,
                variable: ["ppt", "tmax", "tmin"][index / 12].to_owned(),
                month: (index % 12 + 1) as u8,
                units: ["millimetres/month", "degrees Celsius", "degrees Celsius"][index / 12]
                    .to_owned(),
            })
            .collect();
        value.validity =
            "one little-endian bit per cell; set iff all 36 layers are valid".to_owned();
        assert!(value.validate(&Distribution::embedded()).is_ok());
    }
}
