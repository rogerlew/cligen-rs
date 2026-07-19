# A10M5R10 — Parallel Architecture Portfolio

Status: `EXECUTED-HOLD-JOB-LOCAL-CAPACITY`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Compare a prospectively frozen portfolio of stochastic climate architectures
in one parallel campaign. The package optimizes scientific wall time rather
than GPU-minute economy: it evaluates matched P1/P2 capacities and three
registered seeds for every family, retains as many as three eligible Pareto
candidates, and requires at least two retained configurations before declaring
the architecture portfolio ready.

## Scientific basis

A10M5R7 found no single dominant residual mechanism and showed that generated
daily feedback degraded the accepted open-loop model. A10M5R8 showed that a
climate-statistics objective can improve aggregate stochastic behavior while
damaging location and daily proper fit. A10M5R9 then isolated a useful centered
monthly residual mechanism, but its undersized replacement climate-normal
baseline remained weaker than P1. Those results justify comparing several
bounded structures under one objective instead of serially committing to one
architecture at a time.

## Scope

Included:

- exact P1 and P2 matched-seed controls for seeds `147031`, `271828`, and
  `314159`;
- `monthly_residual_adapter`, `annual_monthly_residual_adapter`,
  `hierarchical_joint_factor_adapter`,
  `climate_normal_hierarchical_state_space`, and
  `physics_conditioned_hierarchical_adapter`;
- K1/P1 and K2/P2 capacity envelopes for every family;
- ten independent one-L40 family-capacity roles, with all three seeds executed
  inside each role and all ten roles eligible to run concurrently;
- equal-weight monthly location, monthly interannual dispersion, within-month
  daily dispersion, annual location, annual interannual dispersion, wet
  occurrence/amount, and precipitation-temperature dependence losses;
- exact revision-2 Daymet calendar and missingness preflight, including the
  physics arm's `srad` target mask;
- sixteen-member, all-240 fit-validation final evaluation, deterministic
  eligibility and Pareto retention, evidence collection, accounting, and exact
  cleanup; and
- a target-only solar-radiation head and deterministic latitude/day-of-year
  astronomical envelope in the physics candidate.

Excluded:

- observed precipitation, solar radiation, or other target-day weather as
  model input;
- paired day-to-day target-pattern loss, scheduled sampling, observed or
  generated daily feedback, target lookup, post-generation rescaling, or
  outcome-time hyperparameter changes;
- more families, capacities, seeds, retries, or roles than the frozen matrix;
- development-selection, confirmation metadata, confirmation targets,
  source-sensitivity targets, spatial promotion, production Rust, or a public
  generation profile; and
- multi-rank DDP/NCCL execution. Parallelism is across independent one-GPU
  jobs.

## Authority

The operator's 2026-07-19 dispatch authorizes this portfolio and explicitly
prioritizes wall-clock turnaround over GPU-minute minimization. Scientific and
machine authority are `SPEC-A10-ARCHITECTURE-PORTFOLIO` and
`artifacts/portfolio-contract.json`. `SPEC-A10-CORPUS` revision 2 governs
calendar and target masks. The accepted P1/P2 identities and three seeds come
from A10M5R3R1 and the exact reconstruction record used by A10M5R4R2.

The authority permits one 30-minute one-L40 control-materialization predecessor,
ten 90-minute independent one-L40 family-capacity roles, and one five-minute
exact-node cleanup reserve: 935 GPU-minutes total. Every role is single-attempt.
No scientific retry is authorized.

## Frozen portfolio

K1 uses the accepted P1 control with hidden size 80 and 87,295 parameters;
adapter candidates may contain at most 110,000 total inference parameters.
K2 uses accepted P2 with hidden size 144 and 276,927 parameters; adapter
candidates may contain at most 330,000 total inference parameters. The
climate-normal replacement family must fit the same respective total-capacity
envelopes rather than reuse a frozen neural backbone.

For K1/K2, monthly, annual, and shared-factor dimensions are respectively
`6/3/4` and `12/6/8`, and adapter decoder widths are 32 and 64. The monthly
adapter omits annual and shared-factor state. The annual/monthly adapter uses
separate centered states. The joint-factor adapter uses common low-rank
innovations and a shared decoder for precipitation occurrence, positive amount,
temperature mean, and log diurnal range. The climate-normal family owns an
explicit candidate-fit-only six-regime by twelve-month baseline and trains a
capacity-matched hierarchical state-space model end to end.

