# A8c gate results

Status: `EXECUTED-COMPLETE`
Date: 2026-07-15
Source commit: `046eba3c8d4508c84522c6dbd7cec4d39f094563`
Terminal decision: `STOP-A8-ROUTED-DAILY`

## Prospective and execution boundary

The pre-execution freeze bound 40 specification, implementation, analyzer,
parent-evidence, station, runspec, and contract files before the first A8c
climate output. The frozen campaign then ran 96 processes: six stations, four
burn offsets, two horizons, and candidate plus faithful control. It retained
24 candidate/control station-burn cells.

The first analysis invocation stopped before outcome access and wrote no
result artifact because three parent fallback cells lacked a cached `budget`
object. Amendment 001 reconstructs the same legacy Markov variance identity
from retained parent values. The pre-analysis freeze was rebound before
outcome access; no candidate byte, estimator, threshold, or terminal rule
changed.

## Package-specific evidence gates

| Check | Result | Evidence |
|---|---|---|
| deterministic replay | PASS | All candidate streams reproduced byte-for-byte. |
| nested horizons | PASS | Every 30-year climate row sequence is the exact prefix of its paired 100-year stream. |
| fallback identity | PASS | All `legacy_daily_fallback` climate rows equal their faithful controls. |
| station/profile/provenance identity | PASS | Every route, parameter-set hash, fit ID, model ID, profile, horizon, and burn matches the frozen contract. |
| retained evidence | PASS | The deterministic archive contains all 96 climate/provenance files and validates every member hash. |
| independent replay | PASS | `verify-a8c.py` passed 160 checks and reproduced analysis, decision, and findings byte-for-byte. |
| consolidated review | PASS | `ACCEPT — STOP TERMINAL`; zero open P1 and zero open P2 findings. |

The registered daily targets passed, but the monthly wet-amount, storm
time-to-peak, and exact cross-variable gate groups did not. The frozen terminal
therefore evaluates to `STOP-A8-ROUTED-DAILY`. This is a valid scientific stop,
not an implementation hold.

## Repository gates

| Command | Result | Evidence |
|---|---|---|
| `cargo fmt --check` | PASS | No formatting difference. |
| `cargo clippy --all-targets -- -D warnings` | PASS | All workspace targets completed without warnings. |
| `cargo test` | PASS | The full workspace suite exited zero; faithful golden and routed A8c integration tests passed. |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS | The full workspace suite completed and wrote `target/lcov.info`. |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS | 778 production functions analyzed; none exceeds CRAP 30. |
| `git diff --check` | PASS | No whitespace error. |

The first full repository run detected that the public provenance schema had
not been copied to its runtime mirror and that the quality-report boundary did
not yet accept routed station identity. The mirrors were synchronized, routed
identity was made explicit, and the A8c integration test now round-trips the
generated quality report. The complete gate set above passed after that
correction. It was performed after the climate decision and did not change
generation or campaign evidence.

## Storage and canonical identities

`git check-attr` reports `filter: lfs` for
`a8c-retained-streams-v1.tar.gz`. The archive is 27,481,991 bytes and contains
96 retained files. Canonical SHA-256 identities are:

- pilot contract:
  `7434b499691d472a77579fac896918e61c9b7bd738180d90c4bc498d48a3bfdf`;
- pre-execution freeze:
  `40e48be2f10bf36f1488e664f8b3b4bf9fc44bb1f4627a28b1ca3316c850f74e`;
- pre-analysis freeze:
  `2d1acf61d2be6f023d5e13f06dd6d60cb6df4a709ef753356d0159cfa7d1ec08`;
- execution evidence:
  `2a171c134d00d84c3ef5c481d171e214b1ec444231a61e274ec856fcc95f8e37`;
- analysis:
  `1819a51649eedc89c4584d28b43bd0aec0b81b6f61cfcb29150e46ad88920423`;
- decision:
  `d393b16ea076a6f14d46b57f383ba4ec26014b766661985f9d2922f1fa5bc827`;
- findings:
  `ff4f54cec5a1b7e1c06ffc160ffeb564a2419ac8883c89a50f271af4c9dd28c7`;
- retained archive:
  `ee50d033c6022f9988fc4734cd892d518866dd7df7a35aba24448399ee47edae`;
- retained-stream manifest:
  `2ed40275241748286255d030c6e2facd82a55990af9669fe925e00e8dda86963`.

## Terminal disposition

All implementation, evidence, storage, review, and repository gates pass. The
package is `EXECUTED-COMPLETE` with `STOP-A8-ROUTED-DAILY`. No A8d,
confirmation campaign, retuning, threshold relaxation, WEPP response study,
or production/default promotion is authorized by this result.
