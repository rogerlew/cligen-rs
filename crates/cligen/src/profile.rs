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
    /// Stable profile identifier carried by the fast-profile CLI header.
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
