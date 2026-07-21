# A10M5R14R2R2 — Two-L40 Two-Wave Portfolio

Status: `EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`
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

## Run r0 operational hold

Run `r0` completed control job `1017887` in 1,303 seconds with exit zero,
all gates true, cleanup true, and 22 charged GPU-minutes. Portfolio admission
then failed before submission because `sinfo --Node` returned the same node row
once per partition. The availability facts themselves passed: four-L40
inventory, one active GPU, and at least two idle GPUs. Fresh run `r1`
deduplicates identical `sinfo` rows before enforcing exact-node identity;
conflicting rows still fail closed. No r0 portfolio admission or reservation
was retained.

## Run r1 operational failure

Run `r1` completed control job `1017918` in 1,300 seconds with all gates
true. Its fresh portfolio admission passed the composed checker and the
two-idle-L40 occupancy gate, and job `1018091` received exactly two L40s.
The launcher saw allocation tokens `0,1` and two devices named `NVIDIA L40`,
but failed before starting any candidate because the scheduling transform
changed the token-count assertion to two while leaving the unique-token
assertion at four. The failed portfolio charged three GPU-minutes; the complete
run charged 25. Collection and remote cleanup succeeded, and replay was
inapplicable because no candidate evidence existed.

Fresh run `r2` changes that single assertion to two, strengthens the focused
test against recurrence, and changes only operational run identities. Frozen
science remains unchanged.

## Run r2 operational failure

Run `r2` completed control job `1018164` in 1,244 seconds with every gate true.
After several correct occupancy holds, its fresh portfolio admission passed and
job `1018406` received exactly two L40s. The corrected launcher authenticated
the two devices and launched both wave-0 children in isolated processes. Both
then failed during import before training because the R14R2 `continuous_core`
export loop copied the public name `inherited` into its own globals, overwriting
the wrapper's module binding before the loop reached
`smooth_climatology_basis`. Wave 1 remained unopened. The run charged 24
GPU-minutes, collected the partial evidence, and cleaned the remote root.
Replay was inapplicable because no training record existed.

Fresh run `r3` makes the wrapper module and accounting bindings private before
exporting the byte-identical R14 public surface. It changes no candidate,
objective, temporal metric, calendar, seed, training, or selector behavior.

## Run r3 disposition

Run `r3` completed control job `1018626` in 1,246 seconds (21 GPU-minutes)
and two-L40 portfolio job `1018733` in 12,243 seconds (409 GPU-minutes). All
control and portfolio operational gates passed; the portfolio receipt is
`16b8ce4c062f33e066d43efdbbdcb029604d1c7f7839e628564d29171897ff8c`.
Collection promoted 241,684,480 authenticated bytes, then cleanup verified
both the remote root and job-local state absent.

The inherited replay asset was an operationally rebound artifact with no
published source path and retained two-L40 assumptions in its evidence and
non-gating annual-diagnostic checks. `artifacts/recover_r3_replay.py`
authenticated the exact deterministic rebind from published R14R2R1 source,
made the two-device token/device checks explicit, and recorded all six
non-gating annual pairwise probabilities rather than unpacking two candidates.
It did not alter collected evidence, candidate decisions, objectives, or
selection gates. Two independent passes were byte-identical and both returned
`HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`; the replay record is
`f4e404326e81fcbf6670552d221da10eca4605ce296a3898cdc08573d83c289a` and
the recovery attestation is
`07e00f5eb40fba65452fb760caf962d600fe17c9288fa3c8fb9ea4955427fb20`.

No candidate is selectable under the frozen temporal protocol. This is a
scientific HOLD, not an operational failure: the completed four-candidate
portfolio and its evidence remain the basis for the next architecture
decision, while confirmation and solar roles remain sealed.
