//! `cligen stations list` / `nearest` over the shipped catalogs
//! (SPEC-STATION-DB §Subcommands).

use std::path::{Path, PathBuf};

use serde::Serialize;

use crate::stations::{resolve_par, Collection, Manifests, StationsError};

/// Mean-Earth-radius sphere for the great-circle distance, km
/// (SPEC-STATION-DB §Subcommands).
pub const EARTH_RADIUS_KM: f64 = 6371.0088;

/// One `list` row.
#[derive(Debug, Clone, Serialize)]
pub struct ListRow {
    pub name: String,
    pub version: String,
    pub description: String,
    pub synced: bool,
    /// Catalog row count when synced (from the cached catalog).
    pub stations: Option<u64>,
}

/// One `nearest` result row.
#[derive(Debug, Clone, Serialize)]
pub struct NearestRow {
    pub collection: String,
    /// The catalog `par` value — the station id.
    pub id: String,
    pub desc: String,
    pub latitude: f64,
    pub longitude: f64,
    pub years: f64,
    pub distance_km: f64,
    /// Absolute cache path; feeds a runspec `station.par`.
    pub path: PathBuf,
}

/// A `nearest` query.
#[derive(Debug, Clone)]
pub struct NearestQuery {
    pub latitude: f64,
    pub longitude: f64,
    /// Result count (CLI default 5).
    pub count: usize,
    /// Restrict to one collection; `None` searches all synced.
    pub collection: Option<String>,
    /// Filter on the catalog `years` column (the GHCN
    /// record-length-tier successor).
    pub min_years: Option<f64>,
}

/// Enumerate every manifest collection with its sync state.
///
/// # Errors
///
/// Propagates catalog read failures for synced collections.
pub fn list(manifests: &Manifests, cache_root: &Path) -> Result<Vec<ListRow>, StationsError> {
    manifests
        .collections
        .iter()
        .map(|collection| {
            let synced = collection.is_synced(cache_root);
            let stations = if synced {
                Some(catalog_row_count(collection, cache_root)?)
            } else {
                None
            };
            Ok(ListRow {
                name: collection.name.clone(),
                version: collection.version.clone(),
                description: collection.description.clone(),
                synced,
                stations,
            })
        })
        .collect()
}

/// The `climNearest` successor: haversine over the shipped catalogs,
/// ascending distance, ties by collection name then id (byte-wise).
///
/// # Errors
///
/// Fails closed on an unknown or unsynced named collection, no synced
/// collections at all, a non-finite or out-of-range query point, or
/// an unresolvable catalog row among the results.
pub fn nearest(
    manifests: &Manifests,
    cache_root: &Path,
    query: &NearestQuery,
) -> Result<Vec<NearestRow>, StationsError> {
    validate_query_point(query)?;
    let targets: Vec<&Collection> = match &query.collection {
        Some(name) => {
            let collection = manifests.get(name)?;
            if !collection.is_synced(cache_root) {
                return Err(StationsError::NotSynced { name: name.clone() });
            }
            vec![collection]
        }
        None => {
            let synced: Vec<&Collection> = manifests
                .collections
                .iter()
                .filter(|collection| collection.is_synced(cache_root))
                .collect();
            if synced.is_empty() {
                return Err(StationsError::Query {
                    message: "no synced collections; run `cligen stations sync`".to_owned(),
                });
            }
            synced
        }
    };

    let mut rows = Vec::new();
    for collection in targets {
        collect_collection_rows(collection, cache_root, query, &mut rows)?;
    }
    rows.sort_by(|a, b| {
        a.distance_km
            .total_cmp(&b.distance_km)
            .then_with(|| a.collection.cmp(&b.collection))
            .then_with(|| a.id.cmp(&b.id))
    });
    rows.truncate(query.count);
    Ok(rows)
}