The physics candidate has the same hierarchical timing and factor dimensions
as the joint-factor candidate. It adds a deterministic extraterrestrial solar
envelope computed only from latitude and day of year and a stochastic
clearness/radiation head. Shared generated factors represent precipitation,
temperature, and radiation association. Daymet `srad` and precipitation are
targets only: neither observed field, nor any fit-validation target statistic,
is a model input.

## Objective and checkpoint

The seven registered core blocks have equal weight in the family-balanced
climate loss. Daily proper NLL has weight `0.2`, latent stability `0.005`, and
residual size/centering `0.01`; paired daily-pattern loss is exactly zero. The
physics arm additionally assigns weight `0.25` to its registered solar family,
without changing any core block weight.

Training uses eight differentiable stochastic members. Checkpoint and final
evaluation use sixteen hard members and common counter-based random fields
that do not contain the architecture ID. Training runs for at least 24 and at
most 96 epochs with patience 16. Checkpoint selection uses the same
lexicographically first four eligible fit-validation points per regime and
`1e-6` tie tolerance as A10M5R8/R9. The selection scalar is core climate plus
`0.2` daily proper NLL and, for the physics arm only, `0.25` solar-family
score; training-only latent-stability and residual-size/centering terms do not
enter validation selection. Final results cover all 240 eligible
fit-validation points. A checkpoint selected at epoch 96 remains the frozen
result and does not authorize an extension.

## Data calendar and missingness preflight

Before authority creation or resource reservation, the full 1,200-point
candidate-fit and 240-point fit-validation corpus must pass
`daymet_official_365_v1`. For each 1980-01-01 through 2009-12-31 object the
normalized Gregorian axis has 10,958 rows and the source-observed core mask has
10,950 rows. The eight unobserved dates are December 31 in 1980, 1984, 1988,
1992, 1996, 2000, 2004, and 2008; February 29 is observed.

The representative 1980-01-01 through exclusive 1988-01-01 window has 2,922
axis rows and 2,920 observed rows. The preflight must exercise February 29, the
absent leap-year December 31, and both sides of the exclusive window boundary.
Core statistics use
`source_observed && prcp != null && tmax != null && tmin != null`; physics
statistics additionally require `srad != null`. The physics mask is expected
to retain the same 10,950 full-period and 2,920 representative-window rows and
must fail closed if the immutable corpus disagrees. Every eligible year-month
must contain at least 28 masked observations. A complete date axis never
implies complete observations.

## Execution and dispatch

The control-materialization predecessor reconstructs and authenticates the six
accepted P1/P2 seed checkpoints, prepares common training/evaluation random
fields, and publishes immutable control records. Only after that predecessor
passes may the ten family-capacity roles start. Each role runs all three seeds
serially on one typed L40; the ten roles are submitted concurrently as
independent jobs. A CPU aggregation step waits for all terminal roles and
replays the frozen selector. No role may substitute another role's missing
result or use a failed seed's partial output.

Codex executes from `/Users/roger/src/cligen-rs`, starting and pushing on
`main`. Package-private controller state and every remote root must use the
package/run/role identity. Job-local cleanup is mandatory; the single
five-minute reserve is for exact-node, owner-marker-validated cleanup only and
cannot run science.

## Decision

Every candidate-family/capacity configuration is summarized over its three
seeds using metric ratios against the matching P1 or P2 seed control. It is
eligible only if:

- every seed is finite, physically supported, identity-complete, calendar
  clean, role clean, and scored on all 240 fit-validation points;
- median family-balanced climate ratio is at most `1.00`;
- median daily-proper-NLL ratio is at most `1.10`;
- every median core-block ratio is at most `1.10`;
- worst-seed climate, NLL, and individual-block ratios are at most `1.10`,
  `1.15`, and `1.20`, respectively; and
- the median ratio for the mean of monthly and annual interannual-dispersion
  errors is at most `0.90`.

