# ADR-0006: Expand the A10 Warm-Generation Runtime Failure Boundary to 30×

Status: Accepted
Date: 2026-07-21
Deciders: Roger Lew (operator)
Evidence:
`docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/`,
`docs/work-packages/20260718-a10m5r3r1-evidence-reconciliation/`, and the
temporal-gate record through
`docs/work-packages/20260720-a10m5r14r2r2-two-l40-two-wave-portfolio/`

## Context

The A10 study plan froze a warm-generation runtime rule relative to
`faithful_5_32_3` on the normative single-core CPU benchmark: `PASS` below
5×, `WARN` at 5× to below 10×, and hard `FAIL` at 10× or greater. That rule
was set when the study still assumed a production-adjacent deployment
posture for the first candidate generation.

Two evidence lines have since changed the trade:

1. The accepted A10M5R3/R3R1 capacity ladder showed validation quality
   still improving monotonically at the top of the ladder while the 10×
   boundary excluded it: P1 (87,295 params, 4.210× worst ratio, NLL
   2.6666), P2 (276,927, 6.280×, 2.5870, `WARN`), P3 (975,679, 12.415×,
   2.4999, excluded), P4 (3,019,695, 27.562×, 2.2037, excluded). The
   quality/capacity curve was not exhausted at the boundary; capacity was
   removed as an experimental lever by an operational rule, not by
   scientific evidence.
2. Every family evaluated under the frozen temporal selector — the P1/P2
   state-space, the retained residual adapters, the continuous
   medium/slow hierarchies, and the R14 distribution-head factorial —
   failed the temporal gates by a wide margin
   (`HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`, best bootstrap
   median regime ratio 2.162 against the 1.25 gate). The binding
   uncertainty is scientific feasibility, not deployment cost.

A10 is a research-only feasibility study; no production profile ships from
it. Holding candidates to a near-deployment runtime envelope while the
scientific question is unresolved inverts the study's priorities.

## Decision

1. The warm-generation hard-failure boundary moves from 10× to 30× of the
   faithful median, prospectively. The amended classification is:
   `PASS` below 5.0×; `WARN` at 5.0× to below 30.0×; `FAIL` at 30.0× or
   greater. Exactly 5× remains a warning; exactly 30× is a failure.
   Ratios remain computed from unrounded times under the frozen
   Section 4.5 benchmark procedure, which is otherwise unchanged.
2. The `WARN` consequence is unchanged and now spans the wider band: a
   warning survives selection, sealing, and the final terminal, and
   runtime optimization remains required before any consumer
   integration. A `WARN` candidate cannot be represented as
   deployment-feasible.
3. Cold-start, memory, export-size, and model-size safeguards are not
   rescaled by this decision. The faithful-relative ratio rule still
   applies only to warm stochastic generation.
4. The amendment is prospective. Closed terminals are not rewritten;
   A10M5R3's exclusion of P3/P4 under the 10× rule remains the accepted
   record of that package. P3 (12.415×) and P4 (27.562×) become
   re-admissible capacities for prospectively identified successor
   packages. P4 sits within measurement dispersion of the new boundary;
   any P4 candidacy must show its frozen dispersion-rule upper bound
   below 30× to be eligible.
5. Re-admitting capacity is authorization to propose, not to train. Each
   successor package still freezes its own capacity roster and resource
   bound before output.

## Consequences

- The research envelope now tolerates roughly an order of magnitude more
  CPU generation cost than a faithful run. This is an explicit research
  posture; any promotion path must either optimize back inside the
  original envelope or carry a prominent standing warning.
- The capacity axis re-opens above P2. The knee arithmetic of
  SPEC-A10-NEURAL-CANDIDATE-V2 is unchanged, but a successor capacity
  screen may extend the frontier to P3/P4 under the amended gate.
- Successor specs cite this ADR for the runtime rule rather than
  restating the superseded 10× boundary. The study plan's Section 4.5
  values are superseded by amendment, not edited in place.
- The 800 L40 GPU-hour study ceiling and per-package job accounting are
  unaffected.
