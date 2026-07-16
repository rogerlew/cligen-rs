# A9c3 gate results

Status: `PASS` with registered scientific terminal
`HOLD-A9C3-NO-SELECTABLE-CANDIDATE`

Date: 2026-07-15
Source commit: `a0e24f0866f4536c168bfd809cb957d91e6d8bf3`

## Canonical execution

- `python3 -m research.a9c3.experiment calibrate`
  - PASS — 14 family/horizon thresholds and 2,000 grouped bootstrap
    replicates; no candidate input; 136/97 development events.
- `python3 -m research.a9c3.experiment fit`
  - eight detail and compact fit records were written before inherited
    research-helper closeout defects stopped aggregation.
- `python3 -m research.a9c3.experiment fit-closeout`
  - PASS — exact immutable fit hashes verified; 8 fresh fits; 4 renewal and 2
    latent fit-valid; structural and uncertainty-adjusted monthly summaries
    pass. The bounded correction is recorded in
    `pre-score-fit-closeout-correction.md`.
- `python3 -m research.a9c3.experiment evaluate`
  - PASS as an execution; six configurations entered the short screen, zero
    entered full development, zero entered Pareto replay, and the registered
    terminal is `HOLD-A9C3-NO-SELECTABLE-CANDIDATE`.
  - The outcome-time 30-year/100-year engineering-horizon deviation and its
    unchanged-terminal proof are recorded in
    `post-outcome-methods-deviation.md`.

Resource gates pass: calibration used 333.8118255827576 seconds and
241,156,096 maximum RSS bytes; fit/structural used 302.9169177059084 seconds
and 173,162,496 bytes; evaluation used 1,894.7092706672847 seconds and
2,154,168,320 bytes. Campaign wall time is 2,531.4380139559507 seconds against
the 259,200-second limit. Every failed-limit list is empty.

## Package and report verification

- `PYTHONDONTWRITEBYTECODE=1 python3 docs/work-packages/20260715-a9c3-two-site-grouped-observed-comparison/artifacts/verify-a9c3.py`
  - PASS — 2-site grouped calibration; 8 fresh fits; 6 short-screen
    configurations with 31-objective coverage; confirmation target series
    untouched.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/a9c3/tests -v`
  - PASS — 6 tests.
- `python3 docs/reports/verify-report.py --internal-review docs/reports/a9c3-two-site-grouped-observed-comparison-report.manifest.json`
  - PASS at each internal-review hash.
- `python3 docs/reports/verify-report.py docs/reports/a9c3-two-site-grouped-observed-comparison-report.manifest.json`
  - PASS — accepted report, evidence, hypotheses, study facts, references, and
    three accepted review lenses agree.
- `python3 docs/reports/verify-report.py --self-test`
  - PASS.
- Consolidated internal review
  - ACCEPT — zero open P1/P2 findings.

## Repository gates

- `cargo fmt --check`
  - PASS.
- `cargo clippy --all-targets -- -D warnings`
  - PASS.
- `cargo test`
  - PASS.
- `git diff --check`
  - PASS.
- authored-text trailing-whitespace scan
  - PASS.
- public-artifact absolute-path, local-file-link, private-key marker, and
  copyrighted-reading-copy-path scan
  - PASS.
- `git lfs fsck`
  - PASS. A9c normalized observed objects remain LFS-managed; A9c3 fit-detail
    JSON is covered by a package-specific LFS rule.

Coverage and CRAP gates were not triggered because A9c3 changes no production
function under `crates/`.

## Closure

No candidate freeze exists. A9d, A9e, production runtime work, openWEPP, and
WEPPcloud integration remain unauthorized. The recommended unscaffolded
follow-up is A9c4: decompose mandatory evidence unavailability, confirm or
prospectively amend completeness, then correct candidate context support
structurally without realized-output clipping.
