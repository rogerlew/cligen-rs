# A10 Structural Architecture Identification

Status: research-only

Revision: 1 (A10M5R7, 2026-07-18)

## Surface and authority

This specification defines a development-only inference-mode diagnostic and a
conditional generated-feedback candidate after the accepted P1/P2 temporal
terminal. It introduces no public generation profile, does not change faithful
CLIGEN, and does not reopen the prior retained set.

Producers are the A10M5R7 Lemhi probe and local evaluator. Consumers are its
deterministic architecture decision and conditional temporal scorer. Every
record fails closed on unknown modes, metrics, sites, seeds, identities,
non-finite values, support failure, or protected-role access.

## Inference modes

`accepted_open_loop` uses the accepted P1 implementation: seven normalized
weather inputs are zero during free generation, while calendar and transferable
site descriptors drive the recurrent state.

`observation_conditioned` is diagnostic-only. For each eligible observation
date it uses the preceding available observed daily weather vector, transformed
through candidate-fit-only normalization, to produce a sampled one-step output.
It cannot be selected as a generator.

`generated_feedback` is a new research candidate identity. It starts from the
accepted zero normalized weather state, samples the declared hurdle-lognormal
and continuous heads, transforms the seven sampled weather values through the
same candidate-fit-only normalizers, and supplies them as the next day's
endogenous inputs. Calendar and site descriptors remain exogenous. No clipping,
repair, monthly rescaling, target lookup, or horizon-dependent parameter is
allowed.

All modes use the same weights, counter-based member field, physical support,
calendar, and site surface. Their difference is transition closure only.

## Attribution and decision

Every common temporal metric publishes the observation, generated value,
signed scaled residual, absolute scaled error, site, regime, mode, and group.
The five groups are fixed in the package contract. Group errors are arithmetic
means of their registered components; the family-balanced diagnostic is the
mean of the five group errors.

Generated feedback may advance only under the exact improvement,
nondegradation, completeness, and support rules in the package contract. If it
does not advance, the registered ordered decision tree identifies at most one
next architecture hypothesis. This attribution never changes the accepted
temporal score or creates favorable missing values.

## Conditional full temporal surface

Only an advancing generated-feedback probe may reconstruct the other two P1
seeds and generate the full matrix. The full decision retains the exact prior
sites, observations, faithful and stochastic-PRISM arms, members, horizon,
component scales, bootstrap, and noninferiority limits. It receives a fresh
candidate identity and cannot edit P1/P2 history.

## Provenance and firewall

Records bind package/source commit, accepted checkpoint payload identities,
corpus and normalization identities, mode/candidate identity, site, member,
seed, and stream hash. Only candidate-fit affects weights or normalization.
Development-selection and confirmation paths are prohibited and recorded as
an empty opened-role list.
