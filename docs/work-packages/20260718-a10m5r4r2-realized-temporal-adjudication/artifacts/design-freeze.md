# A10M5R4R2 prospective temporal freeze

This record was completed before PRISM values, faithful/PRISM generated
streams, or P1/P2 generated outputs were accessed. The six observation sites
are the minimum prepublished A10M1 ordering key within each `fit_validation`
regime. Selection used `daymet-selected-v2.json`, which contains coordinates,
roles, regimes, tiles, and ordering keys but no climate values.

The exact sites, 1980--2009 observation window, six accepted neural export
hashes, three training seeds, eight independent members, 100-year Gregorian
horizon, stochastic burn counts, metrics, component scales, bootstrap seed,
noninferiority limits, larger-capacity preference rule, resource ceiling, and
role firewall are machine-frozen in `temporal-contract.json` and `sites.json`.
The successful A10M5R3 exports were cleaned after evidence collection, so each
model is reconstructed once under its accepted seed and canonical Lemhi
environment. Its TorchScript bytes must reproduce the accepted SHA-256 before
stream generation; mismatch stops that role and prohibits scoring it.

Observations, faithful CLIGEN, and `stochastic_prism_localized_par_v1` remain
distinct arms. PRISM supplies only monthly normals used to localize a CLIGEN
station. It is not a daily observation source. Daymet's eight explicitly
masked leap-year December 31 rows remain missing and are never filled.

The accepted neural stream has daily precipitation and temperature but no
storm duration, time-to-peak, peak-ratio, or half-hour-intensity output.
Faithful and PRISM arms therefore report the registered peak-rate diagnostic;
it is not fabricated for neural arms and does not enter capacity scoring.
This explicit partial-domain report is preferable to silently deriving a
subdaily field the accepted model does not generate.

At least one capacity must reproduce every accepted export, retain physical
support, and pass both the median and worst-regime temporal noninferiority
guards to authorize A10M5R5. Every temporally eligible capacity continues to
the frozen A10M5R6 spatial comparison. A10M5R4R2 may record a temporal
preference for P2 only under the prospective 10%/0.90 rule; it cannot make the
final architecture or public-profile decision.

Development-selection and confirmation remain sealed. Six sequential,
single-attempt, one-L40 jobs of at most 30 minutes are authorized, plus the
canonical five-minute exact-node recovery reserve. All raw streams are
summarized inside their producing job, hash-receipted, and deleted through
toolkit-owned job-local cleanup.
