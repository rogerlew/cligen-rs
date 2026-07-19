# SPEC-A10-ARCHITECTURE-PORTFOLIO — Parallel Climate Architecture Comparison

Status: research-only

Revision: 1 (A10M5R10, 2026-07-19)

## Surface and authority

This specification defines the development-only A10M5R10 architecture
portfolio, its common stochastic climate objective, and its deterministic
multi-candidate retention decision. It introduces no public generation
profile, does not change faithful CLIGEN, and does not authorize protected
target access or production integration.

The producer is the A10M5R10 set of ten independent one-L40 family-capacity
roles. Consumers are its all-240 evaluator and portfolio selector. The exact
machine freeze is
`docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/portfolio-contract.json`.

## Controls, capacities, and seeds

Every comparison uses the accepted `lognormal_wet_v2` P1 or P2 checkpoint with
the matching seed as its proper-NLL control. K1 binds P1, hidden size 80 and
87,295 parameters; K2 binds P2, hidden size 144 and 276,927 parameters. The
registered seeds are `147031`, `271828`, and `314159`. A control-materialization
predecessor must authenticate all six accepted checkpoint identities before
any portfolio role starts.

Adapter candidates have total parameter ceilings of 110,000 at K1 and 330,000
at K2. The climate-normal replacement model must lie in the corresponding
total-capacity band. Parameter count is reported, never silently padded, and
is a deterministic Pareto tie-break.

## Architecture families

`monthly_residual_adapter` freezes the matched P1/P2 backbone and adds a
member-centered AR(1) state updated once per calendar month. The state may
perturb wet-occurrence logit, positive-precipitation log location, temperature
mean, and log diurnal range. It cannot mutate the backbone or consume observed
or generated weather feedback.

`annual_monthly_residual_adapter` uses separate member-centered annual and
monthly AR(1) states. The annual state conditions the monthly transition and
represents year-to-year departures; the monthly state represents seasonal
departures within that year. Its decoder surface is the same as the monthly
adapter.

`hierarchical_joint_factor_adapter` preserves the annual/monthly timing but
uses shared low-rank innovations and a common decoder for wet occurrence,
positive precipitation amount, temperature mean, and diurnal range. This is
the paired test of cross-variable factors against the otherwise matched
separate-state hierarchy.

`climate_normal_hierarchical_state_space` is a replacement rather than an
adapter. A candidate-fit-only six-regime by twelve-month table supplies
distribution-head normals; a shared site correction receives latitude,
longitude, and elevation; annual and monthly stochastic states generate
departures. It is trained end to end within the K1/K2 capacity envelope. No
fit-validation target contributes a normal, descriptor, or weight.

`physics_conditioned_hierarchical_adapter` uses the hierarchical joint-factor
timing and dimensions, adds a deterministic extraterrestrial-radiation
envelope calculated from latitude and day of year, and generates a stochastic
solar-clearness/radiation head coupled through shared latent factors. Its core
weather and solar outputs are joint generated outputs. Observed `srad`,
precipitation, temperature, or their fit-validation aggregates are never
inputs. Candidate-fit `srad` may appear only as a training target and
fit-validation `srad` only as a gradient-free checkpoint/final target.

At K1 the monthly, annual, and shared-factor dimensions are 6, 3, and 4 and
decoder width is 32. At K2 they are 12, 6, and 8 and decoder width is 64.
Unused states are absent rather than ignored parameters. Every stochastic
innovation is counter based and centered across the even member ensemble at
each registered time cell.

## Calendar, masks, and roles

All consumers follow `SPEC-A10-CORPUS` revision 2 and
`daymet_official_365_v1`. From 1980-01-01 through 2009-12-31 the normalized
Gregorian axis has 10,958 rows and the core observed mask has 10,950. February
29 is observed; December 31 is absent in the eight leap years 1980 through
2008. The exact 1980--1987 window uses an exclusive 1988-01-01 end and has
2,922 axis rows and 2,920 observed rows.

