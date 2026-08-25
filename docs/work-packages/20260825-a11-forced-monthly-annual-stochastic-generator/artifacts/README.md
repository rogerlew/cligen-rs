# A11 artifact inventory

This directory began as a scaffold. Unless a file is explicitly present and labeled
`Ran`, its name below remains a conditional or absent artifact, not execution evidence.
Large or restricted inputs, generated streams, WEPP outputs, and confirmation
targets remain outside Git and are represented by immutable manifests.

## Prospective freezes

- `design-freeze-v1.json` — science contract, one candidate identity, numeric
  choices, RNG domains, rosters, horizons, seeds, thresholds, and terminals.
- `predecessor-manifest-v1.json` — exact ADR/spec/package/source authorities.
- `forcing-source-manifest-v1.json` — source, period, role, units, cell, and
  content identities for every forced or fitted quantity.
- `resource-freeze-v1.json` — aggregate CPU, wall-clock, storage, acquisition,
  and operational-attempt ceilings.
- `confirmation-firewall-v1.json` — locked roles, metadata-only surface,
  candidate seal prerequisites, and atomic consume rule.

## Preflight and implementation evidence

- `calendar-preflight-v1.json` — axis, observed/masked counts, leap and window
  fixtures, required masks, eligibility, and verifier receipt.
- `forcing-reconciliation-fixtures-v1.json` — covariance and annual-moment
  feasible/infeasible cases with exact solver receipts.
- `forcing-bundle-examples-v1.json` — canonical positive and fail-closed
  examples once the schema is ratified.
- `texture-fit-manifest-v1.json` — candidate-fit-only pooled regional fit
  identities and diagnostics.
- `oracle-fixtures-v1.json` — occurrence bridge, amount, temperature, storm,
  context, replay, and support fixtures.
- `attempt-ledger-v1.jsonl` — append-only operational attempts with separate
  execution and science status.

## Development and conditional confirmation

- `development-evidence-v1.json` — complete four-arm nested 30/100 climate
  evaluation.
- `wepp-response-evidence-v1.json` — complete pinned WEPP response matrix.
- `development-decision-v1.json` — integrated pass/fail and confirmation-access
  decision.
- `candidate-freeze-v1.json` — candidate bytes and rules; present only after a
  development pass.
- `confirmation-seal-v1.json`, `confirmation-consume-v1.json`, and
  `confirmation-evidence-v1.json` — present only if the firewall opens in that
  order.
- `terminal-v1.json` — the single final scientific disposition.

## Closeout

- `scaffold-gates.md` — repository checks run for the documentation scaffold.
- `review.md` — independent review and finding dispositions (present for the
  scaffold review; update or supersede at terminal review).
- `gate-results.md` — exact commands, versions, and Ran/Static results.
- `resource-ledger.md` — aggregate use, releases, and cleanup.

## Ratified implementation files

- `design-freeze-v1.json` and `design-freeze-v1.md` — revision-1 machine and
  human authorities.
- `a11-evidence-v1.schema.json` — strict compact evidence envelope.
- `a11.py` — package-local preflight, fit, generator, conditional oracle, and
  climate evaluator.
- `calendar-preflight-v1.json`, `development-evidence-v1.json`, and
  `fit-summary-v1.json` — generated only by the registered commands and labeled
  `Ran` in the terminal record.
- `evidence-audit-v1.json` — terminal authority invalidating the attempted
  development evidence for scientific use.
- `development-decision-v1.json` and `terminal-v1.json` — closeout at contract
  nonconformance with science not evaluated.
- `gate-results.md` and `resource-ledger.md` — terminal validation and resource
  reconciliation.
