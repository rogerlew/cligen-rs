# A10 retained-adapter temporal generalization

Status: research-only, revision 1 (A10M5R11)

## Surface

This specification governs the development-only temporal evaluation of the
three configurations retained by A10M5R10:

- `annual_monthly_residual_adapter-k1`;
- `monthly_residual_adapter-k2`; and
- `annual_monthly_residual_adapter-k2`.

It does not define a public model, generation profile, station format, or
confirmation claim.

## Authority basis

Training, controls, seeds, calendar treatment, and residual architectures are
inherited byte-for-byte from A10M5R10R1R4. Temporal generation, metrics,
component scales, comparators, uncertainty, and eligibility are inherited
from the ratified A10M5R4R2 protocol, including the A10M5R4R2R1R2
leap-century correction.

## Producers and consumers

Each typed L40 role trains all three frozen seeds and writes one
`streams.json` containing 100 Gregorian years beginning in 2001 for every
combination of six frozen fit-validation sites and eight members. The local
selector consumes these streams, the hash-pinned Daymet shards, and freshly
generated faithful and stochastic-PRISM comparator streams.

## Semantics

The estimand is stochastic climate, not paired day-to-day reconstruction.
The registered error signal includes monthly and annual precipitation,
Tmax, and Tmin means and dispersions, distributional summaries,
cross-variable dependence, annual persistence, and wet/dry occurrence and
spell behavior. Paired daily-pattern weight remains zero.

Daymet rows are used exactly as observed. No leap-day or year-end value is
filled. Bootstrap year blocks are relabelled to
`2000 + 16 * position + (0 if source block contains February 29 else 1)`,
which preserves block length and leap status without invalid replacement
dates or century collisions.

For each candidate and regime, the reference is the smaller composite error
of faithful CLIGEN and `stochastic_prism_localized_par_v1`. A candidate is
temporally eligible only when both inherited gates pass:

- the 90th percentile of the 1,000-replicate bootstrap distribution of its
  median regime ratio is at most 1.25; and
- its point-estimate maximum regime ratio is at most 1.50.

Every eligible candidate continues. The package may report paired candidate
contrasts, but introduces no new selector or parsimony tie-break.

## Failure and provenance

Malformed identities, incomplete stream matrices, non-finite metrics,
support failures, calendar drift, role opening, or comparator failure close
the package without inference. Stream records bind candidate, capacity,
training seed, point, regime, member, row count, metric payload, and stream
SHA-256. Development-selection and confirmation roles remain sealed.

## Solar boundary

Solar radiation is explicitly deferred. A later package should use a
partially procedural architecture: a deterministic astronomical envelope
from latitude and day of year, with learned stochastic clearness/cloud
residuals coupled to generated precipitation and temperature. It must not use
observed daily weather as a generation input. This direction is a downstream
design constraint, not evidence or a gate in A10M5R11.
