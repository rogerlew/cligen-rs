# Predecessor verification

Date: 2026-07-16 PDT
Host: `rmm` (Apple M1, macOS, 16 GB memory)
Source: `f831d54c2f5c37eb69b27acaa99a3a228a32f7c7`

## Authority and status checks

`sha256sum -c artifacts/predecessor-manifest.sha256` passed for all 20 frozen
authorities when evaluated from the repository root.

The accepted status chain was checked directly:

- A7a, A7b, A8a, A8b, A8c, A8c1, A9a, and A9b are complete.
- A9c retains its gate-calibration hold.
- A9c2 retains its hot-arid-roster hold.
- A9c3 retains its no-selectable-candidate hold.
- A9c4 retains its completeness-surface hold.
- A9d retains `HOLD-A9D-NO-SELECTABLE-CANDIDATE`.

No hold was treated as a pass or rewritten.

## LFS hydration and replay

The initial checkout contained Git LFS pointers for the 18 A9d detail fits.
Their OIDs agreed with the fit manifest. The operator directed a full pull;
Git LFS 3.7.1 was installed on `rmm`, initialized for the repository, and
`git lfs pull` completed successfully.

The native command then ran against hydrated bodies:

```text
/tmp/cligen-a10m0-venv/bin/python -m research.a9d.campaign verify-development
PASS: 18 fits; 24 staged evaluations; 92 retained/19 report-only cells per horizon; terminal=HOLD-A9D-NO-SELECTABLE-CANDIDATE
```

The verifier environment used Python 3.12.13, NumPy 1.26.4, SciPy 1.13.1,
jsonschema 4.23.0, and scikit-learn 1.5.2. `research/a9c3` imports
scikit-learn but its requirements omit a pin; this is inherited packaging debt
and does not change the verified evidence identity or terminal.

## Confirmation firewall

The development result reports `candidate_freeze_count=0` and
`confirmation_series_accessed=false`. This package read no confirmation target
series, selected no candidate, and authorized no confirmation execution.