fn validate_query_point(query: &NearestQuery) -> Result<(), StationsError> {
    let lat_ok = query.latitude.is_finite() && (-90.0..=90.0).contains(&query.latitude);
    let lon_ok = query.longitude.is_finite() && (-360.0..=360.0).contains(&query.longitude);
    if !lat_ok || !lon_ok {
        return Err(StationsError::Query {
            message: "latitude must be finite in [-90, 90] and longitude finite in [-360, 360]"
                .to_owned(),
        });
    }
    Ok(())
}

fn collect_collection_rows(
    collection: &Collection,
    cache_root: &Path,
    query: &NearestQuery,
    rows: &mut Vec<NearestRow>,
) -> Result<(), StationsError> {
    let payload_dir = collection.cache_dir(cache_root);
    let connection = open_catalog(collection, cache_root)?;
    let mut statement = connection
        .prepare("SELECT par, desc, latitude, longitude, years FROM stations")
        .map_err(|error| catalog_error(collection, error))?;
    let mapped = statement
        .query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, f64>(2)?,
                row.get::<_, f64>(3)?,
                row.get::<_, f64>(4)?,
            ))
        })
        .map_err(|error| catalog_error(collection, error))?;
    for station in mapped {
        let (par, desc, latitude, longitude, years) =
            station.map_err(|error| catalog_error(collection, error))?;
        if query.min_years.is_some_and(|min| years < min) {
            continue;
        }
        let path =
            resolve_par(&payload_dir, &par).ok_or_else(|| StationsError::UnresolvedCatalogRow {
                name: collection.name.clone(),
                par: par.clone(),
            })?;
        rows.push(NearestRow {
            collection: collection.name.clone(),
            id: par,
            desc: desc.trim().to_owned(),
            latitude,
            longitude,
            years,
            distance_km: haversine_km(query.latitude, query.longitude, latitude, longitude),
            path,
        });
    }
    Ok(())
}

fn open_catalog(
    collection: &Collection,
    cache_root: &Path,
) -> Result<rusqlite::Connection, StationsError> {
    let path = collection.cache_dir(cache_root).join(&collection.catalog);
    rusqlite::Connection::open_with_flags(&path, rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY)
        .map_err(|error| catalog_error(collection, error))
}

fn catalog_row_count(collection: &Collection, cache_root: &Path) -> Result<u64, StationsError> {
    open_catalog(collection, cache_root)?
        .query_row("SELECT count(*) FROM stations", [], |row| row.get(0))
        .map_err(|error| catalog_error(collection, error))
}

fn catalog_error(collection: &Collection, error: rusqlite::Error) -> StationsError {
    StationsError::Catalog {
        name: collection.name.clone(),
        message: error.to_string(),
    }
}

/// Great-circle haversine distance, f64, sphere radius
/// [`EARTH_RADIUS_KM`].
#[must_use]
pub fn haversine_km(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let phi1 = lat1.to_radians();
    let phi2 = lat2.to_radians();
    let dphi = (lat2 - lat1).to_radians();
    let dlambda = (lon2 - lon1).to_radians();
    let a = (dphi / 2.0).sin().powi(2) + phi1.cos() * phi2.cos() * (dlambda / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());
    EARTH_RADIUS_KM * c
}

#[cfg(test)]
mod tests {
    use super::haversine_km;

    #[test]
    fn haversine_matches_reference_distances() {
        // Moscow ID -> Pullman WA (46.7324,-117.0002 vs
        // 46.7313,-117.1796): Δlon 0.1794° × 76.3 km/° at 46.73°N
        // ≈ 13.7 km, hand-derived.
        let d = haversine_km(46.7324, -117.0002, 46.7313, -117.1796);
        assert!((d - 13.68).abs() < 0.2, "{d}");
        assert_eq!(haversine_km(10.0, 20.0, 10.0, 20.0), 0.0);
        // Antipodal-ish sanity: half circumference ~ 20015 km.
        let half = haversine_km(0.0, 0.0, 0.0, 180.0);
        assert!((half - 20015.0).abs() < 5.0, "{half}");
    }
}
