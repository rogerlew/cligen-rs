//! Origin-Class: CLIGEN-5.32.3-Public-Domain
//! Migration-Method: source-authority-port (ADR-0001)
//! Replaces: reference/cligen532/crandom3.inc (common /random/) +
//!   block-data initializers reference/cligen532/cligen.f:1068-1078
//! Precision-Map: REAL*4 except `g_dsum`/`g_ssum` (double precision,
//!   crandom3.inc:15-16)
//! Faithful-Acceptance: exercised through the dstg replay
//!   (fixtures/taps/*/dg.tap) and Stage C ranset identity
//!
//! # Symbol glossary
//! | Symbol | Fortran | Meaning | Units |
//! |---|---|---|---|
//! | `ranary` | `ranary(31,9)` | batch of 31 random values per parameter | — |
//! | `mox` | `mox` | month `ranary` was last loaded (1..12; 0 = never) | month |
//! | `dax` | `dax` | current day cursor | day |
//! | `chicnt` | `chicnt(10,12,20)` | QC bin counts per parameter/month | count |
//! | `g_dsum` | `g_dsum(9,12)` | running sum of std-normal deviates | — |
//! | `g_ssum` | `g_ssum(9,12)` | running sum of squared deviates | — |
//! | `sumchi` | `sumchi` | running chi-square V-statistic | — |
//! | `chi_n` | `chi_n` | observation count from the last QC test | count |
//! | `thresh` | `thresh(9)` | mean-threshold for month regeneration | — |
//! | `thres2` | `thres2(9)` | variance-threshold for month regeneration | — |
//! | `vv`,`fx`,`z` | `vv,fx,z` | drawn precip-prob / wind-dir / time-to-peak | — |

/// `nrparm` — number of parameters random numbers are generated for.
pub const NRPARM: usize = 9;
/// `nrelem` — random numbers generated together per parameter.
pub const NRELEM: usize = 31;

/// The `/random/` common block (`crandom3.inc`), one owning struct per
/// coding standard §5.
///
/// Indexing note: Fortran `ranary(elem, param)` and
/// `chicnt(param, month, bin)` are 1-based; the Rust arrays are indexed
/// `[param-1][elem-1]` / `[param-1][month-1][bin-1]`. The nine
/// EQUIVALENCE column views (`crandom3.inc:46-62`) are the accessor
/// methods below — single storage, no duplicated fields.
#[derive(Debug, Clone)]
pub struct Crandom3State {
    pub g_dsum: [[f64; 12]; NRPARM],
    pub g_ssum: [[f64; 12]; NRPARM],
    pub sumchi: f32,
    /// `ranary(nrelem, nrparm)` stored `[param][elem]`.
    pub ranary: [[f32; NRELEM]; NRPARM],
    pub g_dimi: [i32; 12],
    pub g_dimp: [i32; 12],
    pub chi_n: i32,
    pub mox: i32,
    pub dax: i32,
    /// `chicnt(nrparm+1, 12, 20)` stored `[param][month][bin]`; row
    /// `NRPARM` (Fortran parameter 10) is `dstg`'s private QC channel.
    pub chicnt: [[[i32; 20]; 12]; NRPARM + 1],
    pub thresh: [f32; NRPARM],
    pub thres2: [f32; NRPARM],
    pub vv: f32,
    pub fx: f32,
    pub z: f32,
    pub idum1: i32,
    pub idum2: i32,
}

impl Default for Crandom3State {
    /// Block-data initializers (`cligen.f:1068-1078`): `mox=0`, `dax=0`,
    /// zeroed `ranary`/`g_dimi`/`g_dimp`/`g_dsum`/`g_ssum`/`chicnt`,
    /// `thresh`/`thres2` all 50.0. Members without DATA statements
    /// (`sumchi`, `chi_n`, `vv`, `fx`, `z`, `idum1`, `idum2`) are
    /// zero-initialized, matching Fortran static (BSS) storage.
    fn default() -> Self {
        Crandom3State {
            g_dsum: [[0.0; 12]; NRPARM],
            g_ssum: [[0.0; 12]; NRPARM],
            sumchi: 0.0,
            ranary: [[0.0; NRELEM]; NRPARM],
            g_dimi: [0; 12],
            g_dimp: [0; 12],
            chi_n: 0,
            mox: 0,
            dax: 0,
            chicnt: [[[0; 20]; 12]; NRPARM + 1],
            thresh: [50.0; NRPARM],
            thres2: [50.0; NRPARM],
            vv: 0.0,
            fx: 0.0,
            z: 0.0,
            idum1: 0,
            idum2: 0,
        }
    }
}

macro_rules! ranary_view {
    ($name:ident, $col:expr, $doc:expr) => {
        #[doc = $doc]
        /// (1-based `elem`, mirroring the source.)
        pub fn $name(&self, elem: usize) -> f32 {
            self.ranary[$col - 1][elem - 1]
        }
    };
}

impl Crandom3State {
    ranary_view!(
        vvx,
        1,
        "`vvx` — probability of precip today (`ranary(:,1)`)."
    );
    ranary_view!(v2x, 2, "`v2x` — max temperature (`ranary(:,2)`).");
    ranary_view!(v4x, 3, "`v4x` — min temperature (`ranary(:,3)`).");
    ranary_view!(v6x, 4, "`v6x` — radiation (`ranary(:,4)`).");
    ranary_view!(v8x, 5, "`v8x` — precip amount (`ranary(:,5)`).");
    ranary_view!(fxx, 6, "`fxx` — wind direction (`ranary(:,6)`).");
    ranary_view!(v10x, 7, "`v10x` — wind velocity (`ranary(:,7)`).");
    ranary_view!(v12x, 8, "`v12x` — dew-point temperature (`ranary(:,8)`).");
    ranary_view!(zx, 9, "`zx` — time to peak (`ranary(:,9)`).");
}
