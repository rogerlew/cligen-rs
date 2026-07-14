# Interannual Candidate Experiment 001 Report Gate Results

Status: passed
Date: 2026-07-14 (America/Los_Angeles)
Evidence source commit: `7273829517121011edd8bb815ff72fefd3742bcb`

## Report contract gates

| Command or check | Result |
|---|---|
| `python3 docs/reports/verify-report.py --internal-review docs/reports/interannual-candidate-exp-001-report.manifest.json` | PASS on corrected pre-acceptance snapshot |
| `python3 docs/reports/verify-report.py --self-test` | PASS; rejects duplicate keys, nonfinite JSON, contradictory study facts, invalid evidence mode, a second H1, a missing body citation, hypothesis-outcome conflict, report-revision conflict, contradictory review counts, and missing sections |
| `python3 docs/reports/verify-report.py docs/reports/interannual-candidate-exp-001-report.manifest.json` | PASS on accepted snapshot |
| Required metadata and ten ordered H2 sections | PASS |
| Study-identity rows and matrix arithmetic | PASS; 14 candidate/horizon rows, 1,904 climates, 2,176 WEPP response/execution records |
| Evidence/reference/hypothesis registries and body citations | PASS |
| Local report links and report catalog status | PASS |
| Hash-bound review terminal block | PASS; three accepted lenses, zero open P1/P2 |

Accepted revision-1 report SHA-256:
`8f6b4b18e8e1761ab3a5ae9651f201060fc0c9ebebe801e98c4ed9909f7f83e4`.
Accepted revision-2 report SHA-256:
`b1b7f0af0a1f8980183b5e4fa00222c5ae1ccfd29c4bd2b7f43c916652789f5b`.
Accepted revision-2 consolidated-review SHA-256:
`9b4f9e55daff8f05f098d633a47ecfbb2c2d314eab23fa76ac56dbc0f10ba7a7`.
The revision-2 identities are bound by the strict report manifest.

## Scientific and consistency gates

| Gate | Result |
|---|---|
| Accuracy lens | ACCEPT after bounded recheck; 14 gate, 14 detailed climate, and 14 WEPP rows independently reproduced |
| Scientific-validity lens | ACCEPT after all six findings were dispositioned and rechecked |
| Consistency/public-safety lens | ACCEPT after all six findings were dispositioned and the hardened verifier was attacked |
| Open review findings | PASS; P1 = 0, P2 = 0, P3 = 0 |
| Exploratory/prospective language | PASS across abstract, methods, limitations, conclusions, manifest, ledger, and review |
| Exact-version/no-promotion boundary | PASS; no candidate family or public profile is generalized or promoted |
| Daymet/GHCN, storm, winter, and WEPP construct boundaries | PASS |
| Evidence identities | PASS; all 13 evidence and three governance hashes match |

## Revision 2 advisory incorporation gates

| Gate | Result |
|---|---|
| Advisory identity | PASS; SHA-256 `b85c5cb775b4356c587399a182c900ee49a477e8c6abb5e5e0aee6b3a4e689af` |
| ADV-001 through ADV-005 disposition | PASS; all five appear in the report, claim ledger, and consolidated review |
| Frozen experiment results | PASS; no quantitative table, gate outcome, hypothesis outcome, or promotion decision changed |
| Station-day derivation | PASS; `(10,957 + 36,524) × 7 × 17 × 8 = 45,201,912` rows and `15,565,742 / 45,201,912 = 34.436%` dewpoint caps |
| Advisory inference boundaries | PASS; variance identity is idealized, and unverified Gate 5 probability/spectral explanations are not report findings |
| Prospective-only recommendations | PASS; no revision-3 gate is rescored or relaxed |
| Revision identity | PASS; report and manifest both declare revision 2, and self-test rejects mismatch |

## Repository and public-safety gates

| Command or check | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS; faithful byte-parity test included |
| `git diff --check` | PASS |
| `git lfs fsck` | PASS |
| `git ls-files references/copyrighted \| wc -l` | PASS; 0 tracked files |
| New package/report files above 1 MiB | PASS; none, so no new LFS object is appropriate |

Coverage and CRAP gates do not apply: the package changes no production
function under `crates/`.