The core mask is `source_observed` plus non-null precipitation, Tmax, and Tmin.
The physics target mask additionally requires non-null `srad`; its expected
full/window counts are 10,950/2,920 and must be verified from every immutable
object before resource reservation. Every eligible year-month has at least 28
masked days. No missing row is imputed, relabeled, compressed, or treated as
an observed target.

Only `candidate_fit` may fit normalizers, climate normals, weights, or any
target-derived statistic. `fit_validation` supplies no gradient and no model
input. `development_selection`, `confirmation_metadata`,
`confirmation_locked`, and `source_sensitivity` are prohibited. Derived
outputs inherit their source role.

## Common objective and evaluation

The core climate objective is the equal-weight mean of:

1. monthly location;
2. monthly interannual dispersion;
3. within-month daily dispersion;
4. annual location;
5. annual interannual dispersion;
6. wet occurrence and positive amount; and
7. precipitation-temperature dependence.

Daily proper NLL has weight `0.2`, latent stability `0.005`, and residual
size/centering `0.01`. Paired daily target-pattern loss is zero. The physics
candidate adds a `0.25`-weight solar family comprising monthly/annual
location and dispersion, within-month dispersion, wet/dry contrast, and
precipitation/temperature association; this does not renormalize the seven
core blocks.

Training uses eight differentiable members. Checkpoint and final evaluation
use sixteen hard members, identical counter-based fields across arms, exact
eight-calendar-year windows, and mask-based statistics. Training lasts at
least 24 and at most 96 epochs with patience 16. Checkpointing uses the
lexicographically first four eligible fit-validation points in each regime,
with a `1e-6` earlier-epoch tie rule. Its scalar is family-balanced core
climate score plus `0.2` times daily proper NLL; the physics arm additionally
includes `0.25` times solar-family score. Training-only latent-stability and
residual-size/centering regularizers are excluded from validation checkpoint
selection. Final evaluation covers all 240 eligible fit-validation points.

## Portfolio decision

Each family-capacity configuration aggregates three seed-matched ratios
against its P1/P2 controls. Eligibility requires complete finite support and
role/calendar evidence, median climate ratio at most 1.00, median NLL ratio at
most 1.10, every median block ratio at most 1.10, worst-seed climate/NLL/block
ratios at most 1.10/1.15/1.20, and a median combined monthly/annual
interannual-dispersion ratio at most 0.90.

The physics candidate additionally requires at least 15% solar-family
improvement against the candidate-fit regime/month clearness-climatology
control, at least 10% improvement in wet/dry plus precipitation/temperature
dependence, and no solar block degradation above 10%.

Eligible configurations enter a six-axis Pareto comparison: climate, daily
NLL, combined monthly/annual dispersion, combined monthly/annual location,
combined wet/dependence, and within-month dispersion. Dominance requires no
worse value on every axis and at least a 2% improvement on one. Differences
below 2% are equivalent for deterministic ordering, which then uses fewer
parameters, lower training wall time, and configuration ID.

At most three configurations are retained by taking the lowest climate ratio,
then lowest combined-dispersion ratio among remaining nondominated rows, then
lowest NLL ratio among the remainder. Two or three retained rows produce
`A10M5R10-PORTFOLIO-READY`; one produces
`HOLD-A10M5R10-SINGLE-CANDIDATE`; none produces
`HOLD-A10M5R10-NO-CANDIDATE`.

## Provenance and failure behavior

Every result binds source commit, contract and calendar-profile hashes,
accepted control identity, family, capacity, seed, parameter count, optimizer
and checkpoint identity, member field, points, windows, roles, and job/receipt
identities. Unknown identity, incomplete seed matrix, missing final point,
target-derived input, gradient-bearing fit-validation, non-finite output,
physical-support failure, parameter/epoch overrun, random-field drift,
protected-role access, or incomplete cleanup fails closed. A failed role is not
replaced or retried within this package.