The physics candidate must additionally improve the solar family score by at
least 15% against a candidate-fit regime/month clearness-climatology control,
improve its wet/dry plus precipitation/temperature dependence subscore by at
least 10%, and degrade no solar block by more than 10%.

Eligible configurations enter a Pareto comparison on median matched-control
ratios for overall climate, daily NLL, combined monthly/annual dispersion,
combined monthly/annual location, combined wet/dependence, and within-month
dispersion. A configuration dominates another when it is no worse on every
axis and at least 2% better on one. Differences smaller than 2% are equivalent
for ordering and break by fewer parameters, lower training wall time, then
configuration ID.

At most three nondominated configurations are retained: first the lowest
overall-climate ratio, then the lowest combined-dispersion ratio among the
remainder, then the lowest NLL ratio among the remainder. Fewer than two
retained configurations yields a scientific HOLD; two or three yields
`A10M5R10-PORTFOLIO-READY`. Retention is development-only and does not open a
protected role or promote a production model.

## Gates

- machine contract, exact role matrix, candidate definitions, and decision
  fixtures verify before outcome access;
- full-corpus core and physics calendar/missingness preflight passes before
  authority creation or resource reservation;
- all six controls reconstruct exact accepted identities;
- all and only ten family-capacity roles run once and each publishes all three
  seeds;
- only candidate-fit fits normalizers, climate normals, or model weights;
- fit-validation is gradient-free and all protected roles remain sealed;
- common stochastic fields, ensemble sizes, checkpoint rule, parameter
  ceilings, objective weights, and epoch limits match the contract;
- every completed configuration publishes all-240 metrics, seed summaries,
  parameter count, wall time, learning curve, and physical-support result;
- the deterministic eligibility, Pareto, and retention decision replays from
  the collected rows;
- toolkit accounting totals at most 935 GPU-minutes; collection, job-local
  cleanup, exact durable cleanup, reserve settlement, and close reconcile;
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered unless execution changes production functions
under `crates/`.

## Exit criteria

- `A10M5R10-PORTFOLIO-READY`: two or three eligible nondominated
  configurations are retained;
- `HOLD-A10M5R10-SINGLE-CANDIDATE`: exactly one eligible configuration is
  retained;
- `HOLD-A10M5R10-NO-CANDIDATE`: no configuration is eligible;
- or an exact calendar, identity, role, support, evidence, resource, or cleanup
  hold naming the failed condition.

Every terminal preserves complete comparison evidence. No terminal alone
opens development-selection, confirmation, spatial, production, or public
profile work.

## Artifacts

- `artifacts/portfolio-contract.json` — prospective machine-readable freeze;
- `artifacts/verify_freeze.py` — prospective structure and decision fixtures;
- `artifacts/verify_corpus_calendar.py` — immutable core/physics preflight;
- `artifacts/jobs/` — control, role, aggregation, and dispatch sources;
- `artifacts/portfolio-summary.json` — collected all-configuration metrics;
- `artifacts/portfolio-decision.json` — eligibility, Pareto, and retention;
- `artifacts/execution-disposition.md` — scientific terminal and successor;
- `artifacts/resource-ledger.md` and `toolkit-records.md` — resource/evidence
  closure;
- `artifacts/review.md`, `gate-results.md`, and `verify_result.py` — final
  review and committed verification.

## Execution result

Run `a10m5r10-parallel-architecture-portfolio-r0` closed at
`HOLD-A10M5R10-JOB-LOCAL-CAPACITY`. Control materialization and both physics
roles passed, but the other eight candidate roles failed during environment
bootstrap in two four-job batches. Four concurrent bootstraps exceeded the
shared node-local temporary-storage capacity before the science entrypoint
could publish candidate evidence. The selector was therefore not run, and no
architecture conclusion is drawn from this incomplete matrix.

The toolkit settled 103 charged GPU-minutes, collected sanitized evidence,
verified every supervised job-local target absent, removed the exact durable
remote root, released the unused cleanup reserve, and closed the authority.
Corrective A10M5R10R1 reruns the unchanged full portfolio with two live jobs,
one authenticated bootstrap at a time, and verified wheel/cache deletion
before science.
