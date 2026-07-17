# Dispatch

- Operator dispatch: `Execute A10M2D1`, 2026-07-16.
- Source: clean published `main` at
  `3bc543f2404bc6a2d6ab81931f6eb7e9eb033029`.
- Authority: diagnostic comparison only, at most 10 requested GPU-minutes.
- SSH: existing `login-ui` and `lemhi` control masters both reported running;
  every automated connection used `BatchMode=yes`.
- Pre-submit state: no user job was present; `gpu-icrews` was up and `node03`
  was idle with four L40s advertised.
- Remote identity: unique relative run name `a10m2d1-3bc543f`.
- Base submission: D1 job `1013558`, exactly as frozen, with no amendment or
  retry.

Local and staged hashes matched `logs/source-manifest.sha256` before login
prestaging or Slurm submission. No credential or MFA material entered the
payload or retained evidence.
