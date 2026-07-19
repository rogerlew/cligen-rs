# A10M5R4R1 prospective design freeze

The package freezes `stochastic_prism_localized_par_v1` as a preprocessing
mode followed by unchanged `faithful_5_32_3`, not as an independent daily
sampler. Its required request is longitude, latitude, and years. Begin year 1,
burn 0, no interpolation, `us-2015` version 2026.07, and Norm91m 1991--2020
CONUS 4 km are revision-1 constants.

The PRISM source is a hash-pinned external bundle of the 36 official monthly
ppt M4 and Tmax/Tmin M5 archives. Generation queries the local verified
rasters only. The extraction receipt binds the registered bundle and
manifest, every source archive/raster hash, PRISM release metadata, access
date, cell coordinates, raw values, unit conversions, and required
attribution.

Station selection keeps the nearest ten `us-2015` candidates, then rank-sums
distance (1), latitude difference (1), precipitation-normal error (3), Tmax-
normal error (1.5), and Tmin-normal error (1.5). Component ties and the final
tie break by station ID. This intentionally follows the user's supplied axes;
it is not mislabeled as byte-for-byte current `wepppy` US behavior, which
adds elevation and omits temperature normals.

Localization follows the registered `wepppy` algebra: PRISM-to-station
monthly precipitation ratio moves station wet-day count halfway toward the
ratio within 50--200% and calendar bounds; P(wet|wet) and P(wet|dry) are
recomputed while preserving their ratio; wet-day mean is set from PRISM total
and the new wet-day count; Tmax/Tmin means are replaced; and raw `MX .5 P` is
scaled by the monthly-total ratio within 0.5--2.0. The 0.05-inch dry threshold
is retained. Only `.par` records 4, 7, 8, 9, 10, and 15 may change.

Fixed-width quantization is observable evidence, not hidden preprocessing.
The mode records requested and reparsed values, refuses an unrepresentable
positive target, proves all untouched records and tail byte-identical, and
uses the localized bytes as the faithful runspec input.

No neural output or protected role is accessible during implementation or
generic acceptance. Successful generic acceptance is only a prerequisite for
a fresh A10 temporal-adjudication package; it makes no comparative claim.
