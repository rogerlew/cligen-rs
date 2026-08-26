# Test results

Status: terminal gates passed for `EXECUTED-HOLD-REPAIR-INELIGIBLE`.

## Prospective and amendment gates

- Bundled Python 3.12.13 / NumPy 2.3.5 evaluator tests: 20/20 passed.
- Inherited A12 evaluator tests: 16/16 passed.
- Strict manifest validation: passed; digest
  `04ef9509e421fd3de962c39dbca675349e216a1df300e6e04932d48c4717cca1`.
- `git diff --check`: passed.
- Independent prospective and amendment reviews: GO, no unresolved P0/P1.

The first-source attempt `b34e94104208df868bd602dea21f1b9723850362`
failed safely before terminal publication on an inherited selector-component
tolerance. Its exact build receipt is preserved. The authenticated diagnostic
found maximum distance drift `6.679101716144942e-13 km`, no pool/rank/score/
winner mismatches, and four production repair failures.

## Realized execution and replay

- Exact amended source: `866d0401ab757708d80a58ad9dda5683f6e000bc`.
- Calendar preflight: 240 fit-validation sites, 10,958 axis rows, 10,950
  observed rows, eight exact masked leap-year December 31 dates; passed.
- Feasibility: exactly 2,400 cells; 2,362 ordinarily localizable; every site
  has 3--10 eligible donors; passed census completeness.
- Frozen repair gate: 11 policy-site failures across four sites; formal
  `HOLD-REPAIR-INELIGIBLE` emitted with quality scoring false.
- First/replay calendar preflight SHA-256:
  `e7a042c7e5aed05b15a17a431bc19e7e117cc5f31bae7f56a2cbb16f49b10a36`.
- First/replay feasibility file SHA-256:
  `9523b1a27d09affd755fde1c701ae6b26f7d31be883e054c78b99aee5a84d508`.
- Quality evidence, quality decision, and success execution receipt: correctly
  absent.
- Confirmation target access: false.

## Terminal repository gates

- `cargo fmt --check`: passed.
- `cargo clippy --all-targets -- -D warnings`: passed.
- `cargo test`: passed (all ordinary tests; evidence-gated ignored tests remain
  explicitly ignored by their existing contracts).
- Production-function coverage/CRAP gate: not triggered; no production
  functions changed.
