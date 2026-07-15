//! Declared generation behavior profiles.
//!
//! Faithful behavior remains defined by the vendored CLIGEN source. Profiles
//! in this module are explicit extension boundaries under ADR-0001; a host
//! feature or environment variable must never select one implicitly.

use serde::Deserialize;

/// The algorithm family used to generate a run's stochastic inputs.
#[derive(Debug, Clone, Copy, Default, Deserialize, PartialEq, Eq)]
pub enum GenerationProfile {
    /// The source-authority REAL*4/REAL*8 port of CLIGEN 5.32.3.
    #[default]
    #[serde(rename = "faithful_5_32_3")]
    Faithful5323,
    /// Experimental four-lane monthly batch producer with no `ranset` QC.
    #[serde(rename = "fast_batch_v0")]
    FastBatchV0,
}

impl GenerationProfile {
    /// Canonical schema/provenance identifier. This follows the closed
    /// SPEC-RUNSPEC enum spelling; legacy command markers are a separate
    /// presentation surface.
    pub fn id(self) -> &'static str {
        match self {
            Self::Faithful5323 => "faithful_5_32_3",
            Self::FastBatchV0 => "fast_batch_v0",
        }
    }

    /// Legacy display spelling carried by the non-faithful CLI command echo.
    /// Structured provenance uses [`Self::id`].
    pub fn provenance_name(self) -> &'static str {
        match self {
            Self::Faithful5323 => "faithful-5.32.3",
            Self::FastBatchV0 => "fast-batch-v0",
        }
    }

    /// Preserve faithful header bytes; append a mandatory marker for an
    /// extension output so it cannot be mistaken for a faithful trajectory.
    pub fn command_echo(self, echo: String) -> String {
        match self {
            Self::Faithful5323 => echo,
            Self::FastBatchV0 if echo.is_empty() => {
                format!("--generation-profile {}", self.provenance_name())
            }
            Self::FastBatchV0 => {
                format!("{echo} --generation-profile {}", self.provenance_name())
            }
        }
    }
}

/// The QC conditioning policy knob (SPEC-GENERATION-PROFILES §qc_filter,
/// ADR-0002 ruling 3; accepted by the runspec as of the Q3 package).
///
/// `Faithful` applies the source acceptance/retry protocol
/// (`cligen.f:4002-4340`); on the faithful backend it preserves golden
/// byte identity. `Off` accepts every produced batch: `RANDN`, the
/// per-parameter streams, the column-5/9 zero masks, and the `ell`
/// chain stay source-shaped; only the accept/retry loop and its QC
/// accumulation are skipped.
#[derive(Debug, Clone, Copy, Default, Deserialize, PartialEq, Eq)]
pub enum QcFilter {
    #[default]
    #[serde(rename = "faithful")]
    Faithful,
    #[serde(rename = "off")]
    Off,
}

impl QcFilter {
    /// The provenance string (`identity.provenance.qc_filter` and
    /// `process.qc_filter`).
    pub fn provenance_name(self) -> &'static str {
        match self {
            Self::Faithful => "faithful",
            Self::Off => "off",
        }
    }

    /// Append the mandatory non-faithful header marker (`--qc-filter
    /// off`); faithful output keeps its legacy-compatible bytes.
    pub fn command_echo(self, echo: String) -> String {
        match self {
            Self::Faithful => echo,
            Self::Off if echo.is_empty() => "--qc-filter off".to_owned(),
            Self::Off => format!("{echo} --qc-filter off"),
        }
    }
}
