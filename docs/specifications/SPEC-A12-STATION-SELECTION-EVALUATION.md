# SPEC-A12-STATION-SELECTION-EVALUATION — Automatic Donor Evaluation

Status: research-only revision 1; no runtime-default or confirmation authority

## Purpose and claim boundary

A12 evaluates whether the current `stochastic_prism_localized_par_v1` donor
selector is more appropriate than geographic closest selection. It also
evaluates one WEPPpy-style elevation/PRISM reference. This is an exploratory
validation decision, not a port, promotion, or claim that any selector is
universally optimal.

## Corpus and roles

The evaluation roster is exactly the 240 `fit_validation` locations in the
A10M5R15R1 cohort: 40 in each of six registered regimes. Values cover
1980-01-01 through 2009-12-31 under `daymet_official_365_v1`. Only the explicit
observed mask is eligible. `candidate_fit` objects may authenticate the corpus
but are not scored; development and confirmation objects are not opened.

Every object must have 10,958 normalized dates, 10,950 observed dates, and
masked dates `1980-12-31`, `1984-12-31`, `1988-12-31`, `1992-12-31`,
`1996-12-31`, `2000-12-31`, `2004-12-31`, and `2008-12-31`. The full roster,
object/shard hashes, source transform, role, bounds, counts, and masks are
recorded before scoring.

## Frozen policies

All policies use the nearest ten `us-2015@2026.07` stations ordered by
SPEC-STATION-DB distance and station ID.

- `closest_v1`: select the first row.
- `cligen_prism_rank_sum_v1`: the current SPEC-A10 selector—zero-based ranks
  for distance, absolute latitude difference, Euclidean PRISM precipitation,
  Tmax, and Tmin monthly-normal errors; score
  `distance + latitude + 3*ppt + 1.5*tmax + 1.5*tmin`.
- `wepppy_elevation_prism_reference_v1`: zero-based ranks for distance,
  absolute latitude difference, absolute station/target elevation difference,
  and Euclidean PRISM precipitation-normal error; score
  `distance + latitude + elevation + 3*ppt`.

Every component tie breaks by station ID and final selection minimizes score,
then distance, then station ID. The reference uses the authenticated Daymet
object elevation in metres for the target. The `us-2015` SQLite catalog donor
elevation is explicitly interpreted as feet and converted by exact factor
`0.3048` to metres. This corrects the reviewed WEPPpy path's implicit unit
mismatch. The prior-art identity is WEPPpy commit
`3ee74d02df445a30968ef92975e5e3e2f6084669`, file
`wepppy/climates/cligen/cligen.py` SHA-256
`4071cc72165d174851316349c0d96a3f4fa06fcf0b2d91e5b67de439f39a42c1`.
The reference does not call WEPPpy, an elevation service, or the network and
makes no exact-identity claim about a WEPPpy runtime.

At every scored site, the exact source-bound release executable performs a
one-year `prism run`. Its station receipt is the authority for the current
policy's pool, ranks, component values, winner, and fully encoded localized
file; the independent evaluator must agree or fail closed. Closest and the
elevation reference use the same authenticated ten-row pool and the full
production six-row localization/render/reparse constraints.

## Observed descriptors and errors

A wet day has finite observed precipitation strictly greater than zero. For
each site/month, compute empirical wet-after-wet and wet-after-dry
probabilities, positive precipitation sample SD and adjusted sample skew, and
Tmax/Tmin sample SD. Months require at least three positive-precipitation
values and both a wet and dry predecessor transition; otherwise evaluation
fails closed.

For a donor `.par`, compare wet-day precipitation SD and skew and Tmax/Tmin SD
from the unchanged source rows. Compare `P(W/W)` and `P(W/D)` only after the
exact production localization algebra, F6.2 rendering, and f32 reparse because
the PRISM path rewrites those rows. An unlocalizable selected donor fails the
evaluation closed. Probability errors are absolute differences. SD errors are
absolute relative errors with denominator `max(observed, 1e-6)`. Skew error is
absolute difference divided by `max(1, abs(observed))`. Each family error is
the median of its 12 monthly errors; the site composite is the arithmetic mean
of the six family errors.

PRISM-localized monthly means are excluded from the primary score because the
localizer replaces them after selection. Daymet cannot adjudicate donor wind,
radiation, dew-point, time-to-peak, or subdaily-intensity structure; these are
explicit limitations.

## Frozen inference and decision

For each heuristic, define the paired site delta as heuristic composite minus
closest composite. Report its median, strict site-win fraction, six paired
family median deltas, and a 10,000-replicate percentile bootstrap 95% interval
for the median using common site resamples, NumPy Philox, a SeedSequence made
from integer seed 12012 plus the little-endian u32 words of the SHA-256 of the
frozen domain string, and NumPy's `linear` quantile method.

A heuristic is supported only when:

1. its paired composite median is strictly negative;
2. the bootstrap upper endpoint is strictly below zero;
3. its strict site-win fraction is greater than 0.5; and
4. no family median error exceeds `1.05 ×` the closest family median (when the
   closest median is zero, the heuristic median must also be zero).

The disposition is:

- `CURRENT_HEURISTIC_APPROPRIATE` when the current heuristic is supported and
  its composite median is no higher than the supported reference, if any;
- `ELEVATION_REFERENCE_BETTER` when the reference is supported and the current
  heuristic is not, or the reference has the lower supported composite median;
- `CLOSEST_PREFERRED` when neither heuristic is supported.

Integrity failures produce HOLD, not a scientific disposition. No disposition
changes the CLI default, opens confirmation, or implements the eventual
user/closest/heuristic product surface.

## Cryptographic provenance

The A12 receipt binds its source commit and every source/evidence input. The
runtime station-selection receipt advances to schema version 2 and contains
the selection method ID, station collection name/version/archive SHA-256,
selected source path, selected station ID, selected source `.par` SHA-256, and
the exact executing cligen binary SHA-256. The artifact manifest independently
binds the same executable and all emitted artifacts; mismatches fail closed.
The evaluator copies the authenticated PRISM runtime and release binary into a
private isolated run root, re-verifies those copies before use, and rehashes
them after all 240 runs to close mutable-cache and executable TOCTOU gaps.

## Replay and review

Evidence and decision JSON must replay byte-identically from the same published
source, binary, and inputs. Independent review must reproduce identities,
selector choices, descriptors, statistics, and disposition with no unresolved
P0/P1.
