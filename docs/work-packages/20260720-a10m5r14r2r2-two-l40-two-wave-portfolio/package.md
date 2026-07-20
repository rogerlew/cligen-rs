# A10M5R14R2R2 — Two-L40 Two-Wave Portfolio

Status: `SCAFFOLDED-AUTHORIZED`
Date: 2026-07-20
Evidence mode: Development architecture comparison; unchanged R14 science
Starting branch and push target: current `main`, push `main`

## Objective

Execute the four frozen R14 continuous-distribution-head candidates without
waiting for all four L40s on `node03` to become idle. Retain one independent
single-GPU process per candidate, but schedule two deterministic waves of two
concurrent processes inside one two-L40 allocation.

## Frozen science

Candidate definitions, K2 capacity, seeds, corpus, calendar contract,
monthly and annual objective terms, selectors, training budget, parameter
accounting, and final selection rules are byte-identical to R14R2R1. Month and
year remain aggregation/error domains, never recurrent reset boundaries. Solar
radiation remains sealed for the later procedural-envelope stage.

Wave 0 contains the two location-only candidates. Wave 1 contains the two
location-and-scale candidates. Wave membership is an operational scheduling
fact only and may not enter model inputs, losses, metrics, or selection.

## Resource contract

- control: one L40, 30 minutes;
- portfolio: two L40s, 240 minutes, one allocation;
- within the portfolio: exactly two waves, exactly two concurrent children per
  wave, and no overlap between waves;
- recovery contingency: one L40, five minutes;
- ceiling: 515 GPU-minute-equivalents;
- exactly one shared environment and one shared extracted corpus;
- four disjoint candidate output roots and four disjoint transient cache roots.

Admission requires the exact composed checker chain and a fresh `node03`
snapshot proving the four-L40 inventory and at least two idle L40s. It does not
require the whole node to be idle. The receipt remains valid for at most 60
seconds and submission follows immediately.

## Inheritance and disposition

R14R2R1 source commit `6463ab2bebcf016c371afc56e31ffc7156a2fb95`
proved the composed-checker remedy and completed its control successfully. Its
portfolio was never submitted because the four-idle-L40 gate held. This package
uses fresh source, authority, budget, run, plan, manifest, admission, occupancy,
job, replay, and disposition identities. It does not reuse the R14R2R1 control
as successor evidence because that record is bound to the predecessor run and
source identity.

## Terminal rule

The package may select a candidate only if control, both waves, all four child
records, collection, cleanup, and two independent replay passes authenticate
and agree. Otherwise it closes with an honest HOLD or FAIL disposition while
preserving all retained evidence.
