# SPEC-A8C-ROUTED-DAILY — Explicit Routed Daily Precipitation v1

Status: retired historical specification; runtime retired by A8c1 (revision 1)
Surface: former station-document revision 2, generation profile
`a8c_routed_daily_v1`, and daily precipitation runtime seam.

This document preserves the exact contract used by the accepted A8c pilot. It
is not a current interface specification: A8c1 removed every producer,
consumer, accepted schema branch, and runtime implementation from `main` after
confirming that none had shipped. The implementation remains reproducible from
Git commit `fdd35f60241f25663614db46142bfe3683c6ce5f` and the retained A8c
evidence; new work must define a new contract rather than reuse these IDs.

## Producers and consumers

For the historical A8c implementation, the station builder produced revision-2
station documents. The runspec resolver validated them and the generator
consumed their declared route. Text, Parquet, quality, and provenance consumers
received the selected station-model and generation-profile identities. This
was an extension under ADR-0001; it was not part of faithful CLIGEN 5.32.3.

## Compatibility axes

The following identities remain independent:

| Axis | A8c value |
|---|---|
| station document schema | `org.openwepp.cligen.station` / `2` |
| station model | `a8c_integrated_daily_v1` or `fixed_monthly_5_32_3` |
| daily route | `integrated_daily` or `legacy_daily_fallback` |
| generation profile | `a8c_routed_daily_v1` |
| output schemas | unchanged |

Revision-1 station documents and legacy `.par` inputs remain valid for existing
profiles. They are invalid with `a8c_routed_daily_v1` because neither carries
the required route. Revision-2 documents are accepted only by the A8c profile
during this pilot. No file extension, coordinate, parameter value, or generated
output may infer a route.

## Revision-2 station document

The envelope retains revision 1's `units`, `lineage`, and fixed-monthly
`parameters` objects byte-for-field. It adds:

```json
{
  "station_schema_version": 2,
  "station_model": "a8c_integrated_daily_v1",
  "daily_precipitation": {
    "route": "integrated_daily",
    "fit_id": "a8a_o2_logqspline_gaussian_copula_v1",
    "source_analysis_sha256": "<64 lowercase hex>",
    "seasons": ["<four fixed season coefficient objects>"],
    "months": ["<twelve fixed month coefficient objects>"]
  }
}
```

An integrated season object contains `season` (`DJF`, `MAM`, `JJA`, or `SON`),
eleven positive finite `log_quantile_knots_mm` in fixed probabilities
`[0,.01,.05,.10,.25,.50,.75,.90,.95,.99,1]`, and finite
`gaussian_copula_rho` in `[-0.95,0.95]`. Each season appears once in calendar
order `DJF,MAM,JJA,SON`. An integrated month object contains 1-based `month`,
four finite occurrence probabilities in `(0,1)` ordered `DD,DW,WD,WW`, and a
finite positive `amount_dispersion` no larger than the explicitly retained
positive `legacy_amount_dispersion` from the parent analytic cell.

The fallback form requires:

```json
{
  "station_schema_version": 2,
  "station_model": "fixed_monthly_5_32_3",
  "daily_precipitation": {
    "route": "legacy_daily_fallback",
    "fit_id": "legacy_daily_only_v1",
    "source_analysis_sha256": "<A8b decision SHA-256>",
    "seasons": [],
    "months": []
  }
}
```

Missing or unknown fields, wrong array lengths/order, non-finite values,
foreign hashes/fit identifiers, duplicate months/seasons, a model/route
mismatch, fallback coefficients, or absent integrated coefficients fail closed.
The syntax-independent parameter-set hash covers both the fixed-monthly base
and the daily extension for revision 2; revision-1 hashes remain unchanged.

## Profile pairing and supported modes

`a8c_routed_daily_v1` is explicit and non-default. It requires continuous
mode, interpolation `none`, `qc_filter: faithful`, and a revision-2 station
document. Observed and deprecated storm modes fail closed. Existing profiles
reject revision-2 documents during the pilot so behavior cannot change merely
by swapping station syntax.

The legacy text command echo appends
`--generation-profile a8c-routed-daily-v1`. Structured provenance uses
`a8c_routed_daily_v1`, the declared station model, revision-2 input schema, and
RNG identity `cligen_randn_5_32_3_plus_splitmix64_daily_v1`.

## Integrated daily algorithm

The profile leaves faithful monthly parameter loading, QC-conditioned random
batches, temperature, radiation, wind, duration, intensity, and output
formatting in place. Only generated precipitation occurrence and wet amount are
replaced after the faithful batch refill at the existing daily seam.

State starts at occurrence history `DD` and no amount latent. It persists
across month and year boundaries. For each calendar day, before testing wetness:

1. consume one open-interval f64 uniform from the occurrence stream;
2. consume one open-interval f64 uniform from the amount stream and transform
   it through the pinned inverse-normal approximation;
3. select the current month's `DD,DW,WD,WW` probability from the preceding two
   wet/dry bits and compare the occurrence uniform;
4. on dry, emit zero precipitation and clear the amount latent;
5. on wet after dry, use the day's normal as the latent; on wet after wet, use
   `rho*z_previous + sqrt(1-rho^2)*epsilon`;
6. map the normal CDF through the season's piecewise-linear log-quantile and
   current month's dispersion, divide by its exact piecewise exponential
   integral, multiply by the fixed-monthly wet-day mean, and round once to f32
   inches; and
7. shift the occurrence history and retain the wet latent.

The route does not condition on month totals, generated counts, or downstream
values. There is no rejection, clipping, retry, or output repair. Input bounds
make every produced wet amount finite and positive.

## RNG ownership

Two SplitMix64 streams are domain-separated from the faithful post-burn,
post-warm seed surface. Derivation does not advance any faithful stream. Each
stream advances exactly once per generated calendar day, including dry days.
The occurrence result never controls draw count. Fallback creates no extension
state and consumes no extension draw. Burn therefore changes both the faithful
and extension trajectories without interpreting the burn as a user seed.

## Fallback semantics

`legacy_daily_fallback` delegates to the existing faithful `gen_precip`
function and carries no secondary state or RNG. For equal base parameters,
burn, years, and interpolation, its typed climate rows are identical to the
`faithful_5_32_3` control. Only required profile and station/provenance
declarations differ in serialized artifacts.

## Failure and promotion boundary

Malformed documents and invalid profile pairings fail before generation. A8c
is a pilot profile and never becomes the default through this specification.
Pilot success may only recommend a separately scoped confirmation package; it
does not authorize full-corpus or WEPP claims.

The executed A8c pilot returned `STOP-A8-ROUTED-DAILY`. This specification is
retained only to define the historical experimental surface and reproduce its
evidence. The profile is no longer accepted or implemented on current `main`,
no A8d confirmation is authorized, and faithful mode remains the default.
