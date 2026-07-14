# A5d0 Successor Feasibility and Calibration Gate Results

Status: `PASSED-FOR-HOLD-CLOSURE`
Date: 2026-07-14 (America/Los_Angeles)
Evidence source commit: `8d00f8c2108910f257b29c02341c0e1fca9e4dd9`
Terminal package status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`

Passing these gates accepts the accuracy and completeness of the recorded
hold. It does not accept an A5d candidate or authorize confirmation output.

## Package-specific evidence gates

| Command or check | Result |
|---|---|
| `python3 artifacts/verify-a5d0-package.py` | PASS after closure-manifest creation; 19 input locks and 15 closure artifacts verified, zero public-surface changes, zero confirmation stations, zero candidate/target exposures, and 7/7 fail-closed mutation checks rejected |
| `python3 artifacts/run-feasibility-fixtures.py --self-test` | PASS; deterministic variance, kernel, null-calibration, bootstrap-availability, and sign-design arithmetic |
| Stored fixture reproduction | PASS; script output equals `feasibility-fixtures-v1.json` |
| Strict JSON parsing | PASS; all four pre-closure machine artifacts parse, while the verifier rejects duplicate keys and nonfinite constants |
| Accepted public-surface lock | PASS; all ten A5c-protected hashes match, the profile enum/default is unchanged, no A5d identifier leaked, and no held-package normative evaluation specification exists |
| Development/confirmation inventory | PASS; the repository contains the 17 exposed Daymet and eight exposed GHCN stations recorded in the inventory and no asserted untouched confirmation object |
| Confirmation exposure | PASS; no A5d candidate climate, WEPP output, or target value was accessed or generated |
| Local Markdown links | PASS; every local link in the package resolves |

## Scientific and review gates

| Gate | Result |
|---|---|
| Accuracy lens | ACCEPT; all numeric identities, 19 hashes, and 25 exposed-station identities independently reproduced |
| Scientific-validity lens | ACCEPT after bounded recheck of four dispositions |
| Consistency/public-safety lens | ACCEPT after bounded recheck of three dispositions |
| Open review findings | PASS; P1 = 0, P2 = 0, P3 = 0 |
| Feasibility claim boundary | PASS; the synthetic construction is not represented as an actual-library solution or confirmation evidence |
| Evaluation claim boundary | PASS; revision 4 remains a non-normative plan and is explicitly uncalibrated |
| Decision rule | PASS; the primary contract hold and secondary evaluation/corpus holds follow the preregistered fail-closed exit criteria |

The general report-manifest verifier is not applicable because this package
does not create or revise a registered artifact under `docs/reports/`. The
package nevertheless used the authoring protocol's three independent review
lenses and consolidated disposition gate.

## Repository and hygiene gates

| Command or check | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS, including faithful byte-parity; evidence tests requiring local uncommitted capture corpora remained ignored as declared by the existing suite |
| `git diff --check` | PASS |
| `git lfs fsck` | PASS |
| New package files requiring LFS | None; all are small Markdown, JSON, or Python text artifacts |

Coverage and CRAP gates do not apply because execution added or changed no
production function under `crates/`.
