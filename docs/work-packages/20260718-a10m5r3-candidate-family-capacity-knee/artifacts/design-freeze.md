# A10M5R3 trajectory freeze

ADR-0005 and SPEC-A10-REFINEMENT-TRAJECTORY freeze the scientific order and
scope of this package before execution:

- use only the accepted A10M1 corpus;
- compare lognormal, gamma, and a proper body-plus-GPD-excess candidate at one
  fixed N0 architecture before changing capacity;
- retire the prior whole-wet-day GPD identity;
- measure a five-point geometric parameter ladder with clean-process CPU/RSS
  evidence;
- retain the Pareto knee and its immediately larger passing neighbor;
- defer realized temporal adjudication to A10M5R4;
- defer N3/elevation acquisition to A10M5R5;
- carry both capacities through A10M5R6 spatial validation before final
  architecture freeze; and
- keep development-selection and confirmation roles sealed.

The prospective execution boundary is now complete. Revision 2 is registered
by `SPEC-A10-NEURAL-CANDIDATE-V2`, `a10-model-v2.schema.json`, and
`a10-capacity-screen-v2.schema.json`. `artifacts/matrix.json` freezes all 18
primary rows, the physical 20 mm splice threshold, three seeds, the five
capacity architectures, and the 545 GPU-minute total ceiling. The executable
`research/a10/m5r3_contract.py` freezes selection and pair-stability arithmetic.

The fixed family architecture is N0 L64/W128/D2. Its exact parameter counts
are 56,527 for lognormal and gamma and 56,722 for the splice. The capacity
ladder has the following exact counts, with the splice count in parentheses:
P0 34,351 (34,450), P1 87,295 (87,538), P2 276,927 (277,362), P3 975,679
(976,498), and P4 3,019,695 (3,021,138). Every row remains below 50 million.

The nine family jobs are fixed identities. The five capacity jobs and four
frontier jobs are generic but not adaptive in authority: committed `resolve.py`
consumes all and only the preceding frozen row receipts and applies the
committed selector. It emits content-reconstructable family and capacity
selection receipts before downstream fitting. No agent-authored code or
threshold can change after results become visible.

All jobs are sequential, one L40, one attempt, 30 minutes. One exact-node
five-minute recovery allocation is reserved. The success path stages explicit
`invoked=false` recovery evidence. Raw durable paths are projected through an
exact typed replacement before collection. Family rows run calibration and
stream gates; capacity and frontier rows additionally run the full clean-
process 12-cell CPU benchmark. Every trainer exits before the CPU worker is
launched under `/usr/bin/time -v`.

This committed boundary authorizes allocation. Any family, architecture,
seed, selector, threshold, role, time, retry, or evidence-surface change now
requires a new prospective package; an amendment may correct only operational
projection fields before the matrix settles.

The accepted R2 handoff supplies four operational anchors: L64 lognormal
depth-2 and depth-3 for N0 and N1. All twelve R2 rows passed exact predecessor
identity, clean-process RSS, and runtime gates. R3 may use the four anchors for
lineage and ladder placement, but its prospectively frozen family screen and
Pareto selector remain responsible for the successor scientific decision.
