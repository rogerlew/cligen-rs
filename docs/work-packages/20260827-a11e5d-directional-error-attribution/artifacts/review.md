# A11E5D review

Date: 2026-08-27

## Prospective source review

Disposition: `GO`

The package does not modify or re-adjudicate A11E5. It restores the signs and
raw variance/correlation quantities discarded by the absolute-error evaluator,
requires exact closed metric and stream-hash replay, and separates signed bias
from absolute scatter. Five-percent labels are descriptive and match A11E5's
materiality convention. Confirmation and hybrid design remain excluded. No
P0/P1 finding remains before publication.

## Evidence review

Disposition: `GO — DIRECTIONAL_ERROR_ATTRIBUTED reproduced`

Published source, exact A11E5 closure artifacts, calendars, roles, selector,
fit, 160 paired rows, and 320 streams authenticated. Every regenerated arm
matched its closed metric object and stream hash; directional evidence was
finite, invariants were zero, confirmation remained false, and all scientific
outputs replayed byte-identically.

The signed arithmetic reproduces the primary finding. Circular block annual
temperature variance is systematically low relative to observation
(geometric ratio 0.802; 100 under, 50 over, 10 within 5%) and relative to
Gaussian (ratio 0.878; 88 lower, 61 higher, 11 within 5%). Monthly temperature
variance is essentially arm-neutral (ratio 0.991), so the annual result cannot
be attributed to a blanket monthly-variance deficit.

Precipitation direction is the opposite: Gaussian is extremely overdispersed
and circular block sharply reduces but does not eliminate the excess. Signed
annual lag-one residuals show no comparable precipitation bias; circular block
also reduces temperature lag-one and low-frequency underrepresentation.

The evidence supports covariance decomposition as the smallest next
diagnostic. It does not yet prove a causal covariance component or authorize a
hybrid. No P0/P1 finding remains.
