# Dispatch receipt

- Operator instruction: `Scaffold and execute the A10M2 completion package`.
- Date: 2026-07-17 PDT.
- Repository: `cligen-rs`.
- Starting branch/commit: clean `main` at `c5dadd0`.
- Push target: `main`.
- Authorized remote scope: one package-owned Lemhi run directory, verified
  offline assets, and the frozen C1--C3b matrix.
- Resource ceiling: 35 base requested GPU-minutes; at most one exact
  infrastructure retry while cumulative requested use remains no more than
  60 GPU-minutes.
- Authentication boundary: use only existing MFA-bootstrapped SSH masters in
  `BatchMode=yes`; never solicit, receive, or retain credentials.
