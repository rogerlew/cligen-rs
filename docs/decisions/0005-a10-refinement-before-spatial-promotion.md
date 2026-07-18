# ADR-0005: Refine A10 Before Spatial Expansion and Promotion

Status: Accepted
Date: 2026-07-18
Deciders: Roger Lew (operator)
Evidence:
`docs/work-packages/20260717-a10m5-bounded-gpu-screen/` and
`docs/work-packages/20260717-a10m5r1-cpu-export-memory-remedy/`

## Context

A10M5 proved that the neural training, checkpoint, deterministic generation,
CPU export, and Lemhi execution framework can complete the frozen twelve-row
screen. A10M5R1 then showed that the apparent 3.09--3.13 GiB export RSS was an
inherited high-water-mark artifact: clean workers used 521--525 MB steady RSS
and 628--635 MB external maximum. The engineering framework is therefore not
the limiting uncertainty, and the 50-million-parameter ceiling leaves room to
measure a materially wider capacity range.

The scientific screen exposed three boundaries that must be addressed before
promotion:

1. the evaluated GPD head modeled every wet-day amount with an unshifted GPD;
   it was not a threshold-excess tail splice, and its training auxiliaries used
   a lognormal expected-amount formula;
2. the terms named `monthly_expected_precipitation` and
   `annual_aggregate_dispersion` were expectation regularizers over training
   windows, not realized calendar-month or interannual ensemble diagnostics;
3. the frozen 34,351--226,767-parameter grid was too narrow to locate a useful
   architecture/runtime knee.

The operator also established a longer scientific objective: after temporal
quality is demonstrated, expand the station surface using North American Level
III ecoregions and elevation, test mountain lapse-rate and microclimate
behavior, and eventually pursue a cleanroom, ClimateNA-like terrain
spatializer as a separate post-A10 layer.

## Decision

1. A10M5R2 remains an immutable corrected-memory replay of the frozen A10M5
   grid. If it passes, its promotions are operational/scientific anchors; they
   do not by themselves authorize final A10 selection or sealing.
2. A10M6 is deferred behind a prospective refinement sequence:
   A10M5R3 candidate-family and capacity-knee work on the accepted A10M1
   corpus; A10M5R4 realized temporal-dispersion adjudication on that corpus;
   A10M5R5 N3/elevation corpus expansion and role freeze; and A10M5R6 spatially
   blocked generalization of the retained capacity pair.
3. The current whole-wet-day GPD implementation is retired from successor
   candidacy. The first successor family screen compares hurdle lognormal,
   hurdle gamma, and a proper body-plus-threshold-GPD-excess formulation. A
   GPD may return only under a new identity with a candidate-fit-only frozen
   threshold, family-correct expectation, sampling, support, and calibration
   tests.
4. Distribution selection and the broad architecture/runtime knee use only
   the accepted A10M1 corpus. The family screen holds architecture fixed and
   complete-pooled; the capacity screen then uses a geometric parameter ladder
   broad enough to expose fixed framework cost and nonlinear CPU cost.
5. The capacity screen retains two neighboring passing Pareto capacities: the
   observed knee and the immediately larger frontier point. It does not freeze
   the final architecture.
6. A10M5R4 must compare realized generated calendar-month and annual
   distributions with observations, faithful CLIGEN, and an independently
   versioned revised stochastic baseline. A head expectation or training
   regularizer cannot substitute for generated ensemble evidence.
7. N3/elevation acquisition occurs only after the capacity pair is known.
   A10M5R5 stratifies by Level III ecoregion and within-ecoregion elevation,
   freezes geographic roles before target access, and explicitly samples
   high-relief, valley/ridge, windward/leeward, and coastal/interior contrasts.
8. A10M5R6 carries both retained capacities into spatially blocked evaluation.
   N3 is first an acquisition/evaluation stratum, not automatically a
   categorical model feature. Learned station identity is diagnostic and
   cannot establish scale-free unseen-site behavior.
9. A10M6 promotion requires temporal adjudication, spatial generalization, the
   final clean-process CPU benchmark, and a deterministic capacity decision.
   Confirmation roles remain sealed throughout A10M5R2--R6.
10. A cleanroom ClimateNA-like daily terrain spatializer remains post-A10. It
    will consume a shared coarse daily stochastic state, preserve watershed
    event coherence, and remain distinct from later subdaily storm/intensity
    disaggregation.

## Consequences

- Expanded N3/elevation data are not a prerequisite for locating the broad
  architecture/runtime knee, avoiding a full capacity matrix on the larger
  corpus.
- The wider corpus may still favor the larger retained capacity; final
  architecture freeze therefore occurs only after spatial validation.
- A10M5R2 evidence remains historically comparable and is not rewritten to
  answer the new scientific question.
- The new family, capacity, temporal, corpus, and spatial records receive new
  prospective identities. Earlier A10M3/A10M5 scores cannot be relabeled as
  confirmation evidence.
- Arbitrary coordinate or raster output is not itself evidence of improved
  spatial resolution. Improvement must be demonstrated at geographically held
  observations against the revised stochastic-plus-PRISM baseline.
