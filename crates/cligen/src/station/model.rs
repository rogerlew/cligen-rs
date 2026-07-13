//! Typed state for station model `fixed_monthly_5_32_3`.
//!
//! This type deliberately has no serialization derives. File-schema DTOs
//! adapt to it explicitly so a station-document revision cannot silently
//! change the faithful generator's precision, array orientation, or units.

/// The complete raw typed station state read from a CLIGEN 5.32.3 `.par`
/// file before `sta_parms` applies its load-time derivations.
///
/// # Units
/// Values retain the source file's units: precipitation depth in inches,
/// `wi_raw` intensity in inches/hour, temperature in degrees Fahrenheit,
/// solar radiation in Langleys/day, elevation in feet, and wind speed in
/// metres/second. Probabilities and time-to-peak values are fractions; wind
/// direction occurrence and calm values are percentages.
///
/// # Numerics
/// Every source `REAL*4` field remains `f32`; every source integer remains
/// `i32`. The nested arrays preserve the Fortran read orientation documented
/// by SPEC-PAR.
#[derive(Debug, Clone)]
pub struct FixedMonthly5323 {
    pub stidd: String,
    pub nst: i32,
    pub nstat: i32,
    pub igcode: i32,
    pub ylt: f32,
    pub yll: f32,
    pub years: i32,
    pub itype: i32,
    pub elev_ft: i32,
    pub tp6: f32,
    pub rst: [[f32; 3]; 12],
    pub prw: [[f32; 2]; 12],
    pub obmx: [f32; 12],
    pub obmn: [f32; 12],
    pub stdtx: [f32; 12],
    pub stdtm: [f32; 12],
    pub obsl: [f32; 12],
    pub stdsl: [f32; 12],
    pub wi_raw: [f32; 12],
    pub rh: [f32; 12],
    pub timpkd: [f32; 12],
    pub wvl: [[[f32; 12]; 4]; 16],
    pub calm: [f32; 12],
    pub site: [String; 3],
    pub wgt: [f32; 3],
}
