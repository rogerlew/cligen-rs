# A10M5R3R1 terminal

Disposition: `A10M5R3R1-CAPACITY-PAIR-READY`

## Evidence admissibility

- Parent A10M5R3 remains `HOLD-A10-RESOURCE-BOUND`: 29 settled jobs exceeded
  its 18-job maximum, despite only 188 rounded GPU-minutes of 545.
- The accepted `r4` lineage independently contains exactly 18 registered
  attempt-zero receipts at source `47963a9`; all passed.
- The failed r2/r3 receipts are disjoint and supplied no row to family,
  capacity, or pair selection.
- All 239 raw files match `RAW_COLLECTED` byte counts and SHA-256 identities.
- Projection v3 with `<REMOTE_RUN_ROOT>` produced 239 forbidden-value-clean
  public files and per-file raw-parent receipts. The parent
  `SANITIZATION_FAILED` is preserved, not relabeled.
- All 18 job-local roots were authenticated absent. The exact owner marker and
  plan hash authorized committed `clean.sh`; both it and an independent probe
  returned `REMOTE_ABSENT`. No recovery job ran.

## Accepted scientific handoff

- family: `lognormal_wet_v2`;
- knee P1: L80/W160/D2, 87,295 parameters, three-seed mean NLL 2.663283,
  population SD 0.003118;
- neighbor P2: L144/W288/D2, 276,927 parameters, mean NLL 2.574190,
  population SD 0.014351; and
- retained runtime ranges: P1 4.209--4.376x, P2 6.088--6.347x.

The pair is input to A10M5R4 only. Realized monthly/interannual skill, spatial
generalization, final architecture, confirmation, and promotion remain open.

## Toolkit remedy

Planning and amendment now validate typed projection tokens using the same
grammar collection enforces. `[REMOTE_RUN_ROOT]` fails before staging;
`<REMOTE_RUN_ROOT>` is the typed replacement form. Canonical guidance also
records nested-parent creation, canonical Python ordering, and authority
continuation via `derive-run`.
